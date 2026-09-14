# FlowForge — Autonomous Production Resilience & Optimization
## Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Prototype / Hackathon Build  
**Target Build Window:** 1 working day  
**Product:** FlowForge-AI  
**Repository:** https://github.com/ershehzan/FlowForge-AI

---

## 1. Product Overview

### 1.1 Product Name

**FlowForge — Autonomous Production Resilience & Optimization**

### 1.2 Product Vision

> **“When the factory changes, the schedule changes with it.”**

FlowForge evolves the existing intelligent shop-floor scheduling system into an autonomous production resilience system.

The prototype will retain the existing scheduling, Genetic Algorithm (GA), machine simulation, failure handling, API, history, and Gantt visualization foundations. The primary change is to make **real-time disruption handling and automatic recovery** the central product capability.

FlowForge should demonstrate that when production conditions change, the system can:

1. Detect or receive a disruption.
2. Understand its impact on the current production plan.
3. Automatically generate a recovery schedule.
4. Optimize the new schedule across multiple objectives.
5. Quantify the improvement.
6. Explain the important scheduling decisions to the user.

This is a simulated factory environment; no physical IoT infrastructure is required.

---

# 2. Problem Statement

Traditional production scheduling assumes that the factory state remains relatively stable after a schedule is generated.

In reality, production environments experience:

- Machine failures
- Machine recovery
- Urgent orders
- Job cancellations
- Deadline changes
- Planned or unplanned machine downtime
- Cascading capacity constraints

A schedule that was optimal before a disruption can quickly become infeasible or inefficient.

FlowForge addresses this problem by treating the production schedule as a **continuously recoverable plan**, rather than a static output.

---

# 3. Product Goals

## Primary Goals

### G1 — Autonomous disruption response
When the factory state changes, FlowForge automatically recalculates the production schedule.

### G2 — Multi-objective optimization
The optimizer should consider more than makespan.

The prototype should minimize:

- Makespan
- Tardiness
- Machine downtime / idle capacity
- Energy consumption

### G3 — Demonstrable resilience
The dashboard must clearly show how the factory moves from:

**Original Plan → Disruption → Degraded State → FlowForge Recovery**

### G4 — Explainable optimization
The optimization engine makes scheduling decisions. An AI explanation layer explains those decisions in human-readable language.

### G5 — Interactive simulation
A judge should be able to trigger factory disruptions using simple scenario controls and immediately see the resulting recovery.

---

# 4. Non-Goals

The one-day prototype must explicitly avoid unnecessary complexity.

The following are out of scope:

- Real IoT hardware
- Physical factory sensors
- Complex digital twins
- Reinforcement learning
- Computer vision
- Real industrial APIs
- Authentication / user management
- Large-scale distributed infrastructure
- Massive production datasets
- Complex cloud deployment
- Production-grade industrial integrations

Use deterministic or generated simulated factory data.

---

# 5. Target Users

## Primary User — Production Planner

Needs to:

- Understand current factory capacity.
- See the production schedule.
- Respond to disruptions.
- Protect deadlines.
- Balance speed and energy consumption.
- Understand why jobs were reassigned.

## Secondary User — Operations Manager

Needs to:

- Assess factory health.
- Understand disruption impact.
- Compare recovery strategies.
- Evaluate resilience and production performance.

## Demo User — Hackathon Judge

Needs to understand the value of FlowForge within seconds.

The interface must therefore make the following visually obvious:

> **What happened?**
>
> **What was affected?**
>
> **What did FlowForge change?**
>
> **Did the recovery improve the situation?**
>
> **Why did FlowForge make those decisions?**

---

# 6. Core Product Concept

The existing scheduler becomes part of a larger autonomous resilience loop:

```text
                    FACTORY DATA
                         │
                         ▼
                 ┌───────────────┐
                 │ Factory State │
                 └───────┬───────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Disruption Engine│
                └────────┬─────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    Machine Failure  Urgent Order  Deadline Change
          │              │              │
          └──────────────┼──────────────┘
                         ▼
              ┌─────────────────────┐
              │ Multi-Objective GA  │
              │                     │
              │ Time + Deadline +   │
              │ Energy + Capacity   │
              └──────────┬──────────┘
                         ▼
                   NEW SCHEDULE
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Resilience Score       AI Explanation
              │                     │
              └──────────┬──────────┘
                         ▼
                  VISUAL DASHBOARD
```

---

# 7. Existing System to Preserve

The implementation must build on the current FlowForge architecture rather than rewrite it.

Existing capabilities to preserve where practical:

- Genetic Algorithm scheduling
- Scheduling / optimization foundation
- Machine simulation
- Machine failure foundation
- Supervisor / orchestration
- Gantt visualization
- API layer
- Schedule history

The modification should be incremental and modular.

---

# 8. Functional Requirements

## FR-1 — Factory State

FlowForge shall maintain a simulated factory state containing at minimum:

### Machines

Each machine should have:

- Machine ID
- Availability status
- Processing capability
- Current utilization
- Energy consumption rate
- Available capacity

Example:

```json
{
  "id": "M3",
  "status": "available",
  "energy_kwh_per_hour": 8.5,
  "utilization": 0.72
}
```

### Jobs

Each job should contain:

- Job ID
- Processing requirements
- Eligible machines
- Processing duration
- Priority
- Deadline
- Current assignment
- Status

---

# 9. Disruption Engine

## FR-2 — Central Disruption Engine

Create a central component responsible for receiving simulated factory disruptions.

Supported disruption types:

1. Machine failure
2. Machine recovery
3. Urgent job arrival
4. Job cancellation
5. Deadline change
6. Machine downtime

The Disruption Engine should:

1. Receive a disruption.
2. Update factory state.
3. Identify affected jobs.
4. Calculate disruption impact.
5. Trigger re-optimization.
6. Produce a recovery schedule.
7. Compare the new state against the original plan.
8. Send results to the dashboard.

---

# 10. Automatic Rescheduling

## FR-3 — Recovery Scheduling

Whenever a disruption changes the factory state, FlowForge shall automatically invoke the existing scheduler / GA with the updated constraints.

The system should not require the user to manually rebuild the schedule.

### Example

```text
M3 FAILED
      ↓
Identify jobs assigned to M3
      ↓
Find feasible alternative machines
      ↓
Run multi-objective optimization
      ↓
Generate recovery schedule
      ↓
Calculate impact
      ↓
Update dashboard
```

---

# 11. Multi-Objective Genetic Algorithm

## FR-4 — Optimization Objectives

The existing GA primarily optimizes makespan.

Upgrade the fitness function to incorporate multiple objectives:

### Minimize

- Makespan
- Total tardiness
- Machine idle / downtime impact
- Energy consumption

A normalized weighted objective can be used for the prototype:

```text
Fitness =
    w1 * normalized_makespan
  + w2 * normalized_tardiness
  + w3 * normalized_downtime
  + w4 * normalized_energy
```

Where:

```text
w1 + w2 + w3 + w4 = 1
```

The exact weights should be configurable.

### Recommended prototype defaults

```text
Makespan:       0.30
Tardiness:      0.35
Downtime:       0.15
Energy:         0.20
```

The implementation should allow these weights to be adjusted without rewriting the optimizer.

---

# 12. Energy-Aware Scheduling

## FR-5 — Machine Energy Model

Each simulated machine should have an approximate energy consumption rate:

```text
Energy = Operating Hours × Machine kWh/hour
```

This does not need to represent real industrial measurements.

It is a simulated optimization variable.

### Example

Machine:

```text
M3 = 12 kWh/hour
M5 = 7 kWh/hour
```

If both machines can process a job, FlowForge can consider the energy trade-off.

---

# 13. Speed vs Energy Trade-Off

The dashboard should be able to compare alternative schedules.

Example:

```text
Schedule A
Makespan:        420 min
Energy:          1,250 kWh
Late Jobs:       2

Schedule B
Makespan:        445 min
Energy:            980 kWh
Late Jobs:         0
```

FlowForge should select or recommend the schedule according to the configured objective weights.

The UI should make the trade-off understandable rather than presenting energy as a decorative metric.

---

# 14. What Changed Panel

## FR-6 — Disruption Impact Panel

Every disruption must generate a concise impact summary.

Example:

```text
🔴 M3 FAILED

Affected:
• 4 jobs
• 2 deadlines

Expected impact:
• +95 minutes delay

FlowForge:
✓ Recovery schedule generated
✓ 4 jobs reassigned
✓ Deadline risk reduced
```

The panel should appear immediately after a disruption.

---

# 15. Before vs After Comparison

## FR-7 — Schedule Comparison

This is a mandatory demo feature.

The dashboard must compare:

```text
ORIGINAL PLAN
      ↓
MACHINE FAILURE
      ↓
NAIVE / UNCHANGED PLAN
      ↓
FLOWFORGE RECOVERY
```

Compare at least:

| Metric | Original | Disrupted | FlowForge |
|---|---:|---:|---:|
| Makespan | | | |
| Late Jobs | | | |
| Machine Utilization | | | |
| Energy Consumption | | | |
| Recovery Time | — | — | |

The exact metric values should be calculated from the simulated schedule rather than hard-coded.

---

# 16. Interactive Gantt Chart

## FR-8 — Schedule Visualization

The existing Gantt visualization should become the central visual representation of production.

It should show:

- Machines on the Y-axis
- Time on the X-axis
- Jobs as schedule blocks
- Job IDs
- Current assignments
- Changed / reassigned jobs
- Machine availability / failure state where practical

After a disruption, the Gantt chart should update to display the recovery schedule.

### Demo expectation

The judge should visually see jobs move from one machine to another after a failure.

---

# 17. Factory Resilience Score

## FR-9 — Resilience Score

Create a simple **Factory Resilience Score** between 0 and 100.

Example:

```text
FACTORY RESILIENCE
       87 / 100
```

The score should consider:

- Deadline protection
- Machine utilization
- Recovery performance
- Remaining capacity
- Disruption impact

A simple weighted model is acceptable.

Example:

```text
Resilience =
    0.30 * deadline_protection
  + 0.20 * utilization
  + 0.25 * recovery_performance
  + 0.15 * remaining_capacity
  + 0.10 * disruption_impact
```

All components should be normalized to 0–100.

### Example demo flow

```text
Normal factory:
87 / 100

M3 failure:
54 / 100

After FlowForge recovery:
81 / 100
```

The score should communicate resilience, not merely overall schedule quality.

---

# 18. Cascading Disruption Simulation

## FR-10 — Cascading Failure Scenario

The system should support at least one cascading scenario if time permits.

Example:

```text
M3 fails
   ↓
Jobs move to M4
   ↓
M4 becomes overloaded
   ↓
Deadline risk increases
   ↓
FlowForge detects the secondary constraint
   ↓
Jobs are redistributed
   ↓
Recovery schedule generated
```

This is intended to demonstrate that FlowForge evaluates system-level effects rather than simply replacing a failed machine.

For the one-day build, this can be implemented as a controlled scenario rather than a generalized industrial simulation.

---

# 19. AI Explanation Layer

## FR-11 — Explain Scheduling Decisions

The LLM must NOT determine the schedule.

The optimization engine remains the source of truth.

The AI layer receives structured optimization results and generates a human-readable explanation.

### Example

```text
Why was Job J7 moved from M3 to M5?

M3 became unavailable.
M5 had sufficient capacity.

Moving J7 to M5 prevents a 42-minute
deadline violation while increasing
energy consumption by approximately 3%.
```

### AI responsibilities

The AI may explain:

- Why a job was moved.
- Why a machine was selected.
- Why a deadline was prioritized.
- Why a more energy-efficient option was rejected.
- What changed after a disruption.
- What the main recovery trade-off was.

