# So sánh: Sonnet-Gate v3 vs Claude Code Best Practices

## Executive Summary

**Sonnet-Gate v3** và **claude-code-best-practice** giải quyết hai vấn đề khác nhau:
- **Sonnet-Gate**: Cost optimization + complexity-aware advisory system
- **Best Practices**: Workflow orchestration + productivity patterns

**Kết luận**: Hai hệ thống **bổ sung cho nhau**, không thay thế. Có thể tích hợp để tạo hybrid system.

---

## 1. Architecture Comparison Matrix

| Aspect | Sonnet-Gate v3 | Claude Code Best Practices |
|--------|----------------|---------------------------|
| **Primary Goal** | Cost control via complexity classification | Productivity via structured workflows |
| **Trigger Mechanism** | `UserPromptSubmit` hook (automatic) | Commands (`/command-name`) + agents |
| **Routing Unit** | Per-prompt classification | Per-phase/per-workflow |
| **Execution Control** | Advisory (recommends model switch) | Orchestration (enforces workflow steps) |
| **Model Control** | User manual switch after advisory | User selects via `/model` + profile |
| **Key Components** | Hook → classifier → statusline → stats | Command → agent → skill |
| **Artifacts** | `classifications-*.jsonl`, archives | `.planning/*`, `CLAUDE.md`, checkpoints |
| **Observability** | Real-time (🟢🟡🔴) + cost estimates | Phase tracking + git commits |
| **Failure Handling** | Stats review + manual intervention | `/rewind` checkpoints + verify loops |

---

## 2. Detailed Component Analysis

### 2.1 Sonnet-Gate v3 Components

**File Structure:**
```
~/.claude/
├── hooks/
│   ├── complexity-classifier.py       # Core classification logic
│   ├── complexity-config.json         # Patterns + thresholds
│   ├── archive-generated-files.py     # Pre/post file tracking
│   └── stats.py                       # Audit + analytics
├── logs/complexity-classifier/
│   └── classifications-*.jsonl        # Session logs
├── statusline-newapi.sh               # Real-time display
└── settings.json                      # Hook registration
```

**Data Flow:**
```
User prompt → UserPromptSubmit hook
           → complexity-classifier.py
           → classify() → TRIVIAL/STANDARD/COMPLEX
           → additionalContext injected
           → log to JSONL
           → statusline reads log
           → display 🟢🟡🔴 + cost estimate
```

**Key Functions:**
- `classify(prompt)` - Pattern matching + word count heuristics
- `build_context()` - Git status, file changes, session metadata
- `log_entry()` - JSONL append with timestamp + session_id
- `get_complexity_level()` (statusline) - Read latest classification

**Strengths:**
- ✅ Automatic, zero-friction classification
- ✅ Real-time cost visibility
- ✅ Audit trail for all sessions
- ✅ Configurable patterns (JSON)
- ✅ Archive system for file tracking

**Limitations:**
- ❌ Advisory only (no enforcement)
- ❌ No workflow orchestration
- ❌ No multi-phase planning
- ❌ No automatic model switching

---

### 2.2 Claude Code Best Practices Components

**File Structure:**
```
.claude/
├── commands/          # Entry points (/weather-orchestrator)
├── agents/            # Specialized contexts (weather-agent)
├── skills/            # Reusable workflows (weather-svg-creator)
├── rules/             # Organized instructions
└── settings.json      # Permissions + model config

CLAUDE.md              # Project memory (<200 lines)
.planning/             # GSD-style artifacts
```

**Data Flow:**
```
User: /command-name
    → Command loads agent
    → Agent loads skills progressively
    → Agent executes with preloaded context
    → Results + checkpoints
```

**Key Patterns:**
1. **Command → Agent → Skill orchestration**
   - Commands: user entry points
   - Agents: specialized contexts with permissions
   - Skills: reusable, independently-invokable

2. **Memory hierarchy**
   - `CLAUDE.md` (project-level, <200 lines)
   - `.claude/rules/*` (split large instructions)
   - `~/.claude/rules/*` (global rules)

3. **Permission wildcards**
   - `Bash(npm run *)` instead of blanket approval
   - `Edit(/docs/**)` for scoped file access

4. **Cross-model workflows**
   - Claude Code + Codex for plan review
   - Multiple models for QA

5. **Checkpointing**
   - `/rewind` for undoing off-track decisions
   - Hourly commits minimum
   - `/compact` at 50% context

**Strengths:**
- ✅ Structured workflow orchestration
- ✅ Progressive disclosure (skills on-demand)
- ✅ Explicit permission management
- ✅ Checkpoint/rewind capability
- ✅ Multi-phase planning support

**Limitations:**
- ❌ No automatic complexity classification
- ❌ No cost estimation
- ❌ No real-time advisory
- ❌ Relies on user discipline (CLAUDE.md adherence)
- ❌ "Why does Claude ignore CLAUDE.md?" remains unsolved

