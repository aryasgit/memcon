import os
import yaml
from pathlib import Path

_config = None


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge `override` into `base` (override wins). Used to layer a
    per-machine memcon.config.local.yaml over the tracked config."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def get_config() -> dict:
    """
    Load memcon.config.yaml, layer an optional per-machine override, then apply
    environment overrides for multi-project use:

      MEMCON_VAULT       — override vault.path (absolute or ~-path)
      MEMCON_COLLECTION  — override memory.collection (Qdrant collection name)
      MEMCON_MODEL       — override llm.model (Ollama model tag)
      MEMCON_QDRANT_HOST — handled in memory/qdrant_store.py
      MEMCON_QDRANT_PORT — handled in memory/qdrant_store.py

    Precedence (low → high): memcon.config.yaml < memcon.config.local.yaml < env.

    The local file (gitignored) is how each machine points at its own vault —
    e.g. an iCloud-synced folder so the same brain follows you across machines —
    without dirtying the tracked config. Switch projects on the fly with the env
    vars, e.g.:
      MEMCON_VAULT=~/projects/foo/vault MEMCON_COLLECTION=foo_memory ./start.sh
    """
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "memcon.config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)

        # ── per-machine override (gitignored): keeps the tracked config clean
        #    while letting each machine point at its own (e.g. synced) vault.
        #    Written by scripts/relocate_vault.py.
        local_path = config_path.parent / "memcon.config.local.yaml"
        if local_path.exists():
            try:
                with open(local_path) as lf:
                    _deep_merge(_config, yaml.safe_load(lf) or {})
            except Exception:
                pass

        # ── vault.path: env override > ~-expand + absolutise relative path
        vault = _config.setdefault('vault', {})
        env_vault = os.environ.get('MEMCON_VAULT')
        if env_vault:
            vault['path'] = str(Path(env_vault).expanduser().resolve())
        else:
            vp = vault.get('path')
            if vp:
                vp = Path(vp).expanduser()
                if not vp.is_absolute():
                    vp = config_path.parent.resolve() / vp
                vault['path'] = str(vp.resolve())

        # ── memory.collection: env override
        memory = _config.setdefault('memory', {})
        env_collection = os.environ.get('MEMCON_COLLECTION')
        if env_collection:
            memory['collection'] = env_collection

        # ── llm.model: env override (matches install.sh's MEMCON_MODEL)
        llm = _config.setdefault('llm', {})
        env_model = os.environ.get('MEMCON_MODEL')
        if env_model:
            llm['model'] = env_model

    return _config


def cfg(*keys):
    result = get_config()
    for key in keys:
        result = result[key]
    return result