### AI must NOT

- Modify the schedule.
- Override GA results.
- Invent metrics.
- Claim decisions that are not present in structured optimizer output.

If the LLM/API is unavailable, the prototype should fall back to deterministic template-based explanations.

---

# 20. Scenario Simulator

## FR-12 — Interactive Disruption Controls

The dashboard shall provide simulation controls.

Required buttons:

```text
SIMULATE

🔴 Machine Failure
⚡ Urgent Order
⏰ Deadline Change
❌ Job Cancellation
🔥 Multiple Failures
```

When the user selects a scenario:

1. Apply disruption.
2. Update factory state.
3. Show impact.
4. Run recovery optimization.
5. Update Gantt.
6. Update metrics.
7. Update resilience score.
8. Generate explanation.

The UI should provide visible feedback that the system is processing the disruption.

---

# 21. Dashboard Requirements

The dashboard should be professional but intentionally simple.

## Recommended Layout

```text
┌─────────────────────────────────────────────────────┐
│ FLOWFORGE                                           │
│ Autonomous Production Resilience & Optimization    │
├─────────────────────────────────────────────────────┤
│ Factory Resilience │ Active Machines │ Late Jobs    │
│ 87 / 100           │ 5 / 6          │ 2            │
├─────────────────────────────────────────────────────┤
│                                                     │
│              INTERACTIVE GANTT                     │
│                                                     │
├──────────────────────┬──────────────────────────────┤
│ WHAT CHANGED?        │ BEFORE vs AFTER              │
│                      │                              │
│ M3 FAILED            │ Makespan                    │
│ 4 affected jobs      │ Tardiness                   │
│ 2 deadline risks     │ Energy                      │
│                      │ Utilization                 │
├──────────────────────┴──────────────────────────────┤
│ AI EXPLANATION                                      │
│ Why did FlowForge make these changes?               │
├─────────────────────────────────────────────────────┤
│ SIMULATE                                            │
│ [Machine Failure] [Urgent Order] [Deadline Change] │
│ [Cancellation] [Multiple Failures]                 │
└─────────────────────────────────────────────────────┘
```

---

# 22. UX Principles

The prototype should prioritize:

### Immediate comprehension
A judge should understand the product without reading documentation.

### Cause → effect
Every disruption should visibly cause a schedule change.

### Evidence over claims
Show metric changes rather than simply saying the system is better.

### Explainability
Make important scheduling decisions understandable.

### Demo speed
A scenario should execute quickly enough for a live hackathon demonstration.

### Visual hierarchy
The most important elements are:

1. Current factory state
2. Disruption
3. Recovery schedule
4. Before/after improvement
5. Resilience score
6. AI explanation

---

# 23. API / Backend Requirements

The existing API layer should be extended rather than replaced.

Suggested conceptual endpoints:

```text
GET  /factory/state
GET  /schedule
POST /disruptions
POST /schedule/recover
GET  /schedule/history
GET  /metrics
GET  /resilience
POST /explain
```

The exact route names should follow the existing project conventions.

### Disruption request example

```json
{
  "type": "machine_failure",
  "machine_id": "M3"
}
```

### Recovery response example

```json
{
  "disruption": {
    "type": "machine_failure",
    "machine_id": "M3"
  },
  "affected_jobs": ["J2", "J7", "J9", "J11"],
  "original_schedule": {},
  "recovery_schedule": {},
  "metrics": {
    "makespan": 445,
    "late_jobs": 0,
    "energy_kwh": 980
  },
  "resilience_score": 81
}
```

The actual schema should be adapted to the existing codebase.

---

# 24. Data Requirements

Use simulated factory data.

## Suggested factory

```text
Machines:
M1, M2, M3, M4, M5, M6

Jobs:
J1 ... J12
```

Each job should have:

- Processing time
- Eligible machines
- Deadline
- Priority
- Current assignment

