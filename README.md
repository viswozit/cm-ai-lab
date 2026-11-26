# CM AI Lab

Starter files for the Claude Code assignment.

**All data here is synthetic.** The project, companies, and numbers are invented for teaching. Never put real project data, client documents, or personal information in a public repository.

## The project

Canyon View Medical Office Building (fictional)

- 4-story, steel-frame medical office building in the Phoenix area
- Notice to proceed: November 3, 2025
- Data exported: **October 30, 2026**. Use this as the "as of" date for any aging or past-due calculation.

## Files

| File | What it is |
|---|---|
| `rfi_log.csv` | The project's RFI log: 250 RFIs |
| `CLAUDE.md` | Standing instructions that Claude Code reads at the start of every session |
| `requirements.txt` | Python packages the scripts need |
| `outputs/` | Where scripts save charts and tables (created the first time a script runs) |

## Data dictionary: rfi_log.csv

| Column | Meaning |
|---|---|
| `rfi_id` | RFI number |
| `date_submitted` | Date the RFI was sent to the design team |
| `discipline` | Civil, Structural, Architectural, Mechanical, Electrical, Plumbing, Fire Protection |
| `subject` | Short description of the question |
| `submitted_by` | Subcontractor (or the GC) that raised the question |
| `priority` | High (answer due in 3 days), Medium (7 days), Low (10 days) |
| `assigned_to` | Who must answer: Architect, Structural Engineer, MEP Engineer, Civil Engineer, Owner |
| `date_required` | Date the answer is due |
| `date_answered` | Date the answer came back (blank if not answered) |
| `status` | Closed (answered), Open (still waiting), Void (withdrawn or duplicate) |
| `cost_impact` | Yes, No, or TBD |
| `schedule_impact_days` | Calendar days of schedule impact claimed (0 if none) |

Durations are calendar days unless you decide otherwise. Whatever you choose, say which one you used.
