from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


def evaluate(predictions_csv: str, report_dir: str = "reports") -> dict:
    df = pd.read_csv(predictions_csv)
    if "true_category" not in df.columns:
        raise ValueError("true_category column is required for evaluation")
    y_true = df["true_category"].astype(str)
    y_pred = df["predicted_category"].astype(str)
    labels = sorted(set(y_true) | set(y_pred))
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    metrics = {
        "rows": int(len(df)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "unknown_rate": float((y_pred == "unknown").mean()),
        "other_rate": float((y_pred == "other").mean()),
        "bank_misc_rows": int((df.get("bank_category", "") == "Прочее").sum()) if "bank_category" in df else 0,
        "total_prompt_tokens": int(df.get("prompt_tokens", pd.Series([0])).sum()),
        "total_completion_tokens": int(df.get("completion_tokens", pd.Series([0])).sum()),
        "total_tokens": int(df.get("total_tokens", pd.Series([0])).sum()),
    }
    if "bank_category" in df:
        misc = df[df["bank_category"] == "Прочее"]
        if len(misc):
            metrics["accuracy_on_bank_misc"] = float(
                accuracy_score(misc["true_category"].astype(str), misc["predicted_category"].astype(str))
            )
            metrics["predicted_other_on_bank_misc_rate"] = float((misc["predicted_category"] == "other").mean())

    (report_path / "classification_report.txt").write_text(
        classification_report(y_true, y_pred, labels=labels, zero_division=0), encoding="utf-8"
    )
    pd.Series(metrics).to_json(report_path / "metrics.json", force_ascii=False, indent=2)

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(cm)
    ax.set_xticks(range(len(labels)), labels=labels, rotation=90)
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix")
    fig.tight_layout()
    fig.savefig(report_path / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    return metrics
