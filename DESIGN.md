# FlowForge — DESIGN.md

## 1. Design Direction

### Product
**FlowForge — Autonomous Production Resilience & Optimization**

### Core message
> **When the factory changes, the schedule changes with it.**

The redesigned FlowForge experience should feel like a **production control center**, not a generic analytics dashboard.

The visual story is:

```text
FACTORY STATE
     ↓
DISRUPTION
     ↓
IMPACT
     ↓
AUTONOMOUS RECOVERY
     ↓
NEW OPTIMAL PLAN
     ↓
PROOF + EXPLANATION
```

The design must make that story understandable within seconds.

---

# 2. Design Goals

## Primary goals

1. Make disruptions the central interaction.
2. Make schedule recovery visually obvious.
3. Show measurable improvement before asking the user to trust the algorithm.
4. Make the factory feel alive through changing state.
5. Present optimization results without overwhelming the user.
6. Make AI explanations useful but secondary to the optimizer.
7. Support a fast, polished hackathon demo.

## Design principles

### Clarity over density
Only show information that helps the operator understand the current production state.

### Cause → effect
A disruption should visually connect to affected jobs and the resulting recovery.

### State visibility
The user should always know whether the factory is:

- Healthy
- Disrupted
- Recovering
- Recovered
- At risk

### Evidence over decoration
Metrics should show actual schedule changes.

### Progressive detail
The dashboard gives a high-level overview first, with detailed reasoning available below.

---

# 3. Visual Identity

## Overall style

**Industrial control room + modern AI product**

Avoid:

- Generic SaaS dashboard appearance
- Excessive gradients
- Large decorative illustrations
- Overly colorful charts
- Excessive rounded cards
- AI gimmicks

Prefer:

- Dark control-center interface
- Strong typography
- Clear status indicators
- Compact metric cards
- High-contrast Gantt visualization
- Subtle borders
- Controlled use of status colors
- Motion only where it communicates state change

---

# 4. Color System

Use a dark foundation so production state and disruption colors stand out.

## Base

```text
Background       #0B0F14
Surface          #111820
Elevated Surface #17212B
Border           #26323D
Primary Text     #F5F7FA
Secondary Text   #9BA8B5
Muted Text       #667482
```

## Semantic colors

```text
Healthy / Success    Green
Warning / Risk       Amber
Disruption / Failure Red
Active / Recovery    Blue
Energy               Cyan
```

Use semantic colors primarily for **state**, not decoration.

Example:

```text
M3 FAILED       → Red
Recovery        → Blue
Deadline Risk   → Amber
Recovered       → Green
Energy          → Cyan
```

---

# 5. Typography

Use a clean technical sans-serif.

Recommended:

```text
Inter
```

Optional monospace font for machine IDs, metrics, and technical information:

```text
JetBrains Mono
```

## Hierarchy

### Page title
Large, bold.

```text
FLOWFORGE
```

### Product subtitle

```text
Autonomous Production Resilience & Optimization
```

### Section heading

```text
Production Schedule
```

### Metric

Large numerical value.

```text
81
```

### Supporting label

Small uppercase / muted.

```text
FACTORY RESILIENCE
```

---

# 6. Application Structure

Use a single primary control-center page for the hackathon prototype.

```text
┌──────────────────────────────────────────────────────────────┐
│ FLOWFORGE                              FACTORY ● OPERATIONAL  │
│ Autonomous Production Resilience & Optimization              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ RESILIENCE     ACTIVE MACHINES     LATE JOBS     ENERGY      │
│ 87 / 100       5 / 6               2             980 kWh    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ PRODUCTION SCHEDULE                                          │
│                                                              │
│        08:00    10:00    12:00    14:00    16:00             │
│ M1     █████ J1 ███ J6                                         │
│ M2     ███ J2 █████ J9                                         │
│ M3     ███ J4 ███ J7                                          │
│ M4     █████ J3      ███ J8                                   │
│ M5     ███ J5 █████ J10                                      │
│                                                              │
├───────────────────────────────┬──────────────────────────────┤
│ WHAT CHANGED?                 │ BEFORE vs AFTER              │
│                               │                              │
│ 🔴 M3 FAILED                  │ Makespan       520 → 445    │
│ 4 jobs affected               │ Late Jobs        4 → 0      │
│ 2 deadline risks              │ Energy       1120 → 980     │
│ +95 min expected delay        │ Utilization     71 → 84%    │
│                               │ Resilience      54 → 81      │
├───────────────────────────────┴──────────────────────────────┤
│ FLOWFORGE DECISION                                            │
│                                                              │
│ J7 moved M3 → M5                                              │
│ Deadline protected by 42 min · Energy +3%                    │
├──────────────────────────────────────────────────────────────┤
│ SIMULATE                                                     │
│ [🔴 Machine Failure] [⚡ Urgent Order] [⏰ Deadline Change]    │
│ [❌ Job Cancellation] [🔥 Multiple Failures] [↻ Reset]        │
└──────────────────────────────────────────────────────────────┘
```

