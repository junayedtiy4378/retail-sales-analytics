"""Run from the project folder: python analyze.py."""

import argparse
from pathlib import Path

from retail_insights.pipeline import run_analysis


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Analyze the synthetic retail dataset.")
    parser.add_argument("--input", type=Path, default=root / "data" / "raw")
    parser.add_argument("--output", type=Path, default=root / "reports")
    args = parser.parse_args()
    try:
        summary = run_analysis(args.input, args.output)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f"Analysis failed: {exc}\n")
    print(f"Clean orders: {summary['clean_rows']} / {summary['raw_rows']}")
    print(f"Rejected rows: {summary['rejected_rows']}")
    print(f"Completed-order sales: BDT {summary['net_sales_bdt']:,.2f}")
    print(f"Gross profit: BDT {summary['gross_profit_bdt']:,.2f}")
    print(f"Reports: {args.output.resolve()}")
    print("Open dashboard.html in that folder with your browser.")


if __name__ == "__main__":
    main()
