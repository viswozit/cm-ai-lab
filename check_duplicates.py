"""
check_duplicates.py

Checks rfi_log.csv for three kinds of duplicates:
  1. RFI numbers (rfi_id) that appear more than once
  2. Rows that are exact copies of another row (every column identical)
  3. Possible duplicate questions: RFIs with the same subject submitted
     within 14 calendar days of each other

The script only READS rfi_log.csv. It never changes it.
Results are saved as CSV files in the outputs/ folder.

Run it with:  python check_duplicates.py
"""

from pathlib import Path   # helps build file paths that work on any computer
import pandas as pd        # pandas = the library for working with tables

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
DATA_FILE = Path("rfi_log.csv")
OUTPUT_DIR = Path("outputs")
WINDOW_DAYS = 14   # "within 14 days" -> calendar days, per the README default

# Create the outputs folder if it does not exist yet
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Step 0: Load the RFI log
# ---------------------------------------------------------------------------
# dtype=str reads every cell as plain text, exactly as typed in the file.
# That way "exact copy" really means the text is identical.
df = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False)

# The row number as you would see it in Excel (row 1 is the header,
# so the first RFI is on Excel row 2). Handy for checking by hand.
df["excel_row"] = df.index + 2

print(f"Loaded {len(df)} RFIs from {DATA_FILE}\n")

# The original columns only (not the helper column we just added)
data_cols = [c for c in df.columns if c != "excel_row"]

# ---------------------------------------------------------------------------
# Check 1: RFI numbers that appear more than once
# ---------------------------------------------------------------------------
# keep=False marks EVERY row in a repeated group, not just the 2nd one.
dup_ids = df[df.duplicated(subset="rfi_id", keep=False)]
dup_ids = dup_ids.sort_values(["rfi_id", "excel_row"])

print("CHECK 1 - RFI numbers used more than once")
if dup_ids.empty:
    print("  None found.\n")
else:
    counts = dup_ids["rfi_id"].value_counts().sort_index()
    print(f"  {len(counts)} RFI number(s) repeated:")
    for rfi, n in counts.items():
        rows = dup_ids.loc[dup_ids["rfi_id"] == rfi, "excel_row"].tolist()
        print(f"    {rfi}: appears {n} times (Excel rows {rows})")
    print()
dup_ids.to_csv(OUTPUT_DIR / "dup_rfi_numbers.csv", index=False)

# ---------------------------------------------------------------------------
# Check 2: Rows that are exact copies
# ---------------------------------------------------------------------------
# Compare all original columns. If every value matches, it is an exact copy.
exact = df[df.duplicated(subset=data_cols, keep=False)]
exact = exact.sort_values(["rfi_id", "excel_row"])

print("CHECK 2 - Rows that are exact copies of another row")
if exact.empty:
    print("  None found.\n")
else:
    groups = exact.groupby(data_cols, sort=False)["excel_row"].apply(list)
    print(f"  {len(groups)} set(s) of identical rows "
          f"({len(exact)} rows in total):")
    for key, rows in groups.items():
        print(f"    {key[0]} - '{key[3]}' (Excel rows {rows})")
    print()
exact.to_csv(OUTPUT_DIR / "dup_exact_rows.csv", index=False)

# ---------------------------------------------------------------------------
# Check 3: Same subject submitted within 14 days
# ---------------------------------------------------------------------------
# Judgment call: subjects are compared after removing extra spaces and
# ignoring capital letters, so "Roof drain" and "roof drain " match.
# Different wording does NOT match (that would need human review).
#
# Exact-copy rows from Check 2 are left out here, so the same row
# is not reported twice. Void RFIs are KEPT, because an RFI is often
# voided precisely because it was a duplicate.
work = df.drop_duplicates(subset=data_cols, keep="first").copy()
work["subject_key"] = (work["subject"].str.strip()
                       .str.replace(r"\s+", " ", regex=True).str.lower())
work["submitted"] = pd.to_datetime(work["date_submitted"], errors="coerce")

pairs = []
# Look at each group of RFIs that share the same subject
for subject, grp in work.groupby("subject_key"):
    if len(grp) < 2:
        continue  # only one RFI with this subject, nothing to compare
    grp = grp.sort_values("submitted")
    rows = grp.to_dict("records")
    # Compare every pair of RFIs inside the group
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            gap = (b["submitted"] - a["submitted"]).days
            if gap <= WINDOW_DAYS:
                pairs.append({
                    "subject": a["subject"],
                    "first_rfi": a["rfi_id"],
                    "first_submitted": a["date_submitted"],
                    "first_status": a["status"],
                    "first_submitted_by": a["submitted_by"],
                    "second_rfi": b["rfi_id"],
                    "second_submitted": b["date_submitted"],
                    "second_status": b["status"],
                    "second_submitted_by": b["submitted_by"],
                    "days_apart": gap,
                    "first_excel_row": a["excel_row"],
                    "second_excel_row": b["excel_row"],
                })

near = pd.DataFrame(pairs)
print(f"CHECK 3 - Same subject submitted within {WINDOW_DAYS} calendar days")
if near.empty:
    print("  None found.\n")
else:
    near = near.sort_values(["first_submitted", "first_rfi"])
    print(f"  {len(near)} possible duplicate pair(s):")
    for _, r in near.iterrows():
        print(f"    {r.first_rfi} ({r.first_submitted}, {r.first_status}) & "
              f"{r.second_rfi} ({r.second_submitted}, {r.second_status}) "
              f"- {r.days_apart} days apart - '{r.subject}'")
    print()
near.to_csv(OUTPUT_DIR / "dup_possible_questions.csv", index=False)

# For context: same subject repeated, but MORE than 14 days apart
repeat_subjects = work["subject_key"].duplicated(keep=False).sum()
print(f"Note: {repeat_subjects} RFIs share a subject with at least one "
      f"other RFI (at any distance in time).")
print(f"\nResults saved to the {OUTPUT_DIR}/ folder.")
