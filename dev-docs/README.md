# Dev Docs Organization

This directory contains development documentation organized by tickets.

## Structure

Each ticket has its own folder following this naming convention:
```
ticket-{number}-{short-description}/
```

### Within Each Ticket Folder:

1. **README.md** - Context, analysis, plans, and summary for AI agent
   - Problem description
   - Root cause analysis
   - Solution approach
   - Implementation details
   - Testing notes

2. **HTML files** - Interactive review documents for human-AI collaboration
   - Code diffs (side-by-side comparison)
   - Comment sections for review feedback
   - Generate/copy functionality for AI agent input
   - Visual before/after comparisons

## Current Tickets

### Active Tickets

- **ticket-6-target-pattern-fix/** - Fix target_pattern field to store actual regex patterns instead of hardcoded strings
  - `README.md` - Full analysis and solution
  - `fix-target-pattern-plan.html` - Interactive review page with code diffs

### Legacy Tickets (flat files, to be migrated)

- `ticket-3-tkinter-thread-safety.md` - GUI thread-safety crash fix
- `ticket-4-uv-font-issue.md` - Font rendering issue with uv-managed Python
- `ticket-5-temporary-message-id.md` - Handle temporary message IDs in Feishu chat

## How to Create a New Ticket

1. Create folder: `ticket-{N}-{short-description}/`
2. Create `README.md` with full context for AI
3. Create `{description}-plan.html` for interactive review
4. Update this README with ticket link

## Workflow

1. **AI Analysis** → Write `README.md` with problem analysis and plan
2. **Human Review** → Open HTML file, review code diffs, add comments
3. **Generate Output** → Use HTML copy function to send feedback to AI
4. **Implementation** → AI implements based on approved plan
5. **Documentation** → Update README with final implementation notes