Each machine should have:

- Processing capability
- Energy rate
- Availability
- Capacity
- Current status

The dataset should be small enough to optimize quickly while still producing visible scheduling conflicts.

---

# 25. State Management

FlowForge should maintain at least three schedule states:

```text
BASELINE
DISRUPTED
RECOVERY
```

### Baseline
The schedule before the disruption.

### Disrupted
The state if the original schedule were left unchanged after the disruption.

### Recovery
The optimized schedule generated by FlowForge.

This separation is essential for before/after evaluation.

---

# 26. Metrics

The system should calculate metrics programmatically.

## Makespan

Total time until the last scheduled job completes.

## Tardiness

For each job:

```text
tardiness = max(0, completion_time - deadline)
```

Total tardiness:

```text
Σ job_tardiness
```

## Late Jobs

Number of jobs where:

```text
completion_time > deadline
```

## Machine Utilization

Approximate:

```text
busy_time / available_time
```

## Energy

Approximate:

```text
Σ(machine operating_hours × machine_kwh_per_hour)
```

## Recovery Time

Time taken from disruption event to generation of a valid recovery schedule.

For the prototype, this can be measured computationally.

---

# 27. Failure Handling

The system should handle invalid disruption scenarios gracefully.

Examples:

- Unknown machine ID
- Unknown job ID
- No feasible machine for a job
- All eligible machines unavailable
- Invalid deadline
- Duplicate cancellation
- Failure of an already failed machine

The UI should show a clear error rather than crashing.

---

# 28. Performance Requirements

The prototype should prioritize fast interactive response.

### Target

For the default demo dataset:

- Disruption processing: near real-time
- Recovery optimization: preferably under a few seconds
- Dashboard update: immediate after optimizer response

GA parameters should be tuned for demo speed rather than industrial-scale optimization.

---

# 29. Reliability Requirements

The prototype must:

- Preserve the baseline schedule.
- Avoid corrupting factory state after failed simulations.
- Allow repeated simulations from a clean baseline.
- Keep disruption history.
- Return valid schedules whenever a feasible solution exists.
- Avoid crashing when an invalid scenario is selected.

A **Reset Factory** control is recommended.

---

# 30. Demo Scenarios

## Scenario A — Machine Failure

```text
Initial:
Resilience = 87

Action:
M3 FAILED

Impact:
4 affected jobs
2 deadline risks

FlowForge:
Reassigns jobs
Runs GA
Generates recovery schedule

Result:
Resilience = 81
Late jobs reduced
```

This should be the primary demo.

---

## Scenario B — Urgent Order

```text
Initial schedule
       ↓
URGENT JOB J13 ARRIVES
       ↓
FlowForge evaluates available capacity
       ↓
Existing jobs may be shifted
       ↓
New schedule generated
```

---

## Scenario C — Deadline Change

```text
J7 deadline moved earlier
       ↓
Deadline risk detected
       ↓
GA reprioritizes schedule
       ↓
Recovery plan generated
```

---

## Scenario D — Job Cancellation

```text
J5 CANCELLED
       ↓
Capacity released
       ↓
Remaining jobs re-optimized
       ↓
Energy / makespan may improve
```

---

## Scenario E — Multiple Failures

Optional stretch scenario:

```text
M3 FAILED
+
M5 FAILED
       ↓
Capacity collapse
       ↓
Cascading constraints
       ↓
FlowForge recovery
```

---

# 31. Priority / Scope for One-Day Development

## MUST HAVE

These features define the winning prototype:

1. Disruption simulation
2. Automatic rescheduling
3. Before/after metrics
4. Multi-objective optimization
5. Interactive Gantt
6. Professional dashboard

## SHOULD HAVE

7. Energy optimization
8. Factory resilience score
9. AI explanation layer

## ONLY IF TIME REMAINS

10. Multiple simultaneous failures
11. More disruption types
12. Advanced visualizations
13. More sophisticated cascading disruption logic

