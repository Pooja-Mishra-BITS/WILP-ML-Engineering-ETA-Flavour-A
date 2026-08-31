"""Builds a self-contained HTML observability dashboard (Chart.js via CDN)
focused on per-feature PSI/drift from reports/drift_table.json (produced by
`python -m pipeline.drift_report`) plus real predicted-vs-actual accuracy
drift from reports/accuracy_drift.json (produced by `python -m
pipeline.accuracy_report`).
"""
import json

from .generate_data import ROOT

DRIFT_JSON = ROOT / "reports/drift_table.json"
ACCURACY_JSON = ROOT / "reports/accuracy_drift.json"
OUT_HTML = ROOT / "reports/observability_dashboard.html"
PSI_THRESHOLD = .2
TVD_THRESHOLD = .15
RMSE_THRESHOLD = 8.0


def load_accuracy():
    if not ACCURACY_JSON.exists():
        return None
    report = json.loads(ACCURACY_JSON.read_text(encoding="utf-8"))
    return None if "error" in report else report


def main():
    if not DRIFT_JSON.exists():
        raise SystemExit("reports/drift_table.json not found - run `python -m pipeline.drift_report` first")
    report = json.loads(DRIFT_JSON.read_text(encoding="utf-8"))
    if "error" in report:
        raise SystemExit(report["error"])

    numeric = report["numeric_drift"]
    categorical = report["categorical_drift"]
    concept = report["concept_drift"]
    accuracy = load_accuracy()

    numeric_labels = [r["feature"] for r in numeric]
    numeric_psi = [r["psi"] for r in numeric]
    numeric_colors = ["#e74c3c" if r["drift"] else "#2ecc71" for r in numeric]

    cat_labels = [r["feature"] for r in categorical]
    cat_tvd = [r["total_variation_distance"] for r in categorical]
    cat_colors = ["#e74c3c" if r["drift"] else "#2ecc71" for r in categorical]

    numeric_rows_html = "".join(
        f"<tr><td>{r['feature']}</td><td>{r['baseline_mean']}</td><td>{r['live_mean']}</td>"
        f"<td>{r['baseline_std']}</td><td>{r['live_std']}</td><td>{r['psi']}</td>"
        f"<td>{r['mean_shift_z']}</td><td class=\"{'bad' if r['drift'] else 'good'}\">{'DRIFT' if r['drift'] else 'ok'}</td></tr>"
        for r in numeric
    )
    cat_rows_html = "".join(
        f"<tr><td>{r['feature']}</td><td>{r['total_variation_distance']}</td>"
        f"<td class=\"{'bad' if r['drift'] else 'good'}\">{'DRIFT' if r['drift'] else 'ok'}</td></tr>"
        for r in categorical
    )
    concept_psi = concept.get("psi", "n/a")
    concept_drift = concept.get("drift", False)

    if accuracy:
        acc_rows = accuracy["rows"][-100:]
        acc_labels = [r["timestamp_utc"] for r in acc_rows]
        acc_predicted = [r["predicted_eta_minutes"] for r in acc_rows]
        acc_actual = [r["actual_eta_minutes"] for r in acc_rows]
        acc_abs_error = [r["abs_error"] for r in acc_rows]
        acc_rows_html = "".join(
            f"<tr><td>{r['request_id'][:8]}...</td><td>{r['timestamp_utc']}</td><td>{r['predicted_eta_minutes']}</td>"
            f"<td>{r['actual_eta_minutes']}</td><td>{r['error']}</td><td>{r['abs_error']}</td></tr>"
            for r in acc_rows
        )
        accuracy_section = f"""
<h2>Predicted vs. actual accuracy drift (feedback loop)</h2>
<div class="cards">
<div class="card"><b>Matched pairs</b><div style="font-size:1.6rem">{accuracy['matched_pairs']}</div></div>
<div class="card"><b>Overall MAE</b><div style="font-size:1.6rem">{accuracy['overall']['mae']}</div></div>
<div class="card"><b>Overall RMSE</b><div style="font-size:1.6rem">{accuracy['overall']['rmse']}</div></div>
<div class="card"><b>Newer-window RMSE</b><div style="font-size:1.6rem">{accuracy['second_half_newer']['rmse']}</div></div>
<div class="card"><b>Accuracy drift triggered</b><div style="font-size:1.6rem" class="{'bad' if accuracy['accuracy_drift_triggered'] else 'good'}">{'YES' if accuracy['accuracy_drift_triggered'] else 'no'}</div></div>
</div>
<canvas id="accuracyChart" height="90"></canvas>
<br><br>
<canvas id="errorChart" height="90"></canvas>
<h3>Recent predicted vs. actual (last {len(acc_rows)} of {accuracy['matched_pairs']})</h3>
<table>
<tr><th>Request</th><th>Timestamp</th><th>Predicted</th><th>Actual</th><th>Error</th><th>Abs Error</th></tr>
{acc_rows_html}
</table>
<script>
const rmseThreshold = {RMSE_THRESHOLD};
new Chart(document.getElementById('accuracyChart'), {{
  data: {{
    labels: {json.dumps(acc_labels)},
    datasets: [
      {{ type: 'line', label: 'Predicted ETA', data: {json.dumps(acc_predicted)}, borderColor: '#3498db', pointRadius: 2, tension: .2 }},
      {{ type: 'line', label: 'Actual ETA', data: {json.dumps(acc_actual)}, borderColor: '#2ecc71', pointRadius: 2, tension: .2 }}
    ]
  }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Predicted vs. actual ETA over time' }} }}, scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }} }} }}
}});
new Chart(document.getElementById('errorChart'), {{
  data: {{
    labels: {json.dumps(acc_labels)},
    datasets: [
      {{ type: 'bar', label: 'Absolute error (minutes)', data: {json.dumps(acc_abs_error)}, backgroundColor: '#9b59b6' }},
      {{ type: 'line', label: 'RMSE drift threshold', data: {json.dumps(acc_labels)}.map(() => rmseThreshold), borderColor: '#7f8c8d', borderDash: [6,4], pointRadius: 0 }}
    ]
  }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Absolute prediction error over time' }} }}, scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }} }} }}
}});
</script>
"""
    else:
        accuracy_section = """
<h2>Predicted vs. actual accuracy drift (feedback loop)</h2>
<p><i>No matched predictions/feedback yet. Run <code>python -m client.feedback_client</code> then
<code>python -m pipeline.accuracy_report</code> to populate this section.</i></p>
"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ETA Model Observability Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{font-family:Arial,sans-serif;margin:2rem;background:#f7f7f9}}
.cards{{display:flex;gap:1rem;margin-bottom:2rem;flex-wrap:wrap}}
.card{{background:#fff;border-radius:8px;padding:1rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.15);min-width:160px}}
h1{{margin-bottom:.2rem}}
h2{{margin-top:2.5rem}}
canvas{{background:#fff;border-radius:8px;padding:1rem;box-shadow:0 1px 3px rgba(0,0,0,.15)}}
table{{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.15)}}
th,td{{padding:.5rem .8rem;text-align:right;border-bottom:1px solid #eee}}
th:first-child,td:first-child{{text-align:left}}
.good{{color:#2ecc71;font-weight:bold}}
.bad{{color:#e74c3c;font-weight:bold}}
</style></head><body>
<h1>ETA Prediction Model - Observability Dashboard</h1>
<p>Baseline (training) rows: {report['baseline_size']} | Live client requests analysed: {report['live_size']} | Source: reports/drift_table.json</p>
<div class="cards">
<div class="card"><b>Concept drift PSI (proxy)</b><div style="font-size:1.6rem" class="{'bad' if concept_drift else 'good'}">{concept_psi}</div></div>
<div class="card"><b>PSI threshold</b><div style="font-size:1.6rem">{PSI_THRESHOLD}</div></div>
<div class="card"><b>TVD threshold</b><div style="font-size:1.6rem">{TVD_THRESHOLD}</div></div>
<div class="card"><b>Numeric features drifting</b><div style="font-size:1.6rem">{sum(1 for r in numeric if r['drift'])}/{len(numeric)}</div></div>
<div class="card"><b>Categorical features drifting</b><div style="font-size:1.6rem">{sum(1 for r in categorical if r['drift'])}/{len(categorical)}</div></div>
</div>

<h2>PSI per numeric feature</h2>
<canvas id="psiChart" height="90"></canvas>

<h2>Total variation distance per categorical feature</h2>
<canvas id="tvdChart" height="90"></canvas>

<h2>Numeric feature drift detail</h2>
<table>
<tr><th>Feature</th><th>Baseline Mean</th><th>Live Mean</th><th>Baseline Std</th><th>Live Std</th><th>PSI</th><th>Mean shift (z)</th><th>Status</th></tr>
{numeric_rows_html}
</table>

<h2>Categorical feature drift detail</h2>
<table>
<tr><th>Feature</th><th>Total Variation Distance</th><th>Status</th></tr>
{cat_rows_html}
</table>
{accuracy_section}
<script>
const psiThreshold = {PSI_THRESHOLD};
const tvdThreshold = {TVD_THRESHOLD};
new Chart(document.getElementById('psiChart'), {{
  data: {{
    labels: {json.dumps(numeric_labels)},
    datasets: [
      {{ type: 'bar', label: 'PSI', data: {json.dumps(numeric_psi)}, backgroundColor: {json.dumps(numeric_colors)} }},
      {{ type: 'line', label: 'Drift threshold', data: {json.dumps(numeric_labels)}.map(() => psiThreshold), borderColor: '#7f8c8d', borderDash: [6,4], pointRadius: 0 }}
    ]
  }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'PSI by feature (red = above threshold)' }} }} }}
}});
new Chart(document.getElementById('tvdChart'), {{
  data: {{
    labels: {json.dumps(cat_labels)},
    datasets: [
      {{ type: 'bar', label: 'Total Variation Distance', data: {json.dumps(cat_tvd)}, backgroundColor: {json.dumps(cat_colors)} }},
      {{ type: 'line', label: 'Drift threshold', data: {json.dumps(cat_labels)}.map(() => tvdThreshold), borderColor: '#7f8c8d', borderDash: [6,4], pointRadius: 0 }}
    ]
  }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'TVD by feature (red = above threshold)' }} }} }}
}});
</script>
</body></html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Observability dashboard written to {OUT_HTML}")


if __name__ == "__main__":
    main()
