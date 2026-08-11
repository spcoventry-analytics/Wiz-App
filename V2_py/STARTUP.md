# Starting Up the Wiz-App Streamlit Server

## Prerequisites
- Python 3.11+ installed
- This project uses a virtual environment to avoid conflicts with Anaconda

## Quick Start (First Time)

### 1. Create Virtual Environment
```powershell
cd c:\Users\spcov\Data\Wiz-App\V2_py
python -m venv venv
```

### 2. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Server (Every Time After)

### 1. Navigate to Project Directory
```powershell
cd c:\Users\spcov\Data\Wiz-App\V2_py
```

### 2. Start the Server
```powershell
python -m streamlit run app.py
```

### 3. Access the App
- **Local Browser:** http://localhost:8501
- **Network Access:** http://172.16.0.193:8501

## Configuration Setup

The app requires ESPN league credentials. On first run:

1. Go to **Configuration** page in the app
2. Select your league (Cujos League or Family League)
3. You'll need to set up Streamlit secrets for ESPN credentials:

### Creating `.streamlit/secrets.toml`

If you don't have this file, create it at:
```
c:\Users\spcov\Data\Wiz-App\V2_py\.streamlit\secrets.toml
```

Add your ESPN credentials:
```toml
# Cujos League Credentials
cujos_league_id = "YOUR_LEAGUE_ID"
stephen_espn_s2 = "YOUR_ESPN_S2_COOKIE"
stephen_swid = "YOUR_SWID_COOKIE"

# Family League Credentials (optional)
family_league_id = "YOUR_FAMILY_LEAGUE_ID"
stephen_espn_s2 = "YOUR_ESPN_S2_COOKIE"
stephen_swid = "YOUR_SWID_COOKIE"
courtney_espn_s2 = "COURTNEY_ESPN_S2_COOKIE"
courtney_swid = "COURTNEY_SWID_COOKIE"
# ... add other family members as needed
```

### Getting ESPN Credentials
1. Log into ESPN.com in your browser
2. Open DevTools (F12 or Ctrl+Shift+I)
3. Go to **Application** tab → **Cookies**
4. Find and copy the values for:
   - `espn_s2`
   - `SWID`
5. Paste them into `secrets.toml`

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### "pip is not recognized"
This happens because Anaconda Python doesn't have pip in PATH. Always use:
```powershell
python -m pip install <package>
```

### "Streamlit is not recognized"
Make sure you're running the command from the project directory and using the virtual environment Python.

### Port 8501 already in use
If port 8501 is already occupied, run:
```powershell
python -m streamlit run app.py --server.port 8502
```

## App Pages

- **Current Board** - View live draft board with all teams and their picks
- **Consider Options** - Get player recommendations for your next pick
- **Current Plan** - View your projected starting lineup and gaps to fill
- **Configuration** - Select league, user, and season

## Key Files
- `app.py` - Main Streamlit app entry point
- `requirements.txt` - Python package dependencies
- `configuration.py` - League configuration page
- `draft_board.py` - Draft board display
- `enter_pick.py` - Manual pick entry
- `consider_options.py` - Player recommendations
- `current_plan.py` - Team projections dashboard

---

**Last Updated:** August 8, 2026