---

# 7. Header Design

The header should establish the product immediately.

```text
FLOWFORGE
Autonomous Production Resilience & Optimization
```

Right side:

```text
FACTORY STATUS
● OPERATIONAL
```

When disrupted:

```text
FACTORY STATUS
● DISRUPTED
```

When optimizing:

```text
FACTORY STATUS
◌ RECOVERING
```

When recovered:

```text
FACTORY STATUS
● RECOVERED
```

The status should change dynamically.

---

# 8. Top KPI Strip

Use four or five compact KPI cards.

## Required

### Factory Resilience

```text
87 / 100
```

### Active Machines

```text
5 / 6
```

### Late Jobs

```text
2
```

### Makespan

```text
445 min
```

### Energy

```text
980 kWh
```

Each KPI should include a small comparison indicator when relevant.

Example:

```text
LATE JOBS
0

↓ 4 from disrupted state
```

Avoid unnecessary graphs inside every KPI card.

---

# 9. Resilience Score

The resilience score should be the strongest visual KPI.

## Normal

```text
┌─────────────────────────────┐
│ FACTORY RESILIENCE          │
│                             │
│       87 / 100              │
│                             │
│ █████████████████░░░        │
│                             │
│ HEALTHY                     │
└─────────────────────────────┘
```

## During disruption

```text
54 / 100
AT RISK
```

## After recovery

```text
81 / 100
RECOVERED
```

The score should animate between states.

---

# 10. Production Gantt

The Gantt chart is the **hero visualization**.

## Layout

```text
             TIME
        08  09  10  11  12  13  14  15  16

M1       J1──────J6────
M2          J2──────J9──
M3       J4─── X
M4       J3──────J8────
M5       J5───J10──────
```

## Job blocks

Each job block should show:

```text
J7
M3
```

On hover/click:

```text
Job J7
Machine: M3
Duration: 55 min
Deadline: 14:30
Energy: 7.4 kWh
Status: At Risk
```

---

# 11. Gantt Disruption State

When M3 fails:

```text
M3    J4───  🔴 FAILED
```

Affected jobs should visually indicate that they need reassignment.

Example:

```text
J7
M3 → M5
```

After optimization:

```text
M5       J7────────
```

Use a subtle transition so the user can see the job move.

---

# 12. "What Changed?" Panel

This panel appears prominently after every disruption.

## Default state

```text
NO ACTIVE DISRUPTION

Factory operating normally.
```

## Failure state

```text
🔴 MACHINE FAILURE

M3 is unavailable.

IMPACT
4 jobs affected
2 deadline risks
95 min expected delay

RECOVERY
FlowForge is generating
a new production plan...
```

After recovery:

```text
✓ RECOVERY COMPLETE

4 jobs reassigned
0 late jobs
Deadline risk reduced
```

The panel should focus on **what happened**, not implementation details.

---

# 13. Before vs After Panel

This section provides proof that FlowForge worked.

Use a comparison layout:

```text
                 DISRUPTED       FLOWFORGE
Makespan           520 min         445 min
Late Jobs              4               0
Energy             1120 kWh         980 kWh
Utilization            71%             84%
Resilience             54              81
```

Use arrows where useful:

```text
520 min  → 445 min
4 late   → 0 late
```

The user should not have to calculate improvement mentally.

---

# 14. AI Explanation Panel

Label this clearly so users understand that AI is explaining the optimizer.

```text
FLOWFORGE DECISION
AI-generated explanation
```

Example:

```text
Why was J7 moved from M3 to M5?

M3 became unavailable after the failure.
M5 had sufficient capacity to process J7.

Moving J7 prevents a 42-minute deadline
violation while increasing energy use by
approximately 3%.
```

Include structured facts:

```text
M3 → M5
Deadline protection: +42 min
Energy impact: +3%
```

Do not make the AI panel larger than the Gantt or comparison panel.

---

# 15. Scenario Simulator

The simulator should be visually prominent because it drives the demo.

## Controls

```text
SIMULATE DISRUPTION

[ 🔴 Machine Failure ]
[ ⚡ Urgent Order ]
[ ⏰ Deadline Change ]
[ ❌ Job Cancellation ]
[ 🔥 Multiple Failures ]

[ ↻ Reset Factory ]
```

## Machine failure interaction

Click:

```text
Machine Failure
```

Then display:

```text
SELECT MACHINE

[ M1 ] [ M2 ] [ M3 ]
[ M4 ] [ M5 ] [ M6 ]
```

Selecting M3 immediately launches the disruption flow.

Avoid complex configuration dialogs.