---

## 3. Integration Opportunities

### 3.1 Hybrid Architecture: Sonnet-Gate + Best Practices

**Concept**: Combine automatic classification with structured workflows

```
User prompt → Sonnet-Gate classifier
           → TRIVIAL: direct execution
           → STANDARD: load /opusplan-agent
           → COMPLEX: load /opus-orchestrator command
                   → Multi-phase workflow
                   → Checkpoint gates
                   → Verify loops
```

**Implementation Strategy:**

#### Phase 1: Enhanced Advisory (Current + Best Practices patterns)
```python
# complexity-classifier.py enhancement
def classify(prompt):
    level = determine_complexity(prompt)

    if level == "STANDARD":
        return {
            "additionalContext": """
⚠️ STANDARD complexity detected.
RECOMMENDED: /model opusplan
OR: Use /opusplan-workflow command for structured approach
            """,
            "suggested_command": "/opusplan-workflow"
        }
    elif level == "COMPLEX":
        return {
            "additionalContext": """
🚨 COMPLEX task detected.
RECOMMENDED: /model opus
OR: Use /complex-orchestrator command for multi-phase workflow
            """,
            "suggested_command": "/complex-orchestrator"
        }
```

#### Phase 2: Command Integration
```
.claude/commands/
├── opusplan-workflow.md       # STANDARD complexity workflow
├── complex-orchestrator.md    # COMPLEX multi-phase workflow
└── cost-aware-agent.md        # Agent with cost tracking
```

**Example: `/opusplan-workflow` command**
```markdown
# OpusPlan Workflow

You are in OpusPlan mode (Opus planning + Sonnet execution).

## Workflow:
1. **Plan Phase** (switch to Opus):
   - User runs: /model opus
   - Create detailed plan with verification steps
   - Save to `.planning/PLAN.md`

2. **Execute Phase** (switch to Sonnet):
   - User runs: /model sonnet
   - Follow plan step-by-step
   - Commit after each major step

3. **Verify Phase** (stay Sonnet):
   - Run tests
   - Check against plan
   - Report completion

## Cost Tracking:
- Sonnet-Gate statusline shows real-time cost
- Target: <$0.10 for STANDARD tasks
```

#### Phase 3: Agent with Skills
```
.claude/agents/cost-aware-agent.md
.claude/skills/complexity-check.md
.claude/skills/cost-estimate.md
.claude/skills/archive-checkpoint.md
```

---

### 3.2 Concrete Integration Examples

#### Example 1: STANDARD Task with Workflow
```
User: "implement user authentication with JWT"

Sonnet-Gate: 🟡 STANDARD detected
Statusline: 🟡 Est: $0.08 | Recommended: /opusplan-workflow

User: /opusplan-workflow
Agent loads with:
  - Skill: jwt-implementation
  - Skill: test-generation
  - Checkpoint: after each phase

Workflow:
1. Plan (Opus): architecture + steps
2. Execute (Sonnet): implement + test
3. Verify (Sonnet): run tests + commit
```

#### Example 2: COMPLEX Task with Orchestration
```
User: "migrate from REST to GraphQL across entire codebase"

Sonnet-Gate: 🔴 COMPLEX detected
Statusline: 🔴 Est: $0.50 | Recommended: /complex-orchestrator

User: /complex-orchestrator
Agent loads with:
  - Command: multi-phase-migration
  - Skills: graphql-schema, resolver-generation, test-migration
  - Checkpoints: after each file/module

Workflow:
1. Research (Opus): analyze codebase structure
2. Plan (Opus): phase-wise migration plan
3. Execute Wave 1 (Sonnet): schema + types
4. Verify Wave 1 (Sonnet): tests pass
5. Execute Wave 2 (Sonnet): resolvers
6. Verify Wave 2 (Sonnet): integration tests
7. Final Review (Opus): security + performance
```

---

## 4. Comparison with GSD (get-shit-done)

| Feature | Sonnet-Gate v3 | Best Practices | GSD |
|---------|----------------|----------------|-----|
| **Orchestration** | None | Command-based | Phase-based |
| **Model Control** | Advisory | Manual | Profile-based |
| **Parallelization** | No | Manual (tmux) | Wave-based |
| **Verification** | Stats review | Manual | Automated UAT |
| **Artifacts** | Logs + archives | CLAUDE.md | `.planning/*` |
| **Failure Handling** | Manual | `/rewind` | Debugger agents |
| **Cost Tracking** | Real-time | No | No |
| **Complexity Detection** | Automatic | No | No |

**Key Insight**: GSD is most similar to Best Practices but with stronger enforcement (phase gates, wave execution, automated verification).

---

## 5. Recommendations

### 5.1 Keep Sonnet-Gate v3 Core
**Rationale**: Unique value proposition
- Automatic complexity detection
- Real-time cost visibility
- Zero-friction advisory
- Audit trail

