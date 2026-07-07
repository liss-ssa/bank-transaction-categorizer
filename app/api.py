from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.categorization.pipeline import categorize_file
from app.config import settings
from app.data.generate_synthetic import save_synthetic
from app.evaluation.metrics import evaluate

DATASET_PATH = Path("data/synthetic/transactions.csv")
PREDICTIONS_PATH = Path("data/processed/predictions.csv")
REPORT_DIR = Path("reports")
METRICS_PATH = REPORT_DIR / "metrics.json"

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class Job(BaseModel):
    id: str
    kind: str
    status: JobStatus = "queued"
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


class GenerateRequest(BaseModel):
    rows: int = Field(default=1000, ge=1, le=100_000)
    seed: int = Field(default=42, ge=0)
    output_path: str = str(DATASET_PATH)


class CategorizeRequest(BaseModel):
    input_path: str = str(DATASET_PATH)
    output_path: str = str(PREDICTIONS_PATH)
    use_llm: bool = False


class EvaluateRequest(BaseModel):
    input_path: str = str(PREDICTIONS_PATH)
    report_dir: str = str(REPORT_DIR)


class AllRequest(BaseModel):
    rows: int = Field(default=1000, ge=1, le=100_000)
    seed: int = Field(default=42, ge=0)
    use_llm: bool = False


jobs: dict[str, Job] = {}
job_lock = asyncio.Lock()
app = FastAPI(title="Bank Transaction Categorizer", version="0.2.0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_relative_path(path: str, allowed_roots: tuple[str, ...] = ("data", "reports")) -> str:
    """Keep API file operations inside mounted project folders."""
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HTTPException(status_code=400, detail="Only relative paths inside data/ or reports/ are allowed")
    if not candidate.parts or candidate.parts[0] not in allowed_roots:
        raise HTTPException(status_code=400, detail="Path must be inside data/ or reports/")
    return str(candidate)


async def create_job(kind: str, fn, *args, **kwargs) -> Job:
    job = Job(id=str(uuid.uuid4()), kind=kind, created_at=utc_now())
    async with job_lock:
        jobs[job.id] = job

    async def runner() -> None:
        async with job_lock:
            jobs[job.id].status = "running"
            jobs[job.id].started_at = utc_now()
        try:
            result = await asyncio.to_thread(fn, *args, **kwargs)
            async with job_lock:
                jobs[job.id].status = "succeeded"
                jobs[job.id].finished_at = utc_now()
                jobs[job.id].result = result if isinstance(result, dict) else {"message": str(result)}
        except Exception as exc:  # noqa: BLE001 - API must capture job failures
            async with job_lock:
                jobs[job.id].status = "failed"
                jobs[job.id].finished_at = utc_now()
                jobs[job.id].error = str(exc)

    asyncio.create_task(runner())
    return job


def generate_task(req: GenerateRequest) -> dict[str, Any]:
    output = safe_relative_path(req.output_path, ("data",))
    save_synthetic(req.rows, output, req.seed)
    return {"rows": req.rows, "output_path": output}


def categorize_task(req: CategorizeRequest) -> dict[str, Any]:
    input_path = safe_relative_path(req.input_path, ("data",))
    output_path = safe_relative_path(req.output_path, ("data",))
    previous_llm_enabled = settings.llm_enabled
    settings.llm_enabled = req.use_llm
    try:
        df = categorize_file(input_path, output_path)
    finally:
        settings.llm_enabled = previous_llm_enabled
    return {
        "rows": int(len(df)),
        "input_path": input_path,
        "output_path": output_path,
        "use_llm": req.use_llm,
    }


def evaluate_task(req: EvaluateRequest) -> dict[str, Any]:
    input_path = safe_relative_path(req.input_path, ("data",))
    report_dir = safe_relative_path(req.report_dir, ("reports",))
    return evaluate(input_path, report_dir)


def all_task(req: AllRequest) -> dict[str, Any]:
    generate_task(GenerateRequest(rows=req.rows, seed=req.seed))
    categorize_result = categorize_task(CategorizeRequest(use_llm=req.use_llm))
    metrics = evaluate_task(EvaluateRequest())
    return {"categorize": categorize_result, "metrics": metrics}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "llm_enabled_by_default": settings.llm_enabled, "model": settings.openrouter_model}


@app.post("/generate", response_model=Job)
async def generate(req: GenerateRequest) -> Job:
    return await create_job("generate", generate_task, req)


@app.post("/categorize", response_model=Job)
async def categorize(req: CategorizeRequest) -> Job:
    return await create_job("categorize", categorize_task, req)


@app.post("/evaluate", response_model=Job)
async def evaluate_endpoint(req: EvaluateRequest) -> Job:
    return await create_job("evaluate", evaluate_task, req)


@app.post("/pipeline/all", response_model=Job)
async def all_endpoint(req: AllRequest) -> Job:
    return await create_job("all", all_task, req)


@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str) -> Job:
    async with job_lock:
        job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/metrics")
def get_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found. Run /evaluate or /pipeline/all first.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/reports/{filename}")
def get_report(filename: str) -> FileResponse:
    allowed = {"metrics.json", "classification_report.txt", "confusion_matrix.png"}
    if filename not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported report file")
    path = REPORT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(path)
