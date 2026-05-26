import os
import yaml
from pathlib import Path

_config = None


def get_config() -> dict:
    """
    Load memcon.config.yaml and apply environment overrides for multi-project
    use:

      MEMCON_VAULT       — override vault.path (absolute path expected)
      MEMCON_COLLECTION  — override memory.collection (Qdrant collection name)
      MEMCON_MODEL       — override llm.model (Ollama model tag)
      MEMCON_QDRANT_HOST — handled in memory/qdrant_store.py
      MEMCON_QDRANT_PORT — handled in memory/qdrant_store.py

    Switch projects by exporting these before launching Memcon, e.g.:
      MEMCON_VAULT=~/projects/foo/vault \
      MEMCON_COLLECTION=foo_memory \
      ./start.sh
    """
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "memcon.config.yaml"
        with open(config_path) as f:
            _config = yaml.safe_load(f)

        # ── vault.path: env override > absolutise relative path
        vault = _config.setdefault('vault', {})
        env_vault = os.environ.get('MEMCON_VAULT')
        if env_vault:
            vault['path'] = str(Path(env_vault).expanduser().resolve())
        else:
            vp = vault.get('path')
            if vp and not Path(vp).is_absolute():
                project_root = config_path.parent.resolve()
                vault['path'] = str((project_root / vp).resolve())

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
