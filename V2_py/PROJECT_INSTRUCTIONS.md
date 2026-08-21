# Project Instructions and Conventions for Wiz-App (Fantasy Football Draft App)

## Project Goal
Build a responsive, web-based fantasy football draft application using Python and Streamlit. The app should function as a live draft board, a player recommendation tool, and a team analysis dashboard. It must be accessible and usable on an iPhone.

## Phase 1: Data Gathering and Preparation

### Data Sources & Libraries
- League Settings (ESPN): Use the espn-api library to connect to my specific ESPN league using my league ID and cookies. This is critical for pulling keepers, draft order, traded picks, non-standard scoring rules, and non-standard position lists.
- Projections: I will provide a CSV file with my custom projections from FFAnalytics.net. The app needs to be able to read and parse this file using pandas.
- ADP (Average Draft Position): Scrape real-time, consensus ADP data from a reliable source like FantasyPros.com or Footballguys.com. Use the requests library to fetch the webpage content and BeautifulSoup to parse the HTML and extract the data.
- Advanced Metrics (General NFL): Use the nfl-data-py library to pull in advanced player stats. Specifically, gather data for:
    - WRs: Career year (e.g., Year 3), Yards After Catch (YAC).
    - RBs: Yards After Contact.
    - All Players: Contract year status (if possible from a reliable source), and depth chart position (especially players behind a starter 31+ years old).
- Historical Data: I have a set of spreadsheets (past_drafts.csv, draft_prep.csv) with my past draft results and notes. Use pandas to read and integrate this data to inform predictive features.

### Data Processing with pandas
- Merge all data sources into a single, comprehensive player dataset (a Pandas DataFrame).
- Clean the data to handle missing values and inconsistent player names across sources.
- Create a consistent, custom Player ID or Player Name to link all data frames together.
- Create calculated columns for key insights, such as APG (Average Points Per Game), Value_Over_Replacement, and Draft_Position_Value.
- Create clear filters and flags for the advanced metrics I want to track (e.g., a is_year_3_wr boolean column).

## Phase 2: Core Application Functionality (Streamlit App)

### Technology Stack
The app will be built using streamlit for the UI, with pandas for all data manipulation. Use sqlite3 for simple, file-based data storage of the draft state to ensure persistence. The st-aggrid package can be used to create a more dynamic and sortable player table.

### Draft Board
- Create a live draft board that displays all teams and their drafted players. This will be dynamically updated by connecting to the ESPN league.
- Position columns on the board should be color-coded for quick visual reference (e.g., QB in blue, RB in green).
- The board must be able to handle non-standard fantasy leagues, including custom position lists, keeper rules, and traded picks, all pulled from the ESPN league settings.
- The app should allow me to manually enter a pick quickly, even if it's not the highest-ranked player. The input should be simple (e.g., pos, team, name).

### My Team Dashboard (Activated on my turn)
- When it is my turn to pick, a dashboard should appear with a clear view of my current roster.
- Projected Starting Lineup: Display my best possible starting lineup based on the players drafted so far.
- Projected Points: For each player in my starting lineup, show their projected Average Points Per Game (APG), adjusted for my league's scoring system.
- Gap Analysis: For any empty starting slots, recommend the top 3-5 available players from the remaining pool.
- Value Recommendations: For each recommended player, display their ADP-based projected APG and their estimated draft round. This will help me identify "value picks" who I might be able to wait on.

### Development Strategy and Scope
- Iteration 1 (MVP - Minimum Viable Product): Focus on building the core draft board, player entry, and the basic "My Team" dashboard. Prioritize getting the data pipelines working for my projections CSV, ADP, and the live ESPN league connection first.
- Iteration 2 (Adding Features): After the core is functional, integrate the advanced metrics (YAC, contract year, etc.) and the historical data insights.
- Final Output: The final code should be a single, well-structured Python script that can be run with streamlit run app.py and is ready for deployment. The design should be responsive and work well on a mobile device.