The implementation should stop adding features once the MUST HAVE flow is stable and demo-ready.

---

# 32. Recommended One-Day Implementation Plan

## Phase 1 — Understand Existing Codebase

**Time: ~1 hour**

- Run the existing project.
- Identify scheduler / GA modules.
- Identify machine model.
- Identify failure handling.
- Identify API entry points.
- Identify Gantt component.
- Identify history/state storage.

**Deliverable:** working baseline.

---

## Phase 2 — Multi-Objective Fitness

**Time: ~1.5 hours**

- Extend machine data with energy rate.
- Add tardiness calculation.
- Add energy calculation.
- Add utilization/downtime metric.
- Update GA fitness function.
- Keep objective weights configurable.
- Verify that existing scheduling still works.

**Deliverable:** multi-objective scheduler.

---

## Phase 3 — Disruption Engine

**Time: ~1.5 hours**

Implement a central disruption interface.

Start with:

```text
Machine Failure
```

Then add:

```text
Urgent Order
Deadline Change
Job Cancellation
Machine Recovery
```

Each event must update factory state and trigger recovery scheduling.

**Deliverable:** automatic recovery pipeline.

---

## Phase 4 — Before / After Metrics

**Time: ~45 minutes**

Capture:

```text
Baseline
Disrupted
Recovery
```

Calculate:

- Makespan
- Late jobs
- Tardiness
- Utilization
- Energy
- Recovery time

**Deliverable:** measurable improvement.

---

## Phase 5 — Dashboard

**Time: ~1.5 hours**

Build the primary visual flow:

```text
Factory Status
       ↓
Gantt
       ↓
What Changed
       ↓
Before vs After
       ↓
Resilience Score
       ↓
Simulation Controls
```

Prioritize clarity over decorative UI.

**Deliverable:** judge-ready dashboard.

---

## Phase 6 — AI Explanation

**Time: ~30–45 minutes**

Generate structured decision explanations from optimizer output.

Example input:

```json
{
  "job": "J7",
  "old_machine": "M3",
  "new_machine": "M5",
  "reason": "M3 unavailable",
  "deadline_saved_minutes": 42,
  "energy_change_percent": 3
}
```

Convert this into a natural-language explanation.

Add deterministic fallback if the LLM call fails.

**Deliverable:** explainable scheduling.

---

## Phase 7 — Polish + Demo

**Time: ~30–45 minutes**

- Add Reset Factory.
- Fix visual inconsistencies.
- Verify all buttons.
- Test primary failure scenario.
- Remove unnecessary UI.
- Confirm metrics are real.
- Prepare a 60–90 second demo flow.

**Deliverable:** stable hackathon prototype.

---

# 33. Primary Demo Flow

The entire product should be demonstrated using one clear narrative.

### Step 1 — Show normal factory

```text
FACTORY RESILIENCE: 87/100

6 Machines
12 Jobs
2 Potential Deadline Risks
```

Show the baseline Gantt.

### Step 2 — Trigger failure

Click:

```text
🔴 Machine Failure
```

Select:

```text
M3
```

### Step 3 — Show impact

Immediately display:

```text
M3 FAILED

4 jobs affected
2 deadline risks
95 min expected delay
```

### Step 4 — Show recovery

FlowForge automatically runs the optimizer.

Display:

```text
Generating recovery schedule...
```

Then update the Gantt.

### Step 5 — Prove improvement

Show:

```text
                 Before       After
Makespan          520 min      445 min
Late Jobs              4           0
Energy              1120        980 kWh
Resilience             54          81
```

Actual numbers must be generated from the simulation.

### Step 6 — Explain

Show:

> “J7 was moved from M3 to M5 because M3 became unavailable. M5 had enough capacity to protect the deadline with a small energy increase.”

### Step 7 — End with the product message

> **“When the factory changes, the schedule changes with it.”**

---

# 34. Acceptance Criteria

The prototype is considered successful when all of the following are true.

### AC-1
A machine failure can be triggered from the UI.

