"""
Utility functions for the Design Assistant application.
"""

import yaml
import os
from typing import Dict, Any

def load_prompt(prompt_file: str) -> str:
    """
    Load an instruction prompt from a YAML file.
    
    Args:
        prompt_file (str): Path to the prompt file
        
    Returns:
        str: The instruction string from the prompt file.
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        yaml.YAMLError: If the prompt file is invalid YAML
    """
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', prompt_file)
    with open(prompt_path, 'r') as f:
        prompt_data = yaml.safe_load(f)
        return prompt_data.get('instructions', '') 