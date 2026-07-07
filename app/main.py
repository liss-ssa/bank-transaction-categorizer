from __future__ import annotations

import argparse
from pathlib import Path

from app.categorization.pipeline import categorize_file
from app.data.generate_synthetic import save_synthetic
from app.evaluation.metrics import evaluate
from app.config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bank transaction categorizer MVP")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate synthetic transactions")
    gen.add_argument("--n", "--rows", dest="n", type=int, default=1000)
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--output", default="data/synthetic/transactions.csv")

    run = sub.add_parser("run", help="Categorize transactions")
    run.add_argument("--input", default="data/synthetic/transactions.csv")
    run.add_argument("--output", default="data/processed/predictions.csv")
    run.add_argument("--use-llm", choices=["true", "false"], default=None)

    ev = sub.add_parser("evaluate", help="Evaluate predictions")
    ev.add_argument("--input", default="data/processed/predictions.csv")
    ev.add_argument("--report-dir", default="reports")

    all_cmd = sub.add_parser("all", help="Generate, categorize and evaluate")
    all_cmd.add_argument("--n", "--rows", dest="n", type=int, default=1000)
    all_cmd.add_argument("--seed", type=int, default=42)
    all_cmd.add_argument("--use-llm", choices=["true", "false"], default=None)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "generate":
        save_synthetic(args.n, args.output, args.seed)
        print(f"Saved synthetic data to {args.output}")
    elif args.cmd == "run":
        if args.use_llm is not None:
            settings.llm_enabled = args.use_llm == "true"
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        df = categorize_file(args.input, args.output)
        print(f"Saved predictions to {args.output}; rows={len(df)}")
    elif args.cmd == "evaluate":
        metrics = evaluate(args.input, args.report_dir)
        print(metrics)
    elif args.cmd == "all":
        if args.use_llm is not None:
            settings.llm_enabled = args.use_llm == "true"
        src = "data/synthetic/transactions.csv"
        out = "data/processed/predictions.csv"
        save_synthetic(args.n, src, args.seed)
        categorize_file(src, out)
        print(evaluate(out, "reports"))


if __name__ == "__main__":
    main()
