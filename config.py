import yaml
from pathlib import Path

_config = None

def get_config() -> dict:
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "memcon.config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)
    return _config

def cfg(*keys):
    result = get_config()
    for key in keys:
        result = result[key]
    return result
