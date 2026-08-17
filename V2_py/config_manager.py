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
import pandas as pd
import numpy as np


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
    def _convert_to_json_serializable(obj: Any) -> Any:
        """
        Recursively convert numpy types and other non-JSON-serializable objects to JSON-serializable types.
        
        Args:
            obj: Any object that may contain numpy types
        
        Returns:
            Object with all numpy types converted to Python native types
        """
        if isinstance(obj, dict):
            return {key: ConfigManager._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ConfigManager._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
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
        
        # Convert numpy types to JSON-serializable types
        config_data = ConfigManager._convert_to_json_serializable(config_data)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return config_filename
    
    @staticmethod
    def get_latest_config() -> Optional[Dict[str, Any]]:
        """
        Load the most recently modified config file.
        
        Returns:
            Config dictionary, or None if no config files exist or if latest config is invalid JSON
        """
        configs = ConfigManager.list_configs()
        if not configs:
            return None
        
        try:
            return ConfigManager.load_config(configs[0])
        except json.JSONDecodeError as e:
            # Skip corrupted config and try next one
            import sys
            print(f"Warning: Corrupted config {configs[0]}: {e}", file=sys.stderr)
            
            # Try remaining configs
            for config_file in configs[1:]:
                try:
                    return ConfigManager.load_config(config_file)
                except json.JSONDecodeError:
                    continue
            
            # All configs are corrupted
            return None
    
    @staticmethod
    def get_latest_config_filename() -> Optional[str]:
        """
        Get the filename of the most recently modified config file.
        
        Returns:
            Config filename (e.g., "config_2026_08_14_1430.json"), or None if no config files exist
        """
        configs = ConfigManager.list_configs()
        if not configs:
            return None
        return configs[0]
    
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
    
    @staticmethod
    def save_strategy(config_filename: str, strategy: Dict[str, List[int]]) -> None:
        """
        Save strategy (position → target rounds mapping) to config.
        
        Args:
            config_filename: Name of config file
            strategy: Dict mapping position to list of target rounds, e.g., {'QB': [3, 4], 'RB': [1, 5]}
        """
        # Try to load config, with fallback to older configs if corrupted
        config = None
        try:
            config = ConfigManager.load_config(config_filename)
        except (json.JSONDecodeError, FileNotFoundError):
            # Try to load from older configs
            configs = ConfigManager.list_configs()
            for config_file in configs:
                if config_file == config_filename:
                    continue
                try:
                    config = ConfigManager.load_config(config_file)
                    break
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        # If still no config, create minimal one
        if config is None:
            config = {
                'league_id': None,
                'season_id': None,
                'draft_order': [],
                'my_team': None,
                'current_plan': {'keepers': {}},
            }
        
        if 'strategy' not in config:
            config['strategy'] = {}
        # Convert numpy types to JSON-serializable types
        config['strategy'] = ConfigManager._convert_to_json_serializable(strategy)
        ConfigManager.save_config(config, config_filename)
    
    @staticmethod
    def load_strategy(config_filename: str) -> Dict[str, List[int]]:
        """
        Load strategy from config.
        
        Args:
            config_filename: Name of config file
        
        Returns:
            Strategy dict, or empty dict if not found
        """
        try:
            config = ConfigManager.load_config(config_filename)
            return config.get('strategy', {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    def save_plan(config_filename: str, plan: List[Dict[str, Any]]) -> None:
        """
        Save plan (round → position → target player mapping) to config.
        
        Args:
            config_filename: Name of config file
            plan: List of dicts, each with 'round', 'position', 'target_player', 'status'
        """
        # Try to load config, with fallback to older configs if corrupted
        config = None
        try:
            config = ConfigManager.load_config(config_filename)
        except (json.JSONDecodeError, FileNotFoundError):
            # Try to load from older configs
            configs = ConfigManager.list_configs()
            for config_file in configs:
                if config_file == config_filename:
                    continue
                try:
                    config = ConfigManager.load_config(config_file)
                    break
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        # If still no config, create minimal one
        if config is None:
            config = {
                'league_id': None,
                'season_id': None,
                'draft_order': [],
                'my_team': None,
                'current_plan': {'keepers': {}},
            }
        
        if 'plan' not in config:
            config['plan'] = []
        # Convert numpy types to JSON-serializable types
        config['plan'] = ConfigManager._convert_to_json_serializable(plan)
        ConfigManager.save_config(config, config_filename)
    
    @staticmethod
    def load_plan(config_filename: str) -> List[Dict[str, Any]]:
        """
        Load plan from config.
        
        Args:
            config_filename: Name of config file
        
        Returns:
            Plan list, or empty list if not found
        """
        try:
            config = ConfigManager.load_config(config_filename)
            return config.get('plan', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    @staticmethod
    def calculate_plan_score(plan: List[Dict[str, Any]], player_data: pd.DataFrame, tier_baselines: Dict[str, Dict[int, float]]) -> Dict[str, float]:
        """
        Score a plan based on three metrics:
        - Total POS Value: Sum of PPG for planned players
        - Total Norm Value: Sum of (PPG - tier baseline) for planned players
        - Total PPG: Total projected points per game
        
        Args:
            plan: List of planned picks
            player_data: DataFrame with all available players (includes draft_results)
            tier_baselines: Dict mapping position to tier to baseline PPG
        
        Returns:
            Dict with 'total_pos_value', 'total_norm_value', 'total_ppg' keys
        """
        total_pos_value = 0
        total_norm_value = 0
        total_ppg = 0
        
        for pick in plan:
            target_player = pick.get('target_player', '').strip()
            position = pick.get('position', '')
            round_num = pick.get('round', 0)
            status = pick.get('status', 'ACTIVE')
            
            # Skip invalidated picks
            if status == 'INVALIDATED':
                continue
            
            # Find player by name
            player_match = player_data[player_data['name_x'].str.lower() == target_player.lower()]
            
            if not player_match.empty:
                player = player_match.iloc[0]
                ppg = player.get('PPG', 0)
                
                # Handle NaN for IDP players
                if pd.isna(ppg):
                    ppg = 0
                
                total_pos_value += ppg
                total_ppg += ppg
                
                # Calculate normalized value (PPG - tier baseline)
                # Tier is based on which slot this is for the position
                slot_num = len([p for p in plan if p['position'] == position and plan.index(p) < plan.index(pick)]) + 1
                tier_baseline = 0
                if position in tier_baselines and (slot_num - 1) in tier_baselines[position]:
                    tier_baseline = tier_baselines[position][slot_num - 1]
                
                total_norm_value += (ppg - tier_baseline)
        
        return {
            'total_pos_value': round(total_pos_value, 1),
            'total_norm_value': round(total_norm_value, 1),
            'total_ppg': round(total_ppg, 1),
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
