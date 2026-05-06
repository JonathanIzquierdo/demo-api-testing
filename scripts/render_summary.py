#!/usr/bin/env python3
"""
Render a markdown summary from metrics.json (for $GITHUB_STEP_SUMMARY).
"""
import argparse
import json
from pathlib import Path


def coverage_bar(pct: float, width: int = 20) -> str:
    filled = int(round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def render(metrics: dict) -> str:
    cov = metrics["coverage"]
    nw = metrics["newman"]

    cov_emoji = "🟢" if cov["pct"] >= 80 else "🟡" if cov["pct"] >= 50 else "🔴"
    pass_emoji = "🟢" if nw["pass_rate_pct"] == 100 else "🟡" if nw["pass_rate_pct"] >= 80 else "🔴"

    lines = []
    lines.append("# 📊 API Test Report")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"{cov_emoji} **{cov['pct']}%** — `{cov['covered']}/{cov['total_endpoints']}` endpoints covered")
    lines.append("")
    lines.append(f"```")
    lines.append(f"{coverage_bar(cov['pct'])} {cov['pct']}%")
    lines.append(f"```")
    lines.append("")

    if cov["uncovered_endpoints"]:
        lines.append("### ⚠️ Uncovered endpoints")
        lines.append("")
        for ep in cov["uncovered_endpoints"]:
            lines.append(f"- `{ep}`")
        lines.append("")
        lines.append("> Trigger `QA Agent: Full Scan` in QAEngineerAgent to generate tests for these.")
        lines.append("")

    lines.append("## Test Run")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total assertions | {nw['total']} |")
    lines.append(f"| Passed | {nw['passed']} |")
    lines.append(f"| Failed | {nw['failed']} |")
    lines.append(f"| Pass rate | {pass_emoji} {nw['pass_rate_pct']}% |")
    lines.append(f"| Duration | {nw['duration_ms'] / 1000:.1f}s |")
    lines.append("")

    if nw["failed"] > 0:
        lines.append("> 🔧 Tests are failing. Trigger `QA Agent: Heal Tests` to diagnose and propose fixes.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True)
    args = parser.parse_args()

    metrics = json.loads(Path(args.metrics).read_text())
    print(render(metrics))


if __name__ == "__main__":
    main()
