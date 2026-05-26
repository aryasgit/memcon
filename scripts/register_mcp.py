#!/usr/bin/env python3
"""
Register Memcon as an MCP server in Claude Desktop's config — idempotent.

Run by install.sh at the end of setup, but also safe to invoke directly:
    python3 scripts/register_mcp.py

Behaviour:
  - Detects the Claude Desktop config path per-OS.
  - Creates the parent directory + an empty {} config if missing.
  - Backs up any existing config the first time we touch it.
  - Merges (does not replace) — preserves all other mcpServers entries.
  - Uses absolute paths for command and args so it works under sandboxed
    macOS spawns (Claude does not honour cwd; we don't rely on it).
"""
from __future__ import annotations
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "bin" / "python3"
SERVER = REPO / "memcon_mcp" / "server.py"


def claude_config_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", str(home))) / "Claude" / "claude_desktop_config.json"
    # Linux / others
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def main() -> int:
    # Windows-style paths use backslashes; on macOS/Linux .venv/Scripts vs bin differs.
    py = REPO / (".venv/Scripts/python.exe" if platform.system() == "Windows" else ".venv/bin/python3")
    server = REPO / "memcon_mcp" / "server.py"

    if not py.exists():
        print(f"⚠️  venv python not found at {py}")
        print("   run ./install.sh first")
        return 1
    if not server.exists():
        print(f"⚠️  MCP server not found at {server}")
        return 1

    cfg_path = claude_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    # Load (or initialise) the config
    if cfg_path.exists() and cfg_path.stat().st_size > 0:
        raw = cfg_path.read_text(encoding="utf-8")
        try:
            cfg = json.loads(raw)
        except json.JSONDecodeError as e:
            backup = cfg_path.with_suffix(f".bak-{int(time.time())}")
            shutil.copy2(cfg_path, backup)
            print(f"⚠️  Existing config is not valid JSON ({e}).")
            print(f"   Backed up to {backup} and starting fresh.")
            cfg = {}
    else:
        cfg = {}

    # Back up first-time touch so the user can roll back
    if cfg and not any(cfg_path.parent.glob(f"{cfg_path.name}.bak-*")):
        backup = cfg_path.with_suffix(f".bak-{int(time.time())}")
        shutil.copy2(cfg_path, backup)
        print(f"📦 Backed up existing config → {backup.name}")

    # Merge — preserve everything else
    mcp_servers = cfg.setdefault("mcpServers", {})
    mcp_servers["memcon"] = {
        "command": str(py),
        "args": [str(server)],
    }

    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Memcon registered as MCP server in:")
    print(f"   {cfg_path}")
    print()
    print("   Quit Claude Desktop (Cmd+Q) and reopen to load it.")
    print("   Then ask: \"use memcon to look up what we know about servo overheating\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
