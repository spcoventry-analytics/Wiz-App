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

_Last updated: August 9, 2025_
