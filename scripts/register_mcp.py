#!/usr/bin/env python3
"""
Register Memcon as an MCP server in Claude Desktop's config — idempotent,
cross-platform (macOS / Windows / Linux).

Run by install.sh / install.bat at the end of setup. Also safe to invoke
directly any time the venv or repo moves:

    python3 scripts/register_mcp.py

Behaviour:
  - Detects the Claude Desktop config path per-OS.
  - Picks the right venv python (bin/python3 on Unix, Scripts/python.exe
    on Windows).
  - Creates the parent directory + an empty {} config if missing.
  - Backs up any existing config the first time we touch it.
  - Merges into mcpServers — preserves everything else.
  - Uses absolute paths so it works under sandboxed macOS spawns.
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


def venv_python(repo: Path) -> Path:
    """Locate the venv interpreter for the current OS."""
    if platform.system() == "Windows":
        return repo / ".venv" / "Scripts" / "python.exe"
    return repo / ".venv" / "bin" / "python3"


def claude_config_path() -> Path:
    """Where Claude Desktop reads its MCP config from on this OS."""
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "Claude" / "claude_desktop_config.json"
    # Linux / others
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def main() -> int:
    py = venv_python(REPO)
    server = REPO / "memcon_mcp" / "server.py"

    if not py.exists():
        print(f"⚠️  venv python not found at {py}", file=sys.stderr)
        print("   Run the installer first (./install.sh on macOS/Linux, install.bat on Windows).", file=sys.stderr)
        return 1
    if not server.exists():
        print(f"⚠️  MCP server not found at {server}", file=sys.stderr)
        return 1

    cfg_path = claude_config_path()
    try:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        print(f"⚠️  Cannot create {cfg_path.parent}: {e}", file=sys.stderr)
        print("   Skipping MCP registration. You can add it manually later — see memcon_mcp/README.md.", file=sys.stderr)
        return 0  # non-fatal — installer should keep going

    # Load (or initialise) the config
    cfg: dict = {}
    if cfg_path.exists() and cfg_path.stat().st_size > 0:
        raw = cfg_path.read_text(encoding="utf-8")
        try:
            cfg = json.loads(raw)
            if not isinstance(cfg, dict):
                raise ValueError(f"config root must be an object, got {type(cfg).__name__}")
        except (json.JSONDecodeError, ValueError) as e:
            backup = cfg_path.with_suffix(f".bak-{int(time.time())}")
            shutil.copy2(cfg_path, backup)
            print(f"⚠️  Existing config at {cfg_path} is not valid JSON ({e}).", file=sys.stderr)
            print(f"   Backed up to {backup.name} and starting fresh.", file=sys.stderr)
            cfg = {}

    # First-touch backup so the user can roll back even on a clean merge
    if cfg and not any(cfg_path.parent.glob(f"{cfg_path.name}.bak-*")):
        backup = cfg_path.with_suffix(f".bak-{int(time.time())}")
        try:
            shutil.copy2(cfg_path, backup)
            print(f"📦 Backed up existing config → {backup.name}")
        except Exception:
            pass  # best-effort

    # Merge — preserve everything else
    mcp_servers = cfg.setdefault("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        # someone put a non-object there; bail safely
        print(f"⚠️  Existing 'mcpServers' is not an object — refusing to clobber.", file=sys.stderr)
        return 1

    mcp_servers["memcon"] = {
        "command": str(py),
        "args": [str(server)],
        # Spawn the server IN the repo dir. Without this, Claude Desktop launches
        # it with cwd=/, so a bare load_dotenv() and any relative path resolve
        # against / instead of the project.
        "cwd": str(Path(str(server)).parent.parent),
    }

    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    print("✅ Memcon registered as MCP server in:")
    print(f"   {cfg_path}")
    print()
    print("   Quit Claude Desktop (Cmd+Q on macOS, right-click tray → Quit on Windows)")
    print('   and reopen. Then ask Claude: "use memcon to find anything about the Redis pool exhaustion"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
