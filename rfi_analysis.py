"""
rfi_analysis.py

Answers three questions about rfi_log.csv:
  1. How many days do RFIs take to get answered, by discipline and by
     who they are assigned to?
  2. Which Open RFIs are past due as of the data export date?
  3. How many RFIs were submitted each month?

Choices made (agreed before writing this script):
  - All durations are CALENDAR days (weekends and holidays count).
  - Void RFIs are left out of EVERY measure.
  - "As of" date is the data export date from README.md: 2026-10-30.
  - Past due = status Open AND date_required is BEFORE 2026-10-30.
    (An RFI due on the 30th itself is not late yet.)
  - The due date used is date_required from the log, as written.

The script only READS rfi_log.csv. Results go to the outputs/ folder.
Run it with:  python rfi_analysis.py
"""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # draw charts to files, without opening a window
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
DATA_FILE = Path("rfi_log.csv")
OUTPUT_DIR = Path("outputs")
AS_OF = pd.Timestamp("2026-10-30")   # data export date from README.md
DUE_DAYS = {"High": 3, "Medium": 7, "Low": 10}   # from README.md

OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Step 0: Load the data and turn the date columns into real dates
# ---------------------------------------------------------------------------
raw = pd.read_csv(DATA_FILE)
for col in ["date_submitted", "date_required", "date_answered"]:
    # errors="coerce" turns blanks or bad dates into NaT ("no date")
    raw[col] = pd.to_datetime(raw[col], errors="coerce")

raw["excel_row"] = raw.index + 2     # row number as seen in Excel
print(f"Loaded {len(raw)} RFIs from {DATA_FILE}")
print("Status counts:", raw["status"].value_counts().to_dict())

# Leave out Void RFIs from everything that follows
df = raw[raw["status"] != "Void"].copy()
print(f"Leaving out {len(raw) - len(df)} Void RFIs -> {len(df)} RFIs analyzed\n")

# ---------------------------------------------------------------------------
# Step 0b: Data quality checks (we report problems, we do not fix them)
# ---------------------------------------------------------------------------
flags = []

def flag(mask, problem):
    """Record every row where `mask` is True, with a description."""
    for _, r in df[mask].iterrows():
        flags.append({"rfi_id": r["rfi_id"], "excel_row": r["excel_row"],
                      "status": r["status"], "problem": problem})

flag(df["date_submitted"].isna(), "Missing or unreadable date_submitted")
flag(df["date_required"].isna(), "Missing or unreadable date_required")
flag((df["status"] == "Closed") & df["date_answered"].isna(),
     "Closed but no date_answered")
flag((df["status"] == "Open") & df["date_answered"].notna(),
     "Open but has a date_answered")
flag(df["date_answered"] < df["date_submitted"],
     "Answered before it was submitted")
flag(df["date_answered"] > AS_OF, "Answered after the export date")

# Does date_required match the priority rule in the README?
expected_due = df["date_submitted"] + pd.to_timedelta(
    df["priority"].map(DUE_DAYS), unit="D")
flag(df["date_required"].notna() & (df["date_required"] != expected_due),
     "date_required does not match priority rule (High 3 / Med 7 / Low 10 days)")

flags = pd.DataFrame(flags, columns=["rfi_id", "excel_row", "status", "problem"])
flags.to_csv(OUTPUT_DIR / "data_quality_flags.csv", index=False)
print("DATA QUALITY CHECKS")
if flags.empty:
    print("  No problems found.\n")
else:
    for problem, n in flags["problem"].value_counts().items():
        print(f"  {n:3d}  {problem}")
    print("  (details in outputs/data_quality_flags.csv)\n")

# ---------------------------------------------------------------------------
# Question 1: Days to answer, by discipline and by assignee
# ---------------------------------------------------------------------------
# Only answered RFIs have a turnaround time.
answered = df[df["date_answered"].notna() & df["date_submitted"].notna()].copy()
answered["days_to_answer"] = (answered["date_answered"]
                              - answered["date_submitted"]).dt.days
answered["answered_late"] = answered["date_answered"] > answered["date_required"]

def turnaround_table(group_col):
    """Summary of days to answer for each value in group_col."""
    t = answered.groupby(group_col).agg(
        answered_rfis=("days_to_answer", "size"),
        avg_days=("days_to_answer", "mean"),
        median_days=("days_to_answer", "median"),
        max_days=("days_to_answer", "max"),
        answered_late=("answered_late", "sum"),
    )
    # How many in each group are still waiting (Open)? Shown so a group
    # with many slow, unanswered RFIs does not look faster than it is.
    still_open = df[df["status"] == "Open"].groupby(group_col).size()
    t["still_open"] = still_open.reindex(t.index).fillna(0).astype(int)
    t["pct_answered_late"] = (100 * t["answered_late"] / t["answered_rfis"])
    t = t.round({"avg_days": 1, "median_days": 1, "pct_answered_late": 0})
    return t.sort_values("avg_days", ascending=False)

by_disc = turnaround_table("discipline")
by_assignee = turnaround_table("assigned_to")
by_disc.to_csv(OUTPUT_DIR / "days_to_answer_by_discipline.csv")
by_assignee.to_csv(OUTPUT_DIR / "days_to_answer_by_assignee.csv")

