"""Compares live client traffic (logs/client_requests.jsonl) against the
training baseline (data/processed/trips_clean.csv) and produces a tabular
data-drift + proxy concept-drift report.
"""
import csv, json, statistics
from collections import Counter

from .features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from .generate_data import ROOT
from .monitor import psi

CLIENT_LOG = ROOT / "logs/client_requests.jsonl"
BASELINE_PATH = ROOT / "data/processed/trips_clean.csv"
PSI_THRESHOLD = .2
Z_THRESHOLD = 2.0
TVD_THRESHOLD = .15


def load_baseline():
    with BASELINE_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_live_requests():
    if not CLIENT_LOG.exists():
        return []
    entries = [json.loads(line) for line in CLIENT_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [e for e in entries if e.get("outcome") == "ok"]


def numeric_drift_row(feature, baseline_vals, live_vals):
    b_mean, b_std = statistics.mean(baseline_vals), (statistics.pstdev(baseline_vals) or 1e-9)
    l_mean, l_std = statistics.mean(live_vals), (statistics.pstdev(live_vals) or 1e-9)
    score = psi(baseline_vals, live_vals)
    z = abs(l_mean - b_mean) / b_std
    return {"feature": feature, "baseline_mean": round(b_mean, 4), "live_mean": round(l_mean, 4),
            "baseline_std": round(b_std, 4), "live_std": round(l_std, 4), "psi": round(score, 4),
            "mean_shift_z": round(z, 4), "drift": bool(score >= PSI_THRESHOLD or z >= Z_THRESHOLD)}


def categorical_drift_row(feature, baseline_vals, live_vals):
    bc, lc = Counter(baseline_vals), Counter(live_vals)
    bt, lt = sum(bc.values()) or 1, sum(lc.values()) or 1
    categories = set(bc) | set(lc)
    tvd = sum(abs(bc.get(c, 0) / bt - lc.get(c, 0) / lt) for c in categories) / 2
    return {"feature": feature, "baseline_dist": {c: round(bc.get(c, 0) / bt, 3) for c in categories},
            "live_dist": {c: round(lc.get(c, 0) / lt, 3) for c in categories},
            "total_variation_distance": round(tvd, 4), "drift": bool(tvd >= TVD_THRESHOLD)}


def concept_drift_row(baseline_rows, live_entries):
    baseline_targets = [float(r["trip_duration_minutes"]) for r in baseline_rows]
    predicted = [float(e["response"]["predicted_eta_minutes"]) for e in live_entries if e.get("response")]
    if not predicted:
        return {"note": "no successful live predictions to compare"}
    score = psi(baseline_targets, predicted)
    return {"metric": "PSI(train target vs live predicted eta) - proxy for concept drift; "
                       "true concept drift needs labelled live outcomes (logs/feedback.jsonl)",
            "baseline_target_mean": round(statistics.mean(baseline_targets), 4),
            "live_predicted_mean": round(statistics.mean(predicted), 4),
            "psi": round(score, 4), "drift": bool(score >= PSI_THRESHOLD), "ground_truth_available": False}


def main():
    baseline_rows = load_baseline()
    live_entries = load_live_requests()
    if not live_entries:
        report = {"error": "no successful client requests logged yet; run python -m client.live_client first"}
        (ROOT / "reports").mkdir(exist_ok=True)
        (ROOT / "reports/drift_table.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    live_features = [e["request"] for e in live_entries]
    numeric_rows = [numeric_drift_row(f, [float(r[f]) for r in baseline_rows], [float(r[f]) for r in live_features]) for f in NUMERIC_FEATURES]
    categorical_rows = [categorical_drift_row(f, [r[f] for r in baseline_rows], [r[f] for r in live_features]) for f in CATEGORICAL_FEATURES]
    concept = concept_drift_row(baseline_rows, live_entries)

    report = {"baseline_size": len(baseline_rows), "live_size": len(live_entries),
              "numeric_drift": numeric_rows, "categorical_drift": categorical_rows, "concept_drift": concept}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/drift_table.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = ["# Client traffic drift report", "",
             f"Baseline rows: {len(baseline_rows)}  |  Live requests analysed: {len(live_entries)}", "",
             "## Numeric feature drift (covariate/data drift)", "",
             "| Feature | Baseline Mean | Live Mean | Baseline Std | Live Std | PSI | Mean shift (z) | Drift? |",
             "|---|---:|---:|---:|---:|---:|---:|:---:|"]
    for r in numeric_rows:
        lines.append(f"| {r['feature']} | {r['baseline_mean']} | {r['live_mean']} | {r['baseline_std']} | "
                      f"{r['live_std']} | {r['psi']} | {r['mean_shift_z']} | {'YES' if r['drift'] else 'no'} |")
    lines += ["", "## Categorical feature drift", "", "| Feature | Total Variation Distance | Drift? |", "|---|---:|:---:|"]
    for r in categorical_rows:
        lines.append(f"| {r['feature']} | {r['total_variation_distance']} | {'YES' if r['drift'] else 'no'} |")
    lines += ["", "## Concept drift (proxy, no ground truth yet)", "", "```json", json.dumps(concept, indent=2), "```", "",
              f"Thresholds: PSI >= {PSI_THRESHOLD} | mean-shift z >= {Z_THRESHOLD} | TVD >= {TVD_THRESHOLD}"]
    (ROOT / "reports/drift_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
