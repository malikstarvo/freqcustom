import csv
import json
import os

from .study import Study


class ReportData:
    def __init__(self) -> None:
        self.generated_at: str = ""
        self.symbols: str = ""
        self.timeframes: str = ""
        self.features: list[dict] = []
        self.top_features: list[str] = []
        self.summary: dict = {}


def _generate_html(study: Study) -> str:
    top = study.top_features(5)
    metrics_by_feature: dict[str, dict[str, float]] = {}
    for r in study.all_results:
        if r.feature_name not in metrics_by_feature:
            metrics_by_feature[r.feature_name] = {}
        key = r.metric_name
        if r.label_horizon:
            key = f"{r.metric_name}_{r.label_horizon}"
        metrics_by_feature[r.feature_name][key] = r.metric_value

    feature_names = sorted(metrics_by_feature.keys())

    top_section = ""
    for i, f in enumerate(top):
        top_section += f"<tr><td>{i+1}</td><td>{f}</td></tr>"

    rows_html = ""
    for fname in feature_names:
        metrics = metrics_by_feature[fname]
        rows_html += f"<tr><td>{fname}</td>"
        for mname in ["pearson", "spearman", "q_top_pf", "q_top_wr", "composite_score"]:
            for suffix in ["", "_future_return_4", "_future_return_12", "_future_return_24"]:
                key = mname + suffix
                val = metrics.get(key)
                if val is not None:
                    rows_html += f"<td>{val:.4f}</td>"
                    break
            else:
                rows_html += "<td>-</td>"
        decay_rate = metrics.get("decay_rate", "-")
        rows_html += f"<td>{decay_rate}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Edge Study Report</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a2e; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem; }}
h1 {{ color: #00d4ff; margin-bottom: 0.5rem; }}
h2 {{ color: #7b68ee; margin: 1.5rem 0 0.5rem; }}
.meta {{ color: #888; margin-bottom: 1.5rem; }}
table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
th {{ background: #16213e; color: #00d4ff; padding: 0.75rem; text-align: left; border-bottom: 2px solid #7b68ee; }}
td {{ padding: 0.5rem 0.75rem; border-bottom: 1px solid #333; }}
tr:hover {{ background: #16213e; }}
.top {{ color: #00ff88; font-weight: bold; }}
.summary {{ background: #16213e; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>Edge Study Report</h1>
<p class="meta">Generated: now | Features: {len(metrics_by_feature)} | Metrics: {len(study.all_results)}</p>

<h2>Top Features (Ranked)</h2>
<table>
<tr><th>Rank</th><th>Feature</th></tr>
{top_section}
</table>

<h2>All Features — Detailed Metrics</h2>
<table>
<tr><th>Feature</th><th>Pearson</th><th>Spearman</th><th>Q Top PF</th><th>Q Top WR</th><th>Composite</th><th>Decay Rate</th></tr>
{rows_html}
</table>

<div class="summary">
<h3>Summary</h3>
<p>Total features analyzed: {len(metrics_by_feature)}</p>
<p>Top 3: {", ".join(top[:3])}</p>
</div>
</body>
</html>"""


def export_html(study: Study, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    html = _generate_html(study)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)


def export_csv(study: Study, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["feature", "label_horizon", "metric", "value", "samples"])
        for r in study.all_results:
            w.writerow([r.feature_name, r.label_horizon, r.metric_name,
                        f"{r.metric_value:.6f}", str(r.samples)])


def export_json(study: Study, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    metrics_by_feature: dict[str, dict] = {}
    for r in study.all_results:
        if r.feature_name not in metrics_by_feature:
            metrics_by_feature[r.feature_name] = {}
        key = r.metric_name
        if r.label_horizon:
            key = f"{r.metric_name}_{r.label_horizon}"
        metrics_by_feature[r.feature_name][key] = {
            "value": r.metric_value,
            "samples": r.samples,
        }

    top = study.top_features(5)
    data = {
        "top_features": top,
        "features": metrics_by_feature,
        "total_metrics": len(study.all_results),
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
