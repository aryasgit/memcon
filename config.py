import yaml
from pathlib import Path

_config = None

def get_config() -> dict:
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "memcon.config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)

        # Resolve vault.path to absolute, anchored at the project root (the
        # directory holding memcon.config.yaml). Critical for MCP because
        # Claude Desktop spawns the server with cwd=/ on macOS, which would
        # otherwise make "./vault" resolve to /vault (read-only root fs).
        project_root = config_path.parent.resolve()
        vault = _config.get('vault') or {}
        vp = vault.get('path')
        if vp and not Path(vp).is_absolute():
            _config['vault']['path'] = str((project_root / vp).resolve())

    return _config

def cfg(*keys):
    result = get_config()
    for key in keys:
        result = result[key]
    return result
