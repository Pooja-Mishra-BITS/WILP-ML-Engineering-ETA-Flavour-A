"""Builds a self-contained HTML monitoring dashboard (Chart.js via CDN) from
logs/client_requests.jsonl: request latency over time and status/crash
timeline, plus an uptime summary.
"""
import json

from .generate_data import ROOT

CLIENT_LOG = ROOT / "logs/client_requests.jsonl"
OUT_HTML = ROOT / "reports/dashboard.html"
OUT_SUMMARY = ROOT / "reports/dashboard_summary.json"


def load_entries():
    if not CLIENT_LOG.exists():
        return []
    return [json.loads(line) for line in CLIENT_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    entries = load_entries()
    total = len(entries)
    ok = sum(1 for e in entries if e.get("outcome") == "ok")
    http_error = sum(1 for e in entries if e.get("outcome") == "http_error")
    crash = sum(1 for e in entries if e.get("outcome") == "crash")
    uptime = round(100 * ok / total, 2) if total else 0.0

    labels = [e["timestamp_utc"] for e in entries]
    latencies = [e.get("latency_ms") for e in entries]
    status_values = [e.get("status_code") or 0 for e in entries]
    status_labels = [str(e.get("status_code") or "CRASH") for e in entries]
    colors = ["#2ecc71" if e.get("outcome") == "ok" else ("#e67e22" if e.get("outcome") == "http_error" else "#e74c3c") for e in entries]
    summary = {"total": total, "ok": ok, "http_error": http_error, "crash": crash, "uptime_pct": uptime}

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>ETA API Monitoring Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{font-family:Arial,sans-serif;margin:2rem;background:#f7f7f9}}
.cards{{display:flex;gap:1rem;margin-bottom:2rem;flex-wrap:wrap}}
.card{{background:#fff;border-radius:8px;padding:1rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,.15);min-width:140px}}
h1{{margin-bottom:.2rem}}
canvas{{background:#fff;border-radius:8px;padding:1rem;box-shadow:0 1px 3px rgba(0,0,0,.15)}}
</style></head><body>
<h1>ETA Prediction API - Monitoring Dashboard</h1>
<p>Generated from logs/client_requests.jsonl</p>
<div class="cards">
<div class="card"><b>Total requests</b><div style="font-size:1.6rem">{total}</div></div>
<div class="card"><b>Uptime</b><div style="font-size:1.6rem;color:{'#2ecc71' if uptime >= 99 else '#e67e22'}">{uptime}%</div></div>
<div class="card"><b>200 OK</b><div style="font-size:1.6rem;color:#2ecc71">{ok}</div></div>
<div class="card"><b>HTTP errors</b><div style="font-size:1.6rem;color:#e67e22">{http_error}</div></div>
<div class="card"><b>Crashes</b><div style="font-size:1.6rem;color:#e74c3c">{crash}</div></div>
</div>
<canvas id="latencyChart" height="90"></canvas>
<br><br>
<canvas id="statusChart" height="90"></canvas>
<script>
const labels = {json.dumps(labels)};
const latencies = {json.dumps(latencies)};
const colors = {json.dumps(colors)};
const statusValues = {json.dumps(status_values)};
const statusLabels = {json.dumps(status_labels)};
new Chart(document.getElementById('latencyChart'), {{
  type: 'line',
  data: {{ labels: labels, datasets: [{{ label: 'Latency (ms)', data: latencies, borderColor: '#3498db', pointBackgroundColor: colors, pointRadius: 4, tension: .2 }}] }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Request latency over time (point color = outcome)' }} }}, scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }} }} }}
}});
new Chart(document.getElementById('statusChart'), {{
  type: 'bar',
  data: {{ labels: labels, datasets: [{{ label: 'Status code (0 = crash)', data: statusValues, backgroundColor: colors }}] }},
  options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Status code / crash timeline' }}, tooltip: {{ callbacks: {{ label: (ctx) => 'status=' + statusLabels[ctx.dataIndex] }} }} }}, scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }} }} }}
}});
</script>
</body></html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Dashboard written to {OUT_HTML}")


if __name__ == "__main__":
    main()