---

# 16. Recovery Animation

The transition should communicate autonomy.

Recommended sequence:

```text
M3 FAILED
     ↓
4 JOBS AFFECTED
     ↓
ANALYZING CAPACITY
     ↓
OPTIMIZING RECOVERY
     ↓
RECOVERY PLAN READY
```

The animation should be short.

Target:

```text
1–3 seconds
```

Do not artificially delay the interface if optimization completes faster.

---

# 17. Factory State Indicator

The application should have four primary states.

## Operational

```text
● OPERATIONAL
```

## Disrupted

```text
● DISRUPTED
```

## Recovering

```text
◌ OPTIMIZING
```

## Recovered

```text
✓ RECOVERED
```

This should be consistent across the header and relevant panels.

---

# 18. Machine Status Design

A compact machine status view can be placed beside or below the Gantt.

```text
M1   ● Running      82%
M2   ● Running      74%
M3   🔴 Failed       0%
M4   ● Running      91%
M5   ● Running      68%
M6   ● Idle         12%
```

Clicking a machine can highlight its jobs in the Gantt.

---

# 19. Energy Visualization

Energy should be treated as an optimization dimension.

A compact indicator:

```text
ENERGY

980 kWh

↓ 12.5%
vs disrupted schedule
```

Optional:

```text
Fastest Plan       420 min | 1250 kWh
FlowForge Plan     445 min |  980 kWh
```

This clearly communicates the trade-off.

---

# 20. Cascading Disruption Visualization

For the stretch scenario, show the chain of impact.

```text
M3 FAILURE
    │
    ▼
4 JOBS DISPLACED
    │
    ▼
M4 CAPACITY ↑
    │
    ▼
DEADLINE RISK ↑
    │
    ▼
FLOWFORGE REBALANCES
    │
    ▼
RECOVERY
```

This can appear as a small event timeline rather than a complicated graph.

---

# 21. Event Timeline

A lightweight history panel can show:

```text
20:14:32   M3 failed
20:14:32   4 jobs affected
20:14:33   Recovery optimization started
20:14:34   4 jobs reassigned
20:14:34   Recovery schedule generated
20:14:35   Resilience: 54 → 81
```

This is useful during the demo because it makes the autonomous workflow visible.

---

# 22. Interaction Design

## Primary interaction

```text
Click disruption
      ↓
Observe factory state change
      ↓
Observe impact
      ↓
Observe optimization
      ↓
Observe Gantt update
      ↓
Observe metrics
      ↓
Read explanation
```

No multi-page navigation should be required.

---

# 23. Responsive Layout

The desktop view is the primary target.

## Desktop

Use:

```text
12-column grid
```

Suggested:

```text
Gantt:             12 columns
What Changed:       5 columns
Before/After:       7 columns
AI Explanation:    12 columns
Simulator:         12 columns
```

## Smaller screens

Stack:

```text
KPIs
↓
Gantt
↓
What Changed
↓
Before/After
↓
AI Explanation
↓
Simulator
```

---

# 24. Component System

Recommended reusable components:

```text
AppShell
Header
FactoryStatus
MetricCard
ResilienceScore
GanttChart
MachineRow
JobBlock
DisruptionPanel
ImpactSummary
ComparisonTable
DecisionExplanation
ScenarioControls
MachineSelector
EventTimeline
StatusBadge
RecoveryIndicator
ResetButton
```

Components should receive data through props/state rather than embedding scenario-specific values.

---

# 25. Component States

Every major component should support at least:

```text
Default
Loading
Success
Warning
Error
Disrupted
Recovered
```

Example for the Disruption Panel:

```text
Default:
No active disruption

Loading:
Analyzing disruption...

Success:
Recovery complete

Error:
No feasible recovery schedule
```

---

# 26. Empty / Error States

## No feasible schedule

```text
⚠ RECOVERY NOT POSSIBLE

Current capacity is insufficient
to meet all active deadlines.

Suggested action:
Review machine availability
or relax deadline constraints.
```

## Invalid disruption

```text
Unable to apply disruption.

Machine M9 does not exist.
```

Errors should be clear and actionable.

---

# 27. Motion Guidelines

Use animation only to communicate state.

Good uses:

- Job moving between machines
- Resilience score changing
- Factory status changing
- Recovery progress
- New disruption event appearing

Avoid:

- Constant particle effects
- Decorative chart animation
- Excessive hover animations
- Long loading screens

---

# 28. Accessibility

Minimum requirements:

- High contrast text.
- Do not rely only on color to communicate status.
- Include labels/icons alongside status colors.
- Buttons must have clear labels.
- Gantt jobs should expose their IDs.
- Keyboard interaction should work for primary controls where practical.

Example:

Bad:

```text
🔴
```

Better:

```text
🔴 FAILED
```

---

