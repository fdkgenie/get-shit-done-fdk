# GSD Sonnet-Gateway Integration

Comprehensive implementation of Sonnet-Gateway features for Get Shit Done (GSD), providing automatic complexity classification, cost optimization, and intelligent model routing.

## Overview

GSD Sonnet-Gateway enhances the Get Shit Done framework with:

- **Automatic Complexity Classification**: Real-time analysis of user prompts to determine task complexity
- **Cost Optimization**: Smart model routing based on task requirements (TRIVIAL → Sonnet, STANDARD → OpusPlan, COMPLEX → Full Opus)
- **Audit Trail**: Complete logging of all classifications and decisions for cost analysis
- **Archive System**: Automatic backup of planning artifacts with pre/post snapshots
- **Enhanced Statusline**: Visual complexity indicators integrated into the Claude Code statusline

## Architecture

### Hybrid Integration Approach

GSD Sonnet-Gateway follows a hybrid architecture that combines:

1. **Pre-GSD Hook**: Complexity classification runs before GSD commands
2. **GSD Profile Enhancement**: Automatic routing to appropriate GSD profiles
3. **Statusline Integration**: Real-time complexity visibility for users

```
User Prompt
    ↓
Complexity Classifier Hook (UserPromptSubmit)
    ↓
Classification: TRIVIAL / STANDARD / COMPLEX
    ↓
GSD Profile Recommendation
    ↓
┌─────────────┬──────────────────┬───────────────────────┐
│ TRIVIAL 🟢  │  STANDARD 🟡     │  COMPLEX 🔴           │
│ Sonnet-only │  OpusPlan mode   │  Full GSD workflow    │
│ Direct exec │  Opus → Sonnet   │  Multi-phase Opus-led │
│ ~$0.00-0.01 │  ~$0.02-0.05     │  ~$0.30-0.80         │
└─────────────┴──────────────────┴───────────────────────┘
    ↓
Execution with GSD guarantees:
- Wave-based parallelization
- Automated checkpoints
- Verification loops
- Atomic git commits
```

## Components

### 1. Complexity Classifier (`gsd-complexity-classifier.py`)

**Purpose**: Analyzes user prompts and classifies them into complexity levels.

**Location**: `hooks/gsd-complexity-classifier.py`

**Hook Type**: `UserPromptSubmit` (runs before Claude processes the prompt)

**Classification Logic**:
- **TRIVIAL**: Simple tasks (typo fixes, formatting, git commands)
  - Word count < 10
  - Matches trivial patterns only
  - No complex patterns present

- **STANDARD**: Medium complexity tasks (implement function, fix bug, refactor module)
  - Moderate word count (10-60 words)
  - Matches standard patterns
  - Some complexity indicators but not overwhelming

- **COMPLEX**: High complexity tasks (system redesign, migration, multi-file refactoring)
  - High word count (> 60 words) or
  - Strong complex pattern matches (≥2) or
  - Complex pattern + sufficient word count

**Configuration**: `hooks/gsd-complexity-config.json`

**Example Classifications**:

```bash
# TRIVIAL 🟢
"fix typo in README"
"git status"
"rename variable x to y"

# STANDARD 🟡
"implement user login function"
"fix bug in payment processing"
"add validation to email field"

# COMPLEX 🔴
"migrate entire REST API to GraphQL"
"redesign authentication system"
"refactor codebase to microservices"
```

**Output**: Injects `additionalContext` with:
- Complexity level and emoji indicator
- Recommended GSD profile
- Estimated cost
- Pipeline instructions

### 2. Archive System (`gsd-archive-files.py`)

**Purpose**: Automatically backs up GSD planning files before and after modifications.

**Location**: `hooks/gsd-archive-files.py`

**Hook Types**:
- `PreToolUse` (before Claude writes files)
- `PostToolUse` (after Claude writes files)

