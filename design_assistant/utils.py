import os
import yaml
from typing import Dict, Any

def load_prompt(filename: str) -> str:
    """Load a prompt from a YAML file.
    
    Args:
        filename (str): Name of the YAML file in the prompts directory
        
    Returns:
        str: The prompt instructions from the YAML file
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
    """
    prompt_dir = os.path.join(os.path.dirname(__file__), 'prompts')
    filepath = os.path.join(prompt_dir, filename)
    
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('instructions', '')
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in prompt file {filename}: {str(e)}") 