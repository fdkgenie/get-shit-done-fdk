# GSD Sonnet-Gateway: Quick Start Guide

Get started with GSD Sonnet-Gateway in 5 minutes.

## What is GSD Sonnet-Gateway?

GSD Sonnet-Gateway adds **automatic complexity classification** and **cost optimization** to Get Shit Done. It analyzes your prompts in real-time and recommends the best approach:

- 🟢 **TRIVIAL**: Simple tasks → Use Sonnet directly (~$0.00-0.01)
- 🟡 **STANDARD**: Medium tasks → Use OpusPlan mode (~$0.02-0.05)
- 🔴 **COMPLEX**: Hard tasks → Use full GSD workflow (~$0.30-0.80)

**Result**: ~42% cost savings + better quality on complex tasks.

## Prerequisites

- Claude Code installed
- Get Shit Done (GSD) installed
- Python 3.8+ (check: `python3 --version`)
- Node.js (for statusline) (check: `node --version`)

## 5-Minute Setup

### Step 1: Copy Files

```bash
cd /path/to/get-shit-done-fdk

# Copy hooks to Claude config
cp hooks/gsd-complexity-classifier.py ~/.claude/hooks/
cp hooks/gsd-archive-files.py ~/.claude/hooks/
cp hooks/gsd-stats.py ~/.claude/hooks/
cp hooks/gsd-complexity-config.json ~/.claude/hooks/
cp hooks/gsd-statusline-enhanced.js ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/gsd-complexity-classifier.py
chmod +x ~/.claude/hooks/gsd-archive-files.py
chmod +x ~/.claude/hooks/gsd-stats.py
chmod +x ~/.claude/hooks/gsd-statusline-enhanced.js
```

### Step 2: Update Settings

Edit `~/.claude/settings.json` and add:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"$HOME/.claude/hooks/gsd-complexity-classifier.py\"",
        "timeout": 5
      }]
    }],

    "PreToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "python3 \"$HOME/.claude/hooks/gsd-archive-files.py\" pre",
        "timeout": 5
      }]
    }],

    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "python3 \"$HOME/.claude/hooks/gsd-archive-files.py\" post",
        "timeout": 5
      }]
    }]
  },

  "statusLine": {
    "type": "command",
    "command": "node ~/.claude/hooks/gsd-statusline-enhanced.js"
  }
}
```

**Note**: Merge with your existing hooks/statusline if you have them.

### Step 3: Test Installation

```bash
# Test complexity classifier
echo '{"prompt": "fix typo", "session_id": "test"}' | \
  python3 ~/.claude/hooks/gsd-complexity-classifier.py

# You should see JSON output with "TRIVIAL" classification

# Test stats (will be empty initially)
python3 ~/.claude/hooks/gsd-stats.py
```

### Step 4: Try It Out

Start Claude Code and send a prompt:

```
fix typo in README.md
```

You should see:
- Statusline shows 🟢 (green indicator)
- Claude receives recommendation: "Current model (Sonnet) is optimal"

Try a more complex prompt:

```
implement user authentication with JWT tokens, email verification, and password reset functionality
```

You should see:
- Statusline shows 🟡 (yellow indicator)
- Claude receives recommendation: "RECOMMENDED: Use /gsd:quick"

## First Week Usage

### Day 1-2: Learn the Indicators

Watch the statusline as you work:
- 🟢 = Simple task, Sonnet is fine
- 🟡 = Medium task, consider GSD quick mode
- 🔴 = Complex task, use full GSD workflow

### Day 3-4: Trust the Recommendations

Follow the recommendations:
- 🟢 TRIVIAL: Proceed with Sonnet
- 🟡 STANDARD: Try `/gsd:quick` or `/gsd:quick --discuss`
- 🔴 COMPLEX: Use `/gsd:plan-phase` or `/gsd:new-project`

### Day 5-7: Review and Optimize

Check your stats:

```bash
# Install aliases for convenience
echo 'alias gsd-stats="python3 ~/.claude/hooks/gsd-stats.py"' >> ~/.zshrc
echo 'alias gsd-stats-today="python3 ~/.claude/hooks/gsd-stats.py today"' >> ~/.zshrc
source ~/.zshrc

# View this week's stats
gsd-stats