**Watched Files** (default):
- `.planning/**/PLAN.md`
- `.planning/**/SUMMARY.md`
- `.planning/**/RESEARCH.md`
- `.planning/**/CONTEXT.md`
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/PROJECT.md`

**Archive Location**: `.claude/archive/`

**Filename Format**: `{original-name}-{YYYYMMDD-HHMMSS}-{phase}.md`

**Example Timeline**:
```
10:00:00 - PreToolUse  → PLAN-20260308-100000-pre.md  (old version saved)
10:00:01 - Claude writes new content
10:00:02 - PostToolUse → PLAN-20260308-100002-post.md (new version saved)
```

**Benefits**:
- Never lose planning artifacts even if Claude crashes
- Full audit trail of all changes
- Easy diffing between versions
- Rollback capability

### 3. Stats & Audit Utility (`gsd-stats.py`)

**Purpose**: Analyze classification logs and archive files for cost tracking and auditing.

**Location**: `hooks/gsd-stats.py`

**Usage**:

```bash
# View all-time stats
python3 ~/.claude/hooks/gsd-stats.py

# View today's stats only
python3 ~/.claude/hooks/gsd-stats.py today

# Diff archive files
python3 ~/.claude/hooks/gsd-stats.py diff

# List archive files
python3 ~/.claude/hooks/gsd-stats.py list
```

**Stats Output Example**:
```
============================================================
  GSD Sonnet-Gateway Stats — All time  (47 prompts)
============================================================
  🟢 TRIVIAL     18 ( 38%)  ███████░░░
  🟡 STANDARD    21 ( 45%)  █████████░
  🔴 COMPLEX      8 ( 17%)  ███░░░░░░░

  Total estimated Opus cost: ~96,000 tokens (~$0.4800)

  By project:
    my-web-app                      23 prompts  (3 complex)
    api-service                     15 prompts  (2 complex)
    data-pipeline                    9 prompts  (3 complex)

  Last 5 COMPLEX prompts:
    [2026-03-08 15:30] [api-service] migrate entire REST API to GraphQL…
    [2026-03-08 14:15] [my-web-app] redesign authentication system…
    [2026-03-08 10:45] [data-pipeline] architect new ETL pipeline…
============================================================
```

### 4. Enhanced Statusline (`gsd-statusline-enhanced.js`)

**Purpose**: Display complexity indicators in Claude Code statusline.

**Location**: `hooks/gsd-statusline-enhanced.js`

**Features**:
- Shows complexity emoji (🟢🟡🔴) for current session
- Integrates with existing GSD statusline features
- Displays model, task, directory, and context usage
- Updates in real-time

**Display Format**:
```
🟡 Sonnet │ Implementing user authentication │ my-project ████████░░ 80%
│  │       │                                  │            │
│  │       │                                  │            └─ Context usage
│  │       │                                  └─ Project directory
│  │       └─ Current task
│  └─ Model
└─ Complexity indicator
```

### 5. Configuration (`gsd-complexity-config.json`)

**Purpose**: Centralized configuration for all Sonnet-Gateway components.

**Location**: `hooks/gsd-complexity-config.json`

**Key Settings**:

```json
{
  "word_thresholds": {
    "trivial_max": 10,
    "complex_min": 60,
    "complex_boost": 100
  },

  "trivial_patterns": [
    "\\b(fix typo|rename|format)\\b",
    "\\b(git (status|log|diff))\\b"
  ],

  "standard_patterns": [
    "\\b(implement|add|create).{0,30}(function|method|class)\\b"
  ],

  "complex_patterns": [
    "\\b(architect|design|migrate)\\b",
    "\\b(refactor).{0,20}(entire|whole|all)\\b"
  ],

  "cost_estimate_tokens": {
    "TRIVIAL": 0,
    "STANDARD": 4000,
    "COMPLEX": 12000
  },

  "gsd_profiles": {
    "TRIVIAL": "sonnet-direct",
    "STANDARD": "opusplan",
    "COMPLEX": "opus-full"
  }
}
```

**Customization**: Edit this file without restarting Claude Code. Changes take effect immediately.

## Installation

### 1. Copy Hooks to Claude Config

```bash
# Copy all Sonnet-Gateway hooks
cp hooks/gsd-complexity-classifier.py ~/.claude/hooks/
cp hooks/gsd-archive-files.py ~/.claude/hooks/
cp hooks/gsd-stats.py ~/.claude/hooks/
cp hooks/gsd-complexity-config.json ~/.claude/hooks/
cp hooks/gsd-statusline-enhanced.js ~/.claude/hooks/

