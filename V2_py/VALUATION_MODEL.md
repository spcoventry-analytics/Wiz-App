# Fantasy Draft Assistant Valuation Model

## Core Principle

The application contains three categories of data:

1. **Static Player Values**
   - Describe player quality.
   - Generated before the draft.
   - Do not change as the draft progresses.

2. **Dynamic Draft Values**
   - Describe current draft conditions.
   - Recalculated after every pick.
   - Reflect scarcity and urgency.

3. **Planning Values**
   - Describe future roster outcomes.
   - Recalculated whenever the board changes.
   - Used to maintain a viable draft plan.

---

# 1. Static Player Values

## Purpose

Answer:

> "How good is this player?"

These values should never change during the draft.

## Variables

```python
PPG
points
floor
ceiling
tier
position_rank
adp
age
draft_year_x
```

## Baselines

```python
tier_baselines
```

These are generated once and represent expected starter quality at each roster slot.

## Used By

### Current Plan

Roster evaluation.

### Hypothetical Roster

Starter assignment.

### Strategy Builder

Round targeting.

---

# 2. Dynamic Draft Values

## Purpose

Answer:

> "What happens if I wait?"

These values should change after every draft pick.

## Variables

```python
best_available
next_round_available
```

### Margin

```python
margin = best_available_ppg - next_round_ppg
```

Meaning:

> Raw PPG loss if I wait.

### Ratio

```python
ratio = margin / best_available_ppg
```

Meaning:

> Percentage value lost.

### Elasticity

```python
elasticity = margin * ratio
```

Meaning:

> Combined urgency measure.

### Urgency

```python
urgency = min(2.0, elasticity * 1.5)
```

Meaning:

> Position priority gauge score.

### Scarcity

```python
adp_aware_drafted
scarcity_ratio
```

Meaning:

> How much of the expected talent pool has already disappeared.

## Used By

### Position Status Bar

```python
Urgency
Elasticity
Margin
Ratio
Scarcity
```

### On-The-Clock Draft Assistant

Future recommendation engine.

### Immediate Position Prioritization

```python
QB vs RB vs WR vs TE
```

---

# 3. Planning Values

## Purpose

Answer:

> "Given the current board, what should my plan be now?"

These values should be rebuilt whenever the draft changes.

## Variables

### Strategy Targets

```python
target_rounds_QB
target_rounds_RB
target_rounds_WR
target_rounds_TE
target_rounds_LB
target_rounds_DL
target_rounds_DB
```

### Planned Picks

```python
plan_picks
```

### Plan Status

```python
ACTIVE
INVALIDATED
```

### Hypothetical Roster

Generated from:

```python
keepers
actual picks
planned picks
```

## Used By

### Build Plan

Round-by-round planning.

### Hypothetical Roster

Future roster evaluation.

### Strategy Adjustment Engine

Future enhancement:

```python
If target drafted:
    invalidate pick
    suggest replacement
    re-evaluate later rounds
```

---

# Tab Ownership

## Position Status Bar

Uses:

```python
Dynamic Draft Values
```

Must update every pick.

---

## Consider Options / Gold Mine

Uses:

```python
Static Player Values
+ Dynamic Draft Values
```

Purpose:

```text
Find quality players while considering current scarcity.
```

Must update every pick.

---

## Current Plan

Uses:

```python
Static Player Values
+ Planning Values
```

Purpose:

```text
Build the best future roster.
```

Must update every pick.

---

## Hypothetical Roster

Uses:

```python
Static Player Values
+ Planning Values
```

Purpose:

```text
Evaluate plan outcome.
```

Should never use elasticity or urgency directly.

---

# Design Rule

Whenever adding a new metric, ask:

### Player Quality?

```python
Static Player Value
```

### Draft Urgency?

```python
Dynamic Draft Value
```

### Future Roster Construction?

```python
Planning Value
```

A metric should belong to **exactly one category**. If a variable appears in multiple categories, its purpose should be documented explicitly.
