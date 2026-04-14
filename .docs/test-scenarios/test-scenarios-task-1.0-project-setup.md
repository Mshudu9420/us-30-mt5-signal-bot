# Test Scenarios: Task 1.0 Project Setup & Environment Configuration

**Task Reference:** `.docs/tasks/tasks-prd-us30-mt5-signal-bot.md`  
**PRD Reference:** `.docs/prd/prd-us30-mt5-signal-bot.md`  
**Date:** 2026-04-14  
**Execution Point:** Run this test set after all Task 1.0 subtasks are completed.

---

## 1. Purpose

Validate that Task 1.0 outcomes are fully achieved and the project baseline is ready for Task 2.0+ implementation.

This test set verifies:

- Project structure completeness
- Dependency definition correctness
- Secure local environment handling
- Config readiness for PRD goals and user stories
- Documentation completeness for setup and credentials
- Git/GitHub baseline readiness for collaboration

---

## 2. Coverage Mapping

| Test ID | Task 1.0 Subtask | Objective Coverage |
|---|---|---|
| T1-001 | 1.1 | Project skeleton exists with all required stubs |
| T1-002 | 1.2 | Dependencies required for PRD technical scope are declared |
| T1-003 | 1.3 | Sensitive and generated artifacts are ignored from version control |
| T1-004 | 1.4 | Central config exposes all required runtime parameters |
| T1-005 | 1.5 | `.env` template exists and README explains credential population |
| T1-006 | 1.6 | Repository is initialized, linked to GitHub, and initial skeleton is push-ready |

---

## 3. Validation Scenarios

| ID | Scenario | Preconditions | Steps | Expected Result | Pass/Fail |
|---|---|---|---|---|---|
| T1-001 | Verify full project folder structure | Workspace available | 1) Open project root. 2) Confirm `us30-signal-bot/` exists. 3) Verify required files exist: `config.py`, `main.py`, `mt5_connector.py`, `mt5_mock.py`, `indicators.py`, `strategy.py`, `risk_manager.py`, `signal_output.py`, `alerts.py`, `requirements.txt`, `.gitignore`, `.env`, `README.md`. 4) Verify `tests/` includes `test_indicators.py`, `test_strategy.py`, `test_risk_manager.py`, `test_alerts.py`, `test_mt5_connector.py`. | All required files/folders exist and are accessible. | |
| T1-002 | Verify required dependencies list | `requirements.txt` exists | 1) Open `requirements.txt`. 2) Confirm presence of: `MetaTrader5`, `pandas`, `pandas-ta`, `colorama`, `python-dotenv`, `pytest`. | All listed dependencies are present exactly once and correctly named. | |
| T1-003 | Verify `.gitignore` excludes required items | `.gitignore` exists | 1) Open `.gitignore`. 2) Confirm entries for `.env`, `__pycache__/`, `*.log`, `venv/`, `*.pyc`. | Ignore rules match Task 1.3 requirements. | |
| T1-004 | Verify config parameter completeness | `config.py` exists | 1) Open `config.py`. 2) Confirm symbol setting exists. 3) Confirm capital setting exists. 4) Confirm risk mode setting exists. 5) Confirm timeframe settings exist. 6) Confirm BB/RSI/EMA settings exist. 7) Confirm polling interval exists. 8) Confirm SL buffer pips exists. 9) Confirm email toggle exists. | Config file contains all required task parameters and is centrally organized. | |
| T1-005 | Verify `.env` template + documentation | `.env` and `README.md` exist | 1) Open `.env` and confirm placeholder values (no real credentials). 2) Open `README.md`. 3) Confirm section explains how to populate `.env` keys. 4) Confirm warning to avoid committing secrets is documented. | `.env` is template-safe and README provides clear setup instructions. | |
| T1-006 | Verify Git/GitHub readiness | Git installed; remote configured | 1) Run `git rev-parse --is-inside-work-tree`. 2) Run `git remote -v`. 3) Confirm GitHub remote points to project repository. 4) Run `git status --short` to check change visibility for new skeleton files. | Repository is initialized, connected to GitHub, and changes are visible/push-ready. | |

---

## 4. User-Story and PRD Objective Alignment

Task 1.0 does not implement trading logic directly, but it must establish prerequisites for these PRD goals:

- G1/G2/G3/G4: Config and module stubs exist to support signal logic, H1 filter, and risk calculation implementation.
- G5/G6/G7: Main entrypoint, output module, and startup/config documentation are in place.

Pass condition for alignment:

- All scenarios T1-001 through T1-006 pass.
- No missing required file or config key blocks Task 2.0 start.

---

## 5. Sign-Off Checklist

- [ ] T1-001 passed
- [ ] T1-002 passed
- [ ] T1-003 passed
- [ ] T1-004 passed
- [ ] T1-005 passed
- [ ] T1-006 passed
- [ ] Task 1.0 accepted and closed
