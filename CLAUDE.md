# Instructions for Claude Code

This repository is used in a graduate construction management course on AI. The person you are working with is a construction professional who is new to programming and is working on their own, without an instructor nearby.

## How to work with this person

- Before you do something, say what you are about to do in plain English. Afterward, summarize what you did.
- Define any technical term the first time you use it. Keep explanations short.
- When there is a judgment call (for example calendar days vs. working days, or whether to count Void RFIs), state the choice and why.
- If something fails, explain the error in plain English and what you are doing to fix it.

## How to write code here

- Use Python. Use pandas for tables and matplotlib for charts.
- Install packages with `pip install -r requirements.txt`.
- Read README.md before analyzing data. It explains every column and gives the data export date (2026-10-30). Use that date, not today's date, for any "as of" calculation.
- Never edit `rfi_log.csv`. Save results to `outputs/`.
- Add comments that explain each step for a beginner.

## Checking the work

- After running a script, show the key numbers and explain how the person could check one of them by hand in Excel.
- Commit your work with a clear message that says what changed.