overall_avg = answered["days_to_answer"].mean()
overall_med = answered["days_to_answer"].median()
print("QUESTION 1 - Calendar days to answer (answered, non-Void RFIs)")
print(f"  Overall: {len(answered)} RFIs, average {overall_avg:.1f} days, "
      f"median {overall_med:.1f} days")
print("\n  By discipline:")
print(by_disc.to_string().replace("\n", "\n    "))
print("\n  By assigned to:")
print(by_assignee.to_string().replace("\n", "\n    "))
print()

# ---------------------------------------------------------------------------
# Question 2: Open RFIs past due as of the export date
# ---------------------------------------------------------------------------
open_rfis = df[df["status"] == "Open"].copy()
past_due = open_rfis[open_rfis["date_required"] < AS_OF].copy()
past_due["days_overdue"] = (AS_OF - past_due["date_required"]).dt.days
past_due = past_due.sort_values("days_overdue", ascending=False)

cols = ["rfi_id", "date_submitted", "date_required", "days_overdue",
        "priority", "discipline", "assigned_to", "submitted_by", "subject",
        "cost_impact", "schedule_impact_days", "excel_row"]
past_due_out = past_due[cols].copy()
for c in ["date_submitted", "date_required"]:
    past_due_out[c] = past_due_out[c].dt.strftime("%Y-%m-%d")
past_due_out.to_csv(OUTPUT_DIR / "open_rfis_past_due.csv", index=False)

print(f"QUESTION 2 - Open RFIs past due as of {AS_OF.date()}")
print(f"  {len(open_rfis)} Open RFIs, of which {len(past_due)} are past due "
      f"and {len(open_rfis) - len(past_due)} are not yet due.")
if not past_due.empty:
    print(f"  Days overdue: average {past_due['days_overdue'].mean():.1f}, "
          f"median {past_due['days_overdue'].median():.0f}, "
          f"max {past_due['days_overdue'].max()}")
    print("  By assigned to:",
          past_due["assigned_to"].value_counts().to_dict())
    print("  By priority:", past_due["priority"].value_counts().to_dict())
    print("\n  Full list (most overdue first):")
    print(past_due_out.drop(columns=["subject", "submitted_by", "cost_impact",
                                     "schedule_impact_days"])
          .to_string(index=False).replace("\n", "\n    "))
print()

# ---------------------------------------------------------------------------
# Question 3: RFIs submitted per month
# ---------------------------------------------------------------------------
df["month"] = df["date_submitted"].dt.to_period("M")
monthly = df.groupby(["month", "status"]).size().unstack(fill_value=0)
# Make sure every month from the first to the last appears, even if zero
all_months = pd.period_range(df["month"].min(), df["month"].max(), freq="M")
monthly = monthly.reindex(all_months, fill_value=0)
monthly.index.name = "month"
monthly["total"] = monthly.sum(axis=1)
monthly.to_csv(OUTPUT_DIR / "rfis_per_month.csv")

print("QUESTION 3 - RFIs submitted per month (Void left out)")
print(monthly.to_string().replace("\n", "\n    "))
busiest = monthly["total"].idxmax()
print(f"\n  Busiest month: {busiest} with {monthly['total'].max()} RFIs; "
      f"monthly average {monthly['total'].mean():.1f}\n")

# ---------------------------------------------------------------------------
# Chart: average days to answer by discipline
# ---------------------------------------------------------------------------
# Horizontal bars, sorted longest at top, one color (it is a single series).
plot = by_disc.sort_values("avg_days")      # smallest first -> bottom of chart
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
bars = ax.barh(plot.index, plot["avg_days"], color="#257de0", height=0.6)

# Write the value at the end of each bar, plus how many RFIs it is based on
for bar, (_, row) in zip(bars, plot.iterrows()):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{row['avg_days']:.1f} days  (n={int(row['answered_rfis'])})",
            va="center", fontsize=9, color="#191919", zorder=3,
            # white box behind the text so the dashed line doesn't cross it
            bbox=dict(facecolor="white", edgecolor="none", pad=1))

# Dashed line for the all-discipline average, for comparison.
# Its label sits below the bottom bar so it doesn't hit the title.
ax.axvline(overall_avg, color="#666666", linestyle="--", linewidth=1, zorder=1)
ax.text(overall_avg, -0.65, f" overall avg {overall_avg:.1f}",
        fontsize=8, color="#666666", va="center")
ax.set_ylim(-0.9, len(plot) - 0.5)

ax.set_title("Average calendar days to answer an RFI, by discipline",
             loc="left", fontsize=12, color="#191919")
ax.set_xlabel("Calendar days from submitted to answered "
              "(answered RFIs, Void excluded)", fontsize=9, color="#666666")
ax.set_xlim(0, plot["avg_days"].max() * 1.35)
# Quiet styling: light gridlines, no box around the chart
ax.grid(axis="x", color="#e7e7e7", linewidth=0.8)
ax.set_axisbelow(True)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color("#cccccc")
ax.tick_params(colors="#666666", labelsize=9)
ax.tick_params(axis="y", length=0, labelcolor="#191919")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "avg_days_by_discipline.png")
plt.close(fig)

print("Saved tables and outputs/avg_days_by_discipline.png to outputs/")