## Folder Structure
- `V2_py/` : Main Python/Streamlit app code
- `Past_Drafts/` : Store historical draft spreadsheets (e.g., `Projections_2022.csv`, `Projections_2023.csv`)
- `www/` : Static assets (images, logos, etc.)
- `V1_r/` : Legacy Shiny app code (reference only)

## Data Files
- Past draft records: Named as `Projections_[YEAR].csv` (e.g., `Projections_2025.csv`)
- Place all historical and projection CSVs in `Past_Drafts/`

## Secrets & Credentials
- Use Streamlit secrets for sensitive info (ESPN cookies, league ID, etc.)

## Variable Naming
- Use `snake_case` (lowercase, underscores) for raw data variables (e.g., `players_df`)
- Use `Capitalized` names for processed data (e.g., `PlayersCleaned`)
- For intermediate steps, append a suffix (e.g., `players_scrub_df`) and comment at the start of the step to indicate parent/source and purpose

## Error Handling & Debugging
- Use a global boolean variable `DEBUGMODE` to control error messaging and debugging output
- Wrap debug/error print statements in `if DEBUGMODE:` blocks

## Comments & Documentation
- Prefer block comments before code sections rather than inline comments
- Use docstrings for functions/classes

## Mobile Responsiveness & UI
- Default to Streamlit’s built-in mobile features
- If custom CSS is needed, consider Bootstrap or similar frameworks
- Place custom CSS in `www/` if used

## Legacy Code
- `V1_r/` folder contains Shiny app remains; reference for design/ideas only

## General
- Jumping between development and use mode is expected; keep debugging tools easily toggled
- All future agents should reference this file for project conventions

---
_as of update: August 9, 2025_

# Fantasy Draft Assistant Architecture & Valuation Model

## Core Design Philosophy

The application operates across three decision layers:

### 1. Static Player Values

Answer:

> How good is this player?

These values are generated before the draft and should not change because other players have been selected.

Examples:

```python
PPG
points
floor
ceiling
tier
position_rank
adp
age
depth
draft_year
```

these values are found on the draft_results_[league_id]_[YEAR].csv file, and loaded into the session state after configuration is complete. (configuration.py)  

- ghost of christmas past (it is what we thought before the draft started)

---

### 2. Dynamic Draft Values

Answer:

> What happens if I wait?

These values change after every pick and describe the current state of the draft board.

Examples:

```python
margin
ratio
elasticity
urgency
scarcity_ratio
adp_aware_drafted
```

these values are calculated by position_status_bar.py, and stored in the session state after every pick. (enter_pick.py) 

- ghost of Christmas present (it is what is happening right now as we make a decision)

---

### 3. Dynamic Planning Values

Answer:

> Given everything that has happened so far, what should my plan be now?

These values represent the current recommended draft plan and should evolve throughout the draft.

Examples:

```python
target_rounds
plan_picks
draft_plan
target_player
ACTIVE
INVALIDATED
COMPLETED
```
- ghost of Christmas future (it is what we think will happen if we follow the plan, or what will change moving forward) 
- Don't let Tiny Timmy die! Save Christmas, avoid gaps in the roster caused by necessary pivots in the plan, and avoid drafting players that are not needed.

---

# Tab Ownership

## Position Status Bar

### Purpose

Answer:

> Which position becomes most expensive if I wait?

### Uses

Dynamic Draft Values only.

### Key Metrics

```python
margin
ratio
elasticity
urgency
scarcity
```

### Updates

Every pick.

### User Question

> What position is most urgent right now?

### Category

Tactical Decision Support.

---

## Consider Options (Gold Mine)

### Purpose

Answer:

> I am currently on the clock. Which players deserve serious consideration?

### Uses

```text
Static Player Values
+
Dynamic Draft Values
```

### Key Metrics

```python
PPG
points
floor
ceiling
tier
position_rank

margin
ratio
elasticity
urgency
scarcity
```

### Updates

Every pick.

### User Question

