# Next Task Command

Intelligent work prioritization for the AI Impact Model project. Analyzes repository state and suggests the highest priority task.

## Usage

```bash
# Get next priority task
claude next

# Show detailed information
claude next -v
claude next --verbose

# Show all discovered tasks
claude next --all

# Output in JSON format (for scripting)
claude next --json
```

## Implementation

```bash
#!/bin/bash
cd "$(dirname "$0")" && cd ../..
source venv/bin/activate 2>/dev/null || true
python -m src.commands.next_task "$@"
```

## Description

The `next` command provides intelligent task prioritization by analyzing multiple aspects of your repository:

### Data Sources
- **Git Status**: Uncommitted changes, untracked files
- **Git History**: Unpushed commits, branch status
- **GitHub Integration**: Open issues, pull requests
- **Test Suite**: Failing tests, test collection errors
- **Code Analysis**: TODO/FIXME comments
- **Documentation**: Staleness detection

### Priority Scoring System

Tasks are scored on a 0-100 scale with the following weights:

| Category | Priority | Score | Indicators |
|----------|----------|-------|------------|
| Critical | 🔴 | 100 | Failing tests, broken builds |
| High | 🟠 | 70-75 | Uncommitted changes, unpushed commits |
| Medium | 🟡 | 40-60 | Open PRs, TODO comments, open issues |
| Low | 🟢 | 20-30 | Documentation updates, cleanup |

### Output Format

The command provides:
1. **Primary Recommendation**: The highest priority task with specific action
2. **Other Tasks**: Additional tasks ranked by priority
3. **Repository Health**: Quick status indicators

Example output:
```
🎯 NEXT PRIORITY TASK
==================================================

📌 Commit uncommitted changes
   You have 7 modified file(s) that should be committed

   Priority: 🟠 HIGH (75)
   Action:   git add -A && git commit -m 'Your commit message'
   Why:      Uncommitted changes should be saved to preserve work

📋 OTHER TASKS
--------------------------------------------------

  🟠 HIGH (70) Push commits to remote
       You have 15 unpushed commit(s) on main
       → git push origin main

  🟡 MEDIUM (40) Work on issue #1
       Add SQLite database for storing analysis results
       → gh issue view 1

📊 REPOSITORY HEALTH
--------------------------------------------------
  ✅ Tests passing
  ⚠️  1 uncommitted change set(s)
  ⬆️  Commits ready to push
  📝 3 open issue(s)
```

## Use Cases

### Daily Workflow
Start your day by running `claude next` to see what needs immediate attention.

### CI/CD Integration
Use `claude next --json` in scripts to programmatically check repository health:
```bash
if claude next --json | jq -e '.tasks[0].category == "critical"'; then
  echo "Critical tasks found!"
  exit 1
fi
```

### Team Coordination
Share `claude next` output in standup meetings to communicate priorities.

## Examples

### Check before committing
```bash
$ claude next
# Shows if tests are passing and what changes need committing
```

### Review all pending work
```bash
$ claude next --all
# Lists all discovered tasks with full details
```

### Get machine-readable output
```bash
$ claude next --json | jq '.tasks[0]'
# Returns the highest priority task in JSON format
```

## Exit Codes

- `0`: No critical tasks found
- `1`: Critical task pending (e.g., failing tests)

## Notes

- Requires git and GitHub CLI (`gh`) for full functionality
- Python tests are checked using pytest
- TODO comments are searched in `src/` directory
- Documentation staleness is based on git history comparison