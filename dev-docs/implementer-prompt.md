# Task: Add unit tests for src/gui/tabs/install_tab.py

## Context
We need to increase code coverage for the GUI module.
`src/gui/tabs/install_tab.py` is currently at 17% coverage.

## Goals
1. Create `tests/gui/test_install_tab.py`.
2. Mock `customtkinter` (as done for console_tab).
3. Test public methods:
    - `_on_check_env` (triggered by _start_env_check thread)
    - `_on_install_clicked` (button click)
    - `update_status`
    - `log_message`
    - `set_button_state`
    - `set_install_callback`
4. Use standard unittest.mock/pytest patterns.
5. Ensure 80%+ coverage for this file.

## Requirements
- Do not introduce UI dependencies (mock `customtkinter` entirely).
- Focus on testing logic flow and callback triggers.
- Use existing project structure (`tests/gui/`).
- Follow TDD (write test -> verify fail -> implement -> verify pass -> refactor).