### AC-2
The failure updates factory state.

### AC-3
Affected jobs are identified automatically.

### AC-4
The existing GA generates a new feasible schedule.

### AC-5
The GA considers makespan, tardiness, downtime/capacity, and energy.

### AC-6
The Gantt chart visibly changes after recovery.

### AC-7
Before/after metrics are calculated from actual schedules.

### AC-8
The dashboard clearly shows what changed.

### AC-9
A resilience score changes based on disruption and recovery.

### AC-10
At least one scheduling decision can be explained by the AI layer.

### AC-11
The system can demonstrate at least one complete disruption → recovery flow without crashing.

### AC-12
The primary demo can be completed quickly enough for a live hackathon presentation.

---

# 35. Technical Design Principles

## Principle 1 — Optimization is the source of truth

The GA determines the schedule.

The LLM only explains it.

## Principle 2 — Simulation over infrastructure

Simulated factory data is sufficient for the prototype.

## Principle 3 — Reuse existing architecture

Do not rewrite working scheduling components unnecessarily.

## Principle 4 — Quantify everything

Every important claim should have a metric.

## Principle 5 — Demo-first engineering

A smaller reliable system is preferable to a larger unfinished system.

## Principle 6 — Modular disruption handling

Disruption types should share a common interface so new scenarios can be added easily.

---

# 36. Suggested Component Structure

Conceptually:

```text
flowforge/
│
├── scheduler/
│   ├── genetic_algorithm
│   ├── fitness
│   └── constraints
│
├── factory/
│   ├── machine
│   ├── job
│   └── state
│
├── disruption/
│   ├── engine
│   ├── machine_failure
│   ├── machine_recovery
│   ├── urgent_order
│   ├── deadline_change
│   └── job_cancellation
│
├── resilience/
│   ├── metrics
│   └── score
│
├── explanation/
│   ├── decision_builder
│   └── llm_explainer
│
├── api/
│
├── dashboard/
│   ├── gantt
│   ├── metrics
│   ├── disruption_panel
│   ├── comparison
│   └── simulator
│
└── data/
    └── simulated_factory
```

This is conceptual; existing repository structure should take precedence.

---

# 37. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| GA becomes too slow | Use a small dataset and tune population/generations |
| New fitness breaks existing scheduling | Add metrics incrementally and keep constraints explicit |
| No feasible recovery schedule | Detect infeasibility and display a clear factory-capacity warning |
| LLM response is slow | Use deterministic fallback explanations |
| Dashboard takes too long | Reuse existing Gantt/API components |
| Metrics look artificial | Calculate them directly from schedule state |
| Cascading logic becomes complex | Use one controlled cascading scenario |
| Scope expands beyond one day | Enforce MUST / SHOULD / STRETCH priority |

---

# 38. Definition of Done

FlowForge is ready for hackathon demonstration when:

- The existing system still runs.
- A disruption can be triggered from the dashboard.
- Factory state changes correctly.
- FlowForge automatically generates a recovery schedule.
- Multi-objective metrics influence scheduling.
- Energy is represented realistically enough for simulation.
- Gantt visualization updates.
- Before/after metrics are visible.
- Resilience score changes.
- At least one AI explanation is generated.
- The complete machine-failure demo works reliably.
- The UI communicates the concept without requiring technical explanation.

---

# 39. Final Product Positioning

FlowForge should **not** be presented as merely another production scheduling algorithm.

The product should be positioned as:

> **An autonomous production resilience and optimization system that continuously adapts factory schedules when disruptions occur.**

The core differentiator is the closed loop:

```text
DISRUPTION
    ↓
UNDERSTAND IMPACT
    ↓
OPTIMIZE RECOVERY
    ↓
MEASURE RESULT
    ↓
EXPLAIN DECISION
    ↓
UPDATED FACTORY PLAN
```

The central hackathon message is:

> **FlowForge doesn't just create a schedule. It keeps the factory running when reality changes.**