# Review today's classifications
gsd-stats-today
```

Look for:
- What % of your prompts are COMPLEX? (High % might mean tasks should be broken down)
- What projects have most COMPLEX tasks? (Might need architecture work)
- Are you following recommendations? (Try to for a week and see results)

## Common Patterns

### Pattern 1: TRIVIAL Tasks (40% of prompts)

**Examples**:
- "fix typo in file.js"
- "rename function x to y"
- "git status"
- "add console.log to debug"

**Best Practice**: Execute immediately with Sonnet. Don't overthink.

### Pattern 2: STANDARD Tasks (45% of prompts)

**Examples**:
- "implement user login function"
- "add validation to form field"
- "fix bug in payment processing"
- "refactor component to use hooks"

**Best Practice**: Use `/gsd:quick` for structured approach. Add `--discuss` if you need context gathering.

### Pattern 3: COMPLEX Tasks (15% of prompts)

**Examples**:
- "migrate REST API to GraphQL"
- "redesign authentication system"
- "implement end-to-end testing framework"
- "refactor codebase to microservices"

**Best Practice**: Use full GSD workflow:
1. `/gsd:discuss-phase 1` - Gather requirements
2. `/gsd:plan-phase 1` - Create detailed plan
3. `/gsd:execute-phase 1` - Execute with verification

## Quick Commands Reference

```bash
# View all-time stats
gsd-stats

# View today's stats
gsd-stats-today

# Diff archive files
python3 ~/.claude/hooks/gsd-stats.py diff

# List archive files
python3 ~/.claude/hooks/gsd-stats.py list

# Customize classification patterns
vim ~/.claude/hooks/gsd-complexity-config.json
```

## Customization

### Adjust Classification Sensitivity

Edit `~/.claude/hooks/gsd-complexity-config.json`:

```json
{
  "word_thresholds": {
    "trivial_max": 10,     // Increase for more TRIVIALs
    "complex_min": 60,     // Decrease for more COMPLEXs
    "complex_boost": 100
  }
}
```

### Add Project-Specific Patterns

Add patterns that indicate complexity in your domain:

```json
{
  "complex_patterns": [
    "\\b(deploy|deployment).{0,20}production\\b",
    "\\b(database).{0,20}migration\\b",
    "\\b(your-framework-specific-pattern)\\b"
  ]
}
```

### Customize Watched Files

Control which files get archived:

```json
{
  "watched_files": [
    ".planning/**/PLAN.md",
    "docs/ARCHITECTURE.md",
    "specs/**/*.spec.md"
  ]
}
```

## Troubleshooting

### No complexity indicators appear

1. Check hooks are registered: `cat ~/.claude/settings.json | grep UserPromptSubmit`
2. Verify Python works: `python3 --version`
3. Test manually: `echo '{"prompt":"test","session_id":"test"}' | python3 ~/.claude/hooks/gsd-complexity-classifier.py`

### Classifications seem wrong

1. Review your prompt style - unusually short/long prompts may be misclassified
2. Customize patterns in `gsd-complexity-config.json`
3. Check logs: `cat ~/.claude/logs/gsd-complexity-classifier/classifications-*.jsonl`

### Archive not working

1. Verify PreToolUse/PostToolUse hooks are registered
2. Check hooks are executable: `ls -la ~/.claude/hooks/gsd-archive-files.py`
3. Verify `.gitignore` was updated: `cat .gitignore | grep claude`

### Stats show no data

1. Ensure classifier has run: Send a prompt in Claude Code
2. Check log directory: `ls ~/.claude/logs/gsd-complexity-classifier/`
3. Verify log files: `cat ~/.claude/logs/gsd-complexity-classifier/classifications-*.jsonl`

## Next Steps

1. **Read full documentation**: `docs/SONNET-GATEWAY-INTEGRATION.md`
2. **Explore GSD workflows**: Use `/gsd:help` in Claude Code
3. **Join the community**: Share feedback and learn from others
4. **Customize for your needs**: Edit config to match your workflow

## Tips for Success

1. **Trust the system for a week**: Give it time to learn your patterns
2. **Review stats weekly**: Identify trends and optimization opportunities
3. **Follow recommendations**: The classifier learns from common patterns
4. **Customize gradually**: Start with defaults, tune after collecting data
5. **Use archive for safety**: Never worry about losing planning artifacts

## Expected Results

After 1 week of usage:

- **Cost Reduction**: 30-50% reduction in Opus token usage
- **Quality Improvement**: Better outcomes on complex tasks
- **Time Savings**: Less back-and-forth on task scoping
- **Better Habits**: More structured approach to complex work

## Support

- **Full Documentation**: `docs/SONNET-GATEWAY-INTEGRATION.md`
- **Test Suite**: `tests/run_sonnet_gateway_tests.sh`
- **Configuration**: `hooks/gsd-complexity-config.json`
- **Logs**: `~/.claude/logs/gsd-complexity-classifier/`
- **Archive**: `.claude/archive/`

---

**Ready to Get Shit Done with smart cost optimization? Start using GSD Sonnet-Gateway today!**