> Who should I be considering right now?

### Category

Tactical Decision Support.

### Important Rule

Gold Mine evaluates immediate choices.

Gold Mine does not create draft plans.

---

## Current Plan

### Purpose

Answer:

> Given the current board, what should my draft plan be now?

### Uses

```text
Static Player Values
+
Dynamic Planning Values
```

### Updates

Every pick.

### User Question

> What should my future draft look like from this point forward?

### Category

Strategic Planning.

### Important Rule

Current Plan is intentionally dynamic.

A Round 1 plan is only a starting point.

As the draft evolves:

- players get drafted
- targets become unavailable
- positional needs change
- scarcity changes
- roster gaps appear

The plan should continuously adapt.

### Expected Behavior

If a planned player is drafted:

1. Invalidate the player target.
2. Evaluate replacement candidates.
3. Re-evaluate future rounds.
4. Adjust the remaining plan when appropriate.

Example:

```text
Initial:
R5 WR
R6 RB
R7 TE

After WR Run:
R5 WR
R6 WR
R8 RB
R9 TE
```

The plan adapts.

---

## Hypothetical Roster

### Purpose

Answer:

> If I follow the current plan, what roster will I end up with?

### Uses

```text
Static Player Values
+
Dynamic Planning Values
```

### Inputs

```python
keepers
actual_picks
plan_picks
tier_baselines
```

### Outputs

```python
starting_lineup
bench
lineup_ppg
position_values
```

### Category

Plan Evaluation.

### Important Rule

Hypothetical Roster evaluates plans.

Hypothetical Roster does not generate plans.

---

# Static Player Values

## Rules

- Generated before the draft.
- Represent player quality.
- Do not change during the draft.
- Should not increase simply because better players have been drafted.

## Used By

```text
Current Plan
Hypothetical Roster
Consider Options
```

---

# Dynamic Draft Values

## Margin

```python
margin = best_available_ppg - next_round_available_ppg
```

Raw PPG lost by waiting.

### Marker

```text
📉
```

---

## Ratio

```python
ratio = margin / best_available_ppg
```

Percentage value lost by waiting.

### Marker

```text
📊
```

---

## Elasticity

```python
elasticity = margin * ratio
```

Combined urgency signal.

### Marker

```text
⚡
```

---

## Urgency

```python
urgency = min(2.0, elasticity * 1.5)
```

Position priority gauge.

---

## Scarcity

```python
adp_aware_drafted
scarcity_ratio
```

Measures how much expected positional talent has already disappeared.

## Used By

```text
Position Status Bar
Consider Options
On-The-Clock Assistant
```

---

# Dynamic Planning Values

## Purpose

Maintain the best available draft plan as conditions change.

## Core Objects

```python
target_rounds_QB
target_rounds_RB
target_rounds_WR
target_rounds_TE
target_rounds_LB
target_rounds_DL
target_rounds_DB

plan_picks
draft_plan
```

## Status Values

```python
ACTIVE
INVALIDATED
COMPLETED
```

---

# Future Decision Engine

## Purpose

Answer:

> What should I do next?

### Inputs

```text
Static Player Values
+
Dynamic Draft Values
+
Dynamic Planning Values
```

### Potential Metrics

```python
planning_score
replacement_score
future_value
draft_cost
```

### Consumers

```text
Current Plan
Consider Options
On-The-Clock Assistant
```

---

# Architectural Rules

## Rule 1

Player quality remains stable.

Do not inflate player value because better players were drafted.

---

## Rule 2

Urgency is dynamic.

Elasticity, scarcity, margin, ratio, and urgency should update after every pick.

---

## Rule 3

Plans are dynamic.

Draft plans are living documents and should continuously adapt.

---

## Rule 4

Tab Responsibilities

```text
Position Status Bar = Position urgency right now.

Consider Options = Player choices right now.

Current Plan = Future strategy.

Hypothetical Roster = Evaluate plan outcome.
```
---
update as of 8/20/2026