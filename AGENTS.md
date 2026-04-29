# AGENTS.md - Feishu Auto-Liker GUI

## Run

```bash
python main.py
```

## Build Executable

```bash
python build.py
# Output: dist/飞书自动点赞助手.exe
```

## Dependencies

```
customtkinter>=5.2.0
playwright>=1.40.0
pyyaml>=6.0
loguru>=0.7.0
packaging>=23.0
subprocess-tee>=0.4.0
```

Install: `pip install -r requirements.txt && playwright install chromium`

## Key Files

- `main.py` - All application logic (GUI + RPA). Single file ~1066 lines.
- `config.yaml` - Runtime config (auto-generated)
- `state.json` - Message history to avoid duplicates
- `feishu_browser_data/` - Playwright persistent browser session

## Architecture

- **GUI**: CustomTkinter with 3 tabs (安装/控制台/设置)
- **RPA**: Async Playwright running in background thread
- **Pattern matching**: Supports `re:` prefix for regex keywords

## Notes

- No lint/test/typecheck configured
- Logs go to `rpa_bot.log`
- Browser data persists login session
- Playwright browser path: `~/.cache/ms-playwright` (Linux)
