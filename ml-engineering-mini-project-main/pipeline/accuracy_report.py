"""Joins logs/predictions.jsonl with logs/feedback.jsonl (by request_id) to
measure real-world predicted-vs-actual accuracy drift, as opposed to the
input-feature PSI drift computed by pipeline/drift_report.py.
"""
import json, statistics

from .generate_data import ROOT

PREDICTIONS_PATH = ROOT / "logs/predictions.jsonl"
FEEDBACK_PATH = ROOT / "logs/feedback.jsonl"
RMSE_DRIFT_THRESHOLD = 8.0


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def window_stats(rows):
    if not rows:
        return {"n": 0, "mae": None, "rmse": None}
    errors = [r["abs_error"] for r in rows]
    signed = [r["error"] for r in rows]
    return {"n": len(rows), "mae": round(statistics.mean(errors), 4), "rmse": round((sum(e * e for e in signed) / len(signed)) ** .5, 4)}


def main():
    predictions = {p["request_id"]: p for p in load_jsonl(PREDICTIONS_PATH)}
    feedback = load_jsonl(FEEDBACK_PATH)

    joined = []
    for fb in feedback:
        pred = predictions.get(fb["request_id"])
        if not pred:
            continue
        error = fb["actual_eta_minutes"] - pred["predicted_eta_minutes"]
        joined.append({"request_id": fb["request_id"], "timestamp_utc": pred["timestamp_utc"],
                        "model_version": pred["model_version"], "predicted_eta_minutes": pred["predicted_eta_minutes"],
                        "actual_eta_minutes": fb["actual_eta_minutes"], "error": round(error, 4), "abs_error": round(abs(error), 4)})
    joined.sort(key=lambda r: r["timestamp_utc"])

    (ROOT / "reports").mkdir(exist_ok=True)
    if not joined:
        report = {"error": "no matched predictions+feedback yet; run `python -m client.feedback_client` first"}
        (ROOT / "reports/accuracy_drift.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    overall = window_stats(joined)
    half = max(1, len(joined) // 2)
    first_stats, second_stats = window_stats(joined[:half]), window_stats(joined[half:])
    rmse_delta = (second_stats["rmse"] - first_stats["rmse"]) if first_stats["rmse"] is not None and second_stats["rmse"] is not None else None
    accuracy_drift = bool(second_stats["rmse"] is not None and second_stats["rmse"] >= RMSE_DRIFT_THRESHOLD)

    report = {"matched_pairs": len(joined), "overall": overall, "first_half_older": first_stats, "second_half_newer": second_stats,
              "rmse_delta_first_vs_second": round(rmse_delta, 4) if rmse_delta is not None else None,
              "rmse_threshold": RMSE_DRIFT_THRESHOLD, "accuracy_drift_triggered": accuracy_drift,
              "action": "queue retraining with latest labelled trips" if accuracy_drift else "continue monitoring", "rows": joined}
    (ROOT / "reports/accuracy_drift.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = ["# Prediction vs. actual accuracy drift report", "",
              f"Matched prediction/feedback pairs: {len(joined)}",
              f"Overall MAE: {overall['mae']} | Overall RMSE: {overall['rmse']} | RMSE drift threshold: {RMSE_DRIFT_THRESHOLD}", "",
              "| Window | n | MAE | RMSE |", "|---|---:|---:|---:|",
              f"| First half (older) | {first_stats['n']} | {first_stats['mae']} | {first_stats['rmse']} |",
              f"| Second half (newer) | {second_stats['n']} | {second_stats['mae']} | {second_stats['rmse']} |", "",
              f"**Accuracy drift triggered: {'YES' if accuracy_drift else 'no'}** (newer-window RMSE vs. threshold {RMSE_DRIFT_THRESHOLD})", "",
              "## Per-request detail", "", "| request_id | timestamp | predicted | actual | error | abs_error |", "|---|---|---:|---:|---:|---:|"]
    for r in joined:
        lines.append(f"| {r['request_id'][:8]}... | {r['timestamp_utc']} | {r['predicted_eta_minutes']} | {r['actual_eta_minutes']} | {r['error']} | {r['abs_error']} |")
    (ROOT / "reports/accuracy_drift.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:15]))
    print(f"... {len(joined)} rows total, full detail in reports/accuracy_drift.md")


if __name__ == "__main__":
    main()