# 29. Demo-First Visual Priorities

If development time becomes limited, implement visual features in this order:

## P0

1. Header / factory status
2. KPI strip
3. Interactive Gantt
4. Disruption controls
5. What Changed panel
6. Before vs After metrics

## P1

7. Resilience score
8. AI explanation
9. Machine status list
10. Recovery animation

## P2

11. Event timeline
12. Cascading disruption visualization
13. Advanced energy visualization

---

# 30. Primary Demo Screen

The final demo should look approximately like:

```text
╔══════════════════════════════════════════════════════════════╗
║ FLOWFORGE                          ● FACTORY OPERATIONAL     ║
║ Autonomous Production Resilience & Optimization              ║
╠══════════════════════════════════════════════════════════════╣
║  RESILIENCE     MACHINES       LATE JOBS       ENERGY       ║
║  87 / 100       6 / 6          0               980 kWh      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PRODUCTION SCHEDULE                                         ║
║                                                              ║
║  M1   ███ J1 █████ J6                                        ║
║  M2      ███ J2 █████ J9                                     ║
║  M3   ███ J4 ███ J7                                          ║
║  M4   █████ J3 ███ J8                                        ║
║  M5   ███ J5 █████ J10                                       ║
║  M6      ███ J11                                             ║
║                                                              ║
╠═══════════════════════════╦══════════════════════════════════╣
║ WHAT CHANGED?              ║ BEFORE vs AFTER                  ║
║                           ║                                  ║
║ 🔴 M3 FAILED              ║ Makespan      520 → 445 min     ║
║ 4 jobs affected           ║ Late Jobs       4 → 0           ║
║ 2 deadline risks          ║ Energy      1120 → 980 kWh     ║
║ +95 min expected delay    ║ Resilience      54 → 81        ║
║                           ║                                  ║
║ ✓ RECOVERY COMPLETE       ║                                  ║
╠═══════════════════════════╩══════════════════════════════════╣
║ FLOWFORGE DECISION                                            ║
║                                                              ║
║ J7   M3 → M5                                                 ║
║ Prevents 42-min deadline violation · Energy +3%             ║
╠══════════════════════════════════════════════════════════════╣
║ SIMULATE                                                      ║
║ [🔴 Machine Failure] [⚡ Urgent Order] [⏰ Deadline Change]   ║
║ [❌ Cancellation] [🔥 Multiple Failures]       [↻ Reset]      ║
╚══════════════════════════════════════════════════════════════╝
```

---

# 31. Before / During / After Design States

The dashboard should deliberately change between three visual states.

## STATE 1 — HEALTHY

```text
Status: OPERATIONAL
Resilience: 87
Normal Gantt
No impact panel
Simulator available
```

## STATE 2 — DISRUPTED

```text
Status: DISRUPTED
Resilience: 54
Failed machine highlighted
Affected jobs highlighted
What Changed panel expanded
Recovery indicator active
```

## STATE 3 — RECOVERED

```text
Status: RECOVERED
Resilience: 81
New Gantt
Before/After comparison
AI explanation
Recovery event
```

This state transition is the heart of the design.

---

# 32. Design for the Judge

The first 10 seconds should answer:

### What is this?

> Autonomous production resilience.

### What does it do?

> Automatically adapts the schedule when the factory changes.

### What happened?

> A machine failed.

### What did FlowForge do?

> It generated a new optimized production plan.

### Did it work?

> The metrics improved.

### Why?

> The AI explanation describes the optimization decision.

If the interface communicates these six answers without narration, the design is successful.

---

# 33. Implementation Guidance

The design should be implemented using the existing project architecture.

Do not redesign the backend solely to satisfy the UI.

Recommended data flow:

```text
Factory State
     ↓
Disruption Engine
     ↓
Optimizer
     ↓
Recovery Result
     ↓
Dashboard State
     ├── Gantt
     ├── Impact Panel
     ├── Metrics
     ├── Resilience
     └── AI Explanation
```

The frontend should consume structured data and render state.

---

# 34. Design Definition of Done

The redesign is complete when:

- The factory status is visible at all times.
- The Gantt is the main visual element.
- Disruptions can be triggered directly from the dashboard.
- Failed machines are immediately visible.
- Affected jobs are identifiable.
- Recovery changes are visible on the Gantt.
- Before/after metrics are shown.
- Resilience score changes.
- AI explanations are displayed separately from optimization.
- Reset returns the system to the baseline state.
- The complete machine-failure scenario can be demonstrated without leaving the main page.

---

# 35. Final Design Principle

FlowForge should visually communicate one idea above everything else:

> **The factory is not static. FlowForge continuously adapts the plan to reality.**

The design therefore treats the **disruption → recovery transition** as the primary product experience, with the Gantt, metrics, resilience score, and AI explanation all supporting that story.
