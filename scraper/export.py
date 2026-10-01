"""Save the lead list and print a summary."""
from datetime import datetime
from pathlib import Path

import pandas as pd


def build_summary(df, duplicates_removed):
    total = len(df)
    return {
        "Businesses found": total,
        "With phone number": int(df["has_phone"].sum()),
        "With website": int(df["has_website"].sum()),
        "Missing all contact info": int(df["missing_contact"].sum()),
        "Duplicates removed": duplicates_removed,
        "Sources": ", ".join(sorted(df["source"].unique())) if total else "",
    }


def export(df, summary, fmt="csv", out_dir="output", name="leads"):
    Path(out_dir).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = Path(out_dir) / f"{name}_{stamp}.{fmt}"

    if fmt == "csv":
        df.to_csv(path, index=False)
    elif fmt == "json":
        df.to_json(path, orient="records", indent=2)
    elif fmt == "xlsx":
        summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Leads", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            # Widen columns so the sheet is readable when the client opens it.
            for sheet in writer.sheets.values():
                for column in sheet.columns:
                    width = max(len(str(cell.value or "")) for cell in column)
                    sheet.column_dimensions[column[0].column_letter].width = min(width + 2, 60)
                sheet.freeze_panes = "A2"
    else:
        raise ValueError(f"Unknown format: {fmt}")

    return path


def print_summary(summary, path):
    print("\n" + "=" * 40)
    print("LEAD SUMMARY")
    print("=" * 40)
    for key, value in summary.items():
        print(f"{key:<26} {value}")
    print(f"\nSaved to: {path}")