# Make scripts executable
chmod +x ~/.claude/hooks/gsd-complexity-classifier.py
chmod +x ~/.claude/hooks/gsd-archive-files.py
chmod +x ~/.claude/hooks/gsd-stats.py
chmod +x ~/.claude/hooks/gsd-statusline-enhanced.js
```

### 2. Register Hooks in Settings

Add to `~/.claude/settings.json`:

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

### 3. Verify Installation

```bash
# Test complexity classifier
echo '{"prompt": "fix typo", "session_id": "test"}' | \
  python3 ~/.claude/hooks/gsd-complexity-classifier.py

# Expected output: JSON with TRIVIAL classification

# Test stats utility
python3 ~/.claude/hooks/gsd-stats.py

# Expected output: Stats summary (may be empty on first run)
```

### 4. Add Aliases (Optional)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# GSD Sonnet-Gateway shortcuts
alias gsd-stats='python3 ~/.claude/hooks/gsd-stats.py'
alias gsd-stats-today='python3 ~/.claude/hooks/gsd-stats.py today'
alias gsd-diff='python3 ~/.claude/hooks/gsd-stats.py diff'
alias gsd-archive='python3 ~/.claude/hooks/gsd-stats.py list'
```

## Usage

### Basic Workflow

1. **Start a new task**
   - User sends prompt to Claude Code
   - Complexity classifier automatically analyzes prompt
   - Classification appears as `additionalContext` in Claude's view
   - Statusline shows complexity indicator (🟢🟡🔴)

2. **Claude receives recommendation**
   - TRIVIAL: "Current model (Sonnet) is optimal"
   - STANDARD: "RECOMMENDED: Use /gsd:quick --discuss"
   - COMPLEX: "STRONGLY RECOMMENDED: Use /gsd:plan-phase"

3. **Execute with GSD**
   - Follow the recommendation for best results
   - GSD orchestrates the work with appropriate model mix
   - Archive system backs up all planning artifacts
   - Classification logged for audit

4. **Review and analyze**
   - Check stats: `gsd-stats`
   - Review archive: `gsd-archive`
   - Diff changes: `gsd-diff`

### Example Workflows

#### TRIVIAL Task: Fix Typo

```bash
# User prompt
"fix typo in README.md"

# Classification
🟢 TRIVIAL - Sonnet-only direct execution

# Recommendation
✅ Current model (Sonnet) is optimal for this task.
- Execute directly with Sonnet
- NO Opus invocation required

# Action
Claude fixes typo immediately with Sonnet
Cost: ~$0.001
```

#### STANDARD Task: Implement Feature

```bash
# User prompt
"implement user login function with JWT authentication"

# Classification
🟡 STANDARD - OpusPlan mode recommended

# Recommendation
⚠️ RECOMMENDED: Use GSD with opusplan profile
Consider: /gsd:quick --discuss

# Action
User runs: /gsd:quick --discuss
Pipeline:
- Opus creates implementation plan
- Sonnet executes according to plan
- Sonnet verifies tests pass

Cost: ~$0.03
```

#### COMPLEX Task: System Migration

```bash
# User prompt
"migrate entire REST API to GraphQL with schema, resolvers, and tests"

# Classification
🔴 COMPLEX - Full GSD orchestration

# Recommendation
🚨 STRONGLY RECOMMENDED: Use full GSD workflow
Best approach: /gsd:plan-phase

# Action
User runs: /gsd:plan-phase 1
Pipeline:
- Phase 1 (Opus): Research GraphQL patterns
- Phase 2 (Opus): Architect schema design
- Phase 3 (Opus): Create wave execution plan
- Phase 4 (Sonnet): Execute in parallel waves
  - Wave 1: Schema + types
  - Wave 2-4: Resolvers (parallel)
  - Wave 5: Test migration
- Phase 5 (Sonnet): Integration testing
- Phase 6 (Opus): Final review

Cost: ~$0.60
```

## Cost Optimization

### Baseline Comparison

**Without Sonnet-Gateway**:
- All tasks use same model (usually Opus or Sonnet)
- No complexity-based routing
- Potential over-spending on simple tasks
- Potential under-quality on complex tasks

**With Sonnet-Gateway**:
- Automatic task routing
- Right model for right task
- Cost savings on TRIVIAL tasks (~40% of prompts)
- Quality improvement on COMPLEX tasks (~15% of prompts)

### Expected Savings

Based on typical usage patterns:

| Scenario | Without SG | With SG | Savings |
|----------|-----------|---------|---------|
| 100 prompts (40T, 45S, 15C) | $2.50 | $1.45 | 42% |
| 50 prompts (20T, 25S, 5C) | $1.25 | $0.73 | 42% |
| 200 prompts (80T, 90S, 30C) | $5.00 | $2.90 | 42% |

**Note**: Savings assume baseline of all-Opus usage. Actual savings vary based on prompt distribution.

### Cost Tracking

Monitor costs with stats utility:

```bash
# Daily cost review
gsd-stats-today

# Weekly cost review
gsd-stats

# Identify expensive patterns
# Look for high COMPLEX counts in specific projects
```

## Best Practices

### 1. Trust the Classification

The classifier is trained on patterns that correlate with task complexity. Trust its recommendations:

- 🟢 **TRIVIAL**: Go ahead with Sonnet directly
- 🟡 **STANDARD**: Use `/gsd:quick` or OpusPlan mode
- 🔴 **COMPLEX**: Use full GSD workflow (`/gsd:plan-phase`)

### 2. Review Stats Regularly

Weekly or bi-weekly review of classification stats helps:

- Identify projects with high COMPLEX ratios (may need architecture work)
- Spot opportunities to break complex tasks into smaller pieces
- Track cost trends over time

### 3. Customize Patterns

Edit `gsd-complexity-config.json` to tune classification:

- Add domain-specific patterns for your projects
- Adjust word count thresholds based on your prompt style
- Modify cost estimates to match your usage patterns

### 4. Use Archive for Rollback

If GSD generates incorrect plans:

```bash
# List archives
gsd-archive

# Find the pre-archive version
# Copy it back to overwrite bad version
cp .claude/archive/PLAN-20260308-100000-pre.md .planning/phase-1/PLAN.md

# Re-run GSD execution
/gsd:execute-phase 1
```

### 5. Combine with GSD Features

Sonnet-Gateway enhances but doesn't replace GSD features:

- Use `/gsd:verify-work` for manual UAT
- Use `/gsd:pause-work` for context management
- Use `/gsd:debug` for systematic debugging
- Archive system complements GSD's git commits

## Troubleshooting

### Classifier Not Running

**Symptom**: No complexity indicators in output

**Solutions**:
1. Verify hook is registered in `~/.claude/settings.json`
2. Check hook is executable: `ls -la ~/.claude/hooks/gsd-complexity-classifier.py`
3. Test manually: `echo '{"prompt":"test","session_id":"test"}' | python3 ~/.claude/hooks/gsd-complexity-classifier.py`
4. Check Python version: `python3 --version` (should be 3.8+)

### Wrong Classifications

**Symptom**: Tasks classified incorrectly

**Solutions**:
1. Review patterns in `gsd-complexity-config.json`
2. Add domain-specific patterns for your use case
3. Adjust word count thresholds if you write unusually short/long prompts
4. Check classification logs: `gsd-stats today`

### Archive Not Working

**Symptom**: Files not appearing in `.claude/archive/`

**Solutions**:
1. Verify hooks are registered for PreToolUse and PostToolUse
2. Check hooks are executable
3. Verify file matches watched patterns in config
4. Check `.gitignore` has been updated (auto-updated on first run)

### Statusline Not Showing Complexity

**Symptom**: No emoji indicators in statusline

**Solutions**:
1. Verify enhanced statusline is registered in settings
2. Check classification logs exist: `ls ~/.claude/logs/gsd-complexity-classifier/`
3. Restart Claude Code to reload statusline
4. Test statusline manually: `echo '{"session_id":"test","model":{"display_name":"Sonnet"}}' | node ~/.claude/hooks/gsd-statusline-enhanced.js`

### Stats Show No Data

**Symptom**: `gsd-stats` returns "No classification logs found"

**Solutions**:
1. Ensure classifier has run at least once
2. Check log directory exists: `ls ~/.claude/logs/gsd-complexity-classifier/`
3. Verify log files have content: `cat ~/.claude/logs/gsd-complexity-classifier/classifications-*.jsonl`
4. Run a test classification to generate logs

## Integration with GSD Commands

### Recommended Command Mapping

Based on complexity level, use these GSD commands:

| Complexity | GSD Command | Use Case |
|-----------|-------------|----------|
| 🟢 TRIVIAL | Direct Sonnet | Quick fixes, simple changes |
| 🟡 STANDARD | `/gsd:quick` | Single features, bug fixes |
| 🟡 STANDARD | `/gsd:quick --discuss` | Features needing context gathering |
| 🔴 COMPLEX | `/gsd:plan-phase` | Multi-file changes, new systems |
| 🔴 COMPLEX | `/gsd:new-project` | Greenfield projects, major rewrites |

### GSD Profile Configuration

Add to `.planning/config.json` for automatic profile selection:

```json
{
  "sonnet_gateway": {
    "enabled": true,
    "auto_profile": true,
    "profile_mapping": {
      "TRIVIAL": "sonnet-direct",
      "STANDARD": "opusplan",
      "COMPLEX": "opus-full"
    }
  }
}
```

## Advanced Configuration

### Custom Patterns

Add project-specific patterns to `gsd-complexity-config.json`:

```json
{
  "complex_patterns": [
    "\\b(migrate|migration)\\b",
    "\\b(deploy|deployment).{0,20}(production|prod)\\b",
    "\\b(database).{0,20}(schema|migration|upgrade)\\b",
    "\\b(your-domain-specific-pattern)\\b"
  ]
}
```

### Multi-Language Support

The classifier supports pattern matching in multiple languages. Add patterns for your language:

```json
{
  "complex_patterns": [
    "\\b(thiết kế|kiến trúc|triển khai)\\b",  // Vietnamese
    "\\b(diseñar|arquitectura|migrar)\\b",   // Spanish
    "\\b(konzipieren|architektur|migrieren)\\b" // German
  ]
}
```

### Cost Estimate Tuning

Adjust token estimates based on your actual usage:

```json
{
  "cost_estimate_tokens": {
    "TRIVIAL": 0,
    "STANDARD": 6000,   // If your STANDARD tasks typically use more
    "COMPLEX": 15000    // Adjust based on actual complex task costs
  }
}
```

### Watched Files Customization

Customize which files get archived:

```json
{
  "watched_files": [
    ".planning/**/PLAN.md",
    ".planning/**/SUMMARY.md",
    "docs/ARCHITECTURE.md",      // Add custom docs
    "specs/**/*.spec.md",        // Add spec files
    "your-custom-pattern.md"
  ]
}
```

## Testing

### Run Test Suite