**Action**: No changes needed to core classifier

---

### 5.2 Add Best Practices Patterns
**Rationale**: Enhance workflow structure without losing advisory benefits

**Recommended Additions:**

#### A. Commands for Structured Workflows
```
.claude/commands/
├── opusplan.md           # STANDARD complexity workflow
├── opus-full.md          # COMPLEX multi-phase workflow
└── cost-review.md        # Review session costs
```

#### B. Skills for Reusable Patterns
```
.claude/skills/
├── complexity-aware.md   # Load Sonnet-Gate context
├── cost-estimate.md      # Estimate before execution
└── checkpoint.md         # Save state + commit
```

#### C. Enhanced CLAUDE.md
```markdown
# Project Instructions

## Cost Awareness
- Check statusline 🟢🟡🔴 before starting
- STANDARD (🟡): use /opusplan workflow
- COMPLEX (🔴): use /opus-full workflow

## Workflow Discipline
- Commit after each major step
- Use /compact at 50% context
- Review costs with /cost-review

## Sonnet-Gate Integration
- Classifier runs automatically
- Follow recommendations in additionalContext
- Check ~/.claude/logs/complexity-classifier/ for audit
```

---

### 5.3 Do NOT Replace Sonnet-Gate
**Rationale**: Best Practices doesn't solve cost optimization

**What Best Practices CANNOT do:**
- ❌ Automatic complexity detection
- ❌ Real-time cost estimation
- ❌ Per-prompt advisory
- ❌ Session-level audit trail

**What Sonnet-Gate CANNOT do:**
- ❌ Enforce workflows
- ❌ Multi-phase orchestration
- ❌ Checkpoint management
- ❌ Parallel execution

**Conclusion**: Complementary, not competitive

---

## 6. Implementation Roadmap

### Phase A: Documentation (Week 1)
- [ ] Create `/opusplan` command
- [ ] Create `/opus-full` command
- [ ] Update CLAUDE.md with workflow patterns
- [ ] Document integration in README

### Phase B: Skills (Week 2)
- [ ] Create `complexity-aware.md` skill
- [ ] Create `cost-estimate.md` skill
- [ ] Create `checkpoint.md` skill
- [ ] Test skill loading

### Phase C: Enhanced Classifier (Week 3)
- [ ] Add `suggested_command` to classifier output
- [ ] Update statusline to show command suggestions
- [ ] Test end-to-end workflow

### Phase D: Validation (Week 4)
- [ ] Run 10 STANDARD tasks with `/opusplan`
- [ ] Run 5 COMPLEX tasks with `/opus-full`
- [ ] Compare costs vs baseline
- [ ] Adjust patterns based on results

---

## 7. Key Takeaways

### What Sonnet-Gate v3 Does Well
1. ✅ **Automatic classification** - zero user friction
2. ✅ **Real-time visibility** - statusline integration
3. ✅ **Cost transparency** - estimates + audit trail
4. ✅ **Configurable** - JSON patterns, no code changes

### What Best Practices Adds
1. ✅ **Workflow structure** - commands + agents + skills
2. ✅ **Progressive disclosure** - load context on-demand
3. ✅ **Permission management** - wildcards + scoping
4. ✅ **Checkpoint discipline** - rewind + compact

### Hybrid System Benefits
1. ✅ **Best of both worlds** - automatic + structured
2. ✅ **Gradual adoption** - start with advisory, add workflows
3. ✅ **Flexibility** - user chooses enforcement level
4. ✅ **Maintainability** - separate concerns, clear boundaries

---

## 8. Final Verdict

**Question**: Should we replace Sonnet-Gate with Best Practices?
**Answer**: **NO - Integrate, don't replace**

**Recommended Architecture:**
```
Sonnet-Gate v3 (Foundation)
    ↓
    ├─→ Automatic classification
    ├─→ Real-time cost tracking
    ├─→ Advisory recommendations
    └─→ Audit trail

Best Practices Patterns (Enhancement Layer)
    ↓
    ├─→ Structured workflows (commands)
    ├─→ Reusable patterns (skills)
    ├─→ Checkpoint discipline
    └─→ Permission management

Result: Hybrid System
    ↓
    ├─→ Automatic + Structured
    ├─→ Advisory + Enforcement (opt-in)
    ├─→ Cost-aware + Workflow-driven
    └─→ Flexible + Maintainable
```

**Next Steps:**
1. Keep Sonnet-Gate v3 as-is (proven, working)
2. Add Best Practices patterns incrementally
3. Test hybrid workflows on real tasks
4. Iterate based on usage data

---

## References

- Sonnet-Gate v3: `~/.claude/hooks/complexity-classifier.py`
- Best Practices: https://github.com/shanraisshan/claude-code-best-practice
- GSD: https://github.com/gsd-build/get-shit-done
- MCP Analysis: `~/.claude/hooks/MCP-MODEL-CONTROL-ANALYSIS.md`
