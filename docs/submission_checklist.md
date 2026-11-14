# Submission Checklist

## Deliverables (from the assignment)

| # | Deliverable | Where | Status |
|---|---|---|---|
| 1 | Working Version 1 | `version_1/` | Done. Played live with Gemini. |
| 2 | Version 2 with structured state and validation | `version_2/` | Done. Played live and without a key. |
| 3 | Architecture diagram for each version | `docs/architecture_v1.md`, `docs/architecture_v2.md` (+ PNGs in `docs/images/`) | Done |
| 4 | At least five test cases V1 vs V2 | `docs/testing.md` (8 scenarios), transcripts in `docs/test_results/` | Done |
| 5 | Report (2-3 pages) | `docs/development_report.pdf` (3 pages A4), source `docs/development_report.md` | Done |

## Requirements check

- [x] Streamlit interface with introduction, instructions, chat, restart and victory screen
- [x] Gemini as Game Master (free tier, `gemini-3.5-flash-lite`)
- [x] 5 main objects, 3 puzzles, final escape challenge
- [x] Examine, collect, use, solve, unlock actions
- [x] Conversation / progress remembered (V1 chat history, V2 state dict)
- [x] Clear solution and escape detection
- [x] V2: state in dicts/JSON, Python validation, inventory rule, rules and solutions outside the LLM
- [x] V2: invalid actions and adversarial inputs do not change the state
- [x] Error handling: missing key, API errors, timeouts, empty input, malformed LLM output
- [x] 90 automated tests pass (also from a fresh clone)
- [x] Real screenshots in `screenshots/`
- [x] `.env` is git-ignored. No key in any commit.

## Before you submit

1. Read the report and adjust the wording so it sounds like you. Add your name and student ID
   on the first line of `docs/development_report.md` (there is room: page 3 is half full).
2. If you edit the Markdown, ask Claude to rebuild `docs/development_report.pdf`, or open the
   Markdown in VS Code (Ctrl+Shift+V) and print it to PDF.
3. Run the app once yourself and practise the demo script in `docs/study_guide.md`.

## Publishing to GitHub

1. On <https://github.com/new> create an **empty** repository named
   `MiniProject_01_AI_Escape_Room`. Don't add a README, .gitignore or license, because the
   project already has them.
2. In PowerShell, in the project folder:

   ```powershell
   git remote add origin https://github.com/<your-username>/MiniProject_01_AI_Escape_Room.git
   git push -u origin main
   ```

   Git will open a browser window to sign in to GitHub the first time.
3. Check on GitHub that:
   - the README shows the diagrams and screenshots,
   - there is **no `.env` file** in the file list,
   - the commit history is visible under "Commits".
4. If you ever pasted your key anywhere public by mistake, revoke it at
   <https://aistudio.google.com/apikey> and create a new one.