```bash
# Run all tests
bash tests/run_sonnet_gateway_tests.sh

# Run with verbose output
bash tests/run_sonnet_gateway_tests.sh -v
```

### Manual Testing

```bash
# Test TRIVIAL classification
echo '{"prompt": "fix typo in README", "session_id": "test"}' | \
  python3 hooks/gsd-complexity-classifier.py

# Test STANDARD classification
echo '{"prompt": "implement user login function", "session_id": "test"}' | \
  python3 hooks/gsd-complexity-classifier.py

# Test COMPLEX classification
echo '{"prompt": "migrate entire REST API to GraphQL with schema and resolvers and comprehensive test coverage", "session_id": "test"}' | \
  python3 hooks/gsd-complexity-classifier.py

# Test archive (requires actual file)
echo '{"tool_name":"Write","tool_input":{"file_path":"test.md"}}' | \
  CLAUDE_PROJECT_DIR="." python3 hooks/gsd-archive-files.py pre
```

## API Reference

### Complexity Classifier

**Input** (stdin JSON):
```json
{
  "prompt": "user's prompt text",
  "session_id": "unique-session-id"
}
```

**Output** (stdout JSON):
```json
{
  "additionalContext": "[GSD-SONNET-GATE: STANDARD 🟡]\n..."
}
```

**Exit Codes**:
- `0`: Success
- `1`: Error (invalid JSON, exception)

### Archive Files

**Input** (stdin JSON):
```json
{
  "tool_name": "Write|Edit|MultiEdit",
  "tool_input": {
    "file_path": "/absolute/path/to/file.md"
  }
}
```

**Phase Argument** (argv[1]):
- `pre`: Archive before write
- `post`: Archive after write

**Exit Codes**:
- `0`: Success (archived or skipped)
- `1`: Error (invalid JSON, exception)

### Stats Utility

**Commands**:
- `python3 gsd-stats.py` - All-time stats
- `python3 gsd-stats.py today` - Today's stats
- `python3 gsd-stats.py diff [project]` - Diff archives
- `python3 gsd-stats.py list [project]` - List archives

**Exit Codes**:
- `0`: Success
- `1`: Error

## Changelog

### v1.0.0 (2026-03-08)

**Initial Release**

- ✅ Complexity classifier with TRIVIAL/STANDARD/COMPLEX levels
- ✅ Archive system with pre/post snapshots
- ✅ Stats utility for audit and cost tracking
- ✅ Enhanced statusline with complexity indicators
- ✅ Comprehensive configuration system
- ✅ Full test suite
- ✅ Complete documentation

## Contributing

This is an integration of Sonnet-Gateway v3 concepts into the GSD framework.

**Original Sonnet-Gateway**: See `/sonnet-gateway/` directory for baseline implementation

**GSD Framework**: See main GSD documentation for core workflow concepts

### Reporting Issues

1. Check existing issues
2. Provide reproduction steps
3. Include relevant logs:
   - Classification logs: `~/.claude/logs/gsd-complexity-classifier/`
   - Archive contents: `.claude/archive/`
   - Stats output: `gsd-stats today`

### Submitting Improvements

1. Test changes with test suite
2. Update documentation
3. Add tests for new features
4. Follow existing code style

## License

MIT License - Same as Get Shit Done (GSD) framework

## Credits

- **GSD Framework**: Core workflow orchestration system
- **Sonnet-Gateway v3**: Baseline complexity classification approach
- **Integration**: Combines best of both systems for optimal AI-assisted development

## References

- [GSD Documentation](../README.md)
- [Sonnet-Gateway Hybrid Approach](../sonnet-gateway/gsd-sonnet-gateway-hybrid.md)
- [Sonnet-Gateway vs Best Practices](../sonnet-gateway/comparison-sonnet-gate-vs-best-practices.md)

---

**Get Shit Done with Sonnet-Gateway**: Smart complexity detection + Intelligent cost optimization + Powerful GSD orchestration = Maximum productivity at minimum cost.
