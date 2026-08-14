"""
config_manager.py - Manage draft configuration files

Handles loading, saving, and managing config_*.json files that contain:
- League setup (league_id, season_id, draft_order, my_team)
- Keepers for all teams
- Current draft plan (planned picks)
- Draft results (once filled in)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class ConfigManager:
    """Manage draft configuration files."""
    
    CONFIG_DIR = Path(__file__).parent  # V2_py directory
    CONFIG_PREFIX = "config_"
    CONFIG_SUFFIX = ".json"
    
    @staticmethod
    def list_configs() -> List[str]:
        """
        List all available config files in chronological order (newest first).
        
        Returns:
            List of config filenames (e.g., ["config_2026_08_14_1430.json", ...])
        """
        configs = []
        for file in ConfigManager.CONFIG_DIR.glob(f"{ConfigManager.CONFIG_PREFIX}*{ConfigManager.CONFIG_SUFFIX}"):
            configs.append(file.name)
        
        # Sort by modification time (newest first)
        configs.sort(
            key=lambda f: os.path.getmtime(ConfigManager.CONFIG_DIR / f),
            reverse=True
        )
        return configs
    
    @staticmethod
    def load_config(config_filename: str) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            config_filename: Name of config file (e.g., "config_2026_08_14.json")
        
        Returns:
            Dictionary with config data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_path = ConfigManager.CONFIG_DIR / config_filename
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_filename}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_config(config_data: Dict[str, Any], config_filename: Optional[str] = None) -> str:
        """
        Save a configuration file.
        
        Args:
            config_data: Dictionary with config data
            config_filename: Optional filename. If not provided, generates one with timestamp.
                           (e.g., "config_2026_08_14_1430.json")
        
        Returns:
            Filename that was saved
            
        Raises:
            IOError: If file cannot be written
        """
        if config_filename is None:
            # Generate filename with timestamp: config_YYYY_MM_DD_HHMM.json
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
            config_filename = f"{ConfigManager.CONFIG_PREFIX}{timestamp}{ConfigManager.CONFIG_SUFFIX}"
        
        config_path = ConfigManager.CONFIG_DIR / config_filename
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return config_filename
    
    @staticmethod
    def get_latest_config() -> Optional[Dict[str, Any]]:
        """
        Load the most recently modified config file.
        
        Returns:
            Config dictionary, or None if no config files exist
        """
        configs = ConfigManager.list_configs()
        if not configs:
            return None
        
        return ConfigManager.load_config(configs[0])
    
    @staticmethod
    def update_plan(config_filename: str, planned_picks: List[Dict[str, Any]]) -> None:
        """
        Update the planned_picks in a config file.
        
        Args:
            config_filename: Name of config file
            planned_picks: List of dicts with 'round' and 'position' keys
        """
        config = ConfigManager.load_config(config_filename)
        config['current_plan']['planned_picks'] = planned_picks
        ConfigManager.save_config(config, config_filename)
    
    @staticmethod
    def update_drafted_players(config_filename: str, drafted_players: List[Dict[str, Any]]) -> None:
        """
        Update the drafted_players in a config file (after actual draft picks).
        
        Args:
            config_filename: Name of config file
            drafted_players: List of dicts with player pick info
        """
        config = ConfigManager.load_config(config_filename)
        config['current_plan']['drafted_players'] = drafted_players
        ConfigManager.save_config(config, config_filename)
    
    @staticmethod
    def extract_league_info(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract league information from config for app initialization.
        
        Args:
            config: Config dictionary
        
        Returns:
            Dictionary with league_id, season_id, draft_order, my_team, keepers
        """
        return {
            'league_id': config.get('league_id'),
            'season_id': config.get('season_id'),
            'draft_order': config.get('draft_order', []),
            'my_team': config.get('my_team'),
            'keepers': config.get('current_plan', {}).get('keepers', {}),
            'planned_picks': config.get('current_plan', {}).get('planned_picks', []),
        }


# Example usage for tomorrow's implementation:
"""
# In app.py initialization:
from config_manager import ConfigManager

# Load latest config
config = ConfigManager.get_latest_config()
if config:
    league_info = ConfigManager.extract_league_info(config)
    st.session_state['league_id'] = league_info['league_id']
    st.session_state['season_id'] = league_info['season_id']
    st.session_state['draft_order'] = league_info['draft_order']
    st.session_state['teams'] = league_info['draft_order']
    st.session_state['my_team'] = league_info['my_team']
    st.session_state['keepers'] = league_info['keepers']
    # etc...

# When saving from configuration.py:
ConfigManager.update_plan(config_filename, planned_picks)
ConfigManager.update_drafted_players(config_filename, drafted_players)

# List available configs for user to choose:
configs = ConfigManager.list_configs()
selected = st.selectbox("Select config:", configs)
if selected:
    config = ConfigManager.load_config(selected)
"""
