#!/usr/bin/env python3
"""Relocate the memcon vault to a universal, sync-friendly home.

By default the vault lives inside the repo (./vault), which makes your memory
*project-local* — the opposite of memcon's promise. Move it somewhere global
(ideally synced across machines) so the same brain is reachable from every
project, every MCP client, and every machine.

    python scripts/relocate_vault.py [TARGET] [--apply] [--remove-source]

TARGET   where the brain should live. Default: ~/.memcon/vault
         For cross-machine sync, point it at a synced folder:
           iCloud  : "~/Library/Mobile Documents/com~apple~CloudDocs/memcon/vault"
           Dropbox : "~/Dropbox/memcon/vault"
           git     : a private repo you clone + pull on each machine

DRY RUN by default — prints the plan and changes nothing. Pass --apply to do it:
copies the vault to TARGET, writes the new path into memcon.config.local.yaml
(gitignored, per-machine, so the tracked config stays clean), rebuilds the
search index at the new home, and (with --remove-source) deletes the old vault.

After --apply, restart your MCP clients (quit + reopen Claude Desktop, restart
Claude Code) so they read the new location.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from config import cfg


def _count_md(p: Path) -> int:
    return sum(1 for _ in p.rglob("*.md")) if p.exists() else 0


def main(argv) -> int:
    flags = {a for a in argv if a.startswith("--")}
    positional = [a for a in argv if not a.startswith("--")]
    do_apply = "--apply" in flags
    remove_source = "--remove-source" in flags

    src = Path(cfg("vault", "path")).resolve()
    target = (Path(positional[0]).expanduser() if positional
              else Path.home() / ".memcon" / "vault").resolve()
    local_cfg = REPO / "memcon.config.local.yaml"

    print("memcon vault relocation")
    print(f"  source : {src}   ({_count_md(src)} notes)")
    print(f"  target : {target}")
    print(f"  config : {local_cfg}  (gitignored, per-machine)")

    if src == target:
        print("\nsource and target are the same — nothing to do.")
        return 0
    if not src.exists():
        print(f"\n!! source vault does not exist: {src}")
        return 1

    if not do_apply:
        print("\nDRY RUN — nothing changed.")
        print(f"  to execute:  python scripts/relocate_vault.py "
              f"{positional[0] if positional else ''} --apply")
        return 0

    # 1) copy the notes (never move first — keep the source until verified)
    if _count_md(target) > 0:
        print(f"\n!! target already holds {_count_md(target)} notes — refusing to "
              f"overwrite.\n   Pick an empty target or merge manually.")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    print("\n→ copying vault…")
    shutil.copytree(src, target, dirs_exist_ok=True)

    # 2) point config at the new home via the gitignored per-machine override
    print(f"→ writing {local_cfg.name} (keeps the tracked config clean)…")
    local_cfg.write_text(
        "# Per-machine memcon overrides — gitignored, never committed.\n"
        "# Written by scripts/relocate_vault.py.\n"
        "vault:\n"
        f'  path: "{target.as_posix()}"\n'
    )

    # 3) rebuild the index at the new location (a fresh process reads new cfg)
    print("→ rebuilding the search index at the new home…")
    r = subprocess.run(
        [sys.executable, "-c",
         "from ingestion.ingest import reindex_vault; print(reindex_vault())"],
        cwd=str(REPO), env={**os.environ},
    )
    if r.returncode != 0:
        print("!! reindex failed — notes are copied and config is set; the index "
              "self-heals on the next recall (or run the memcon_reindex tool).")

    # 4) optionally drop the old in-repo vault
    if remove_source:
        print(f"→ removing old vault at {src}…")
        shutil.rmtree(src, ignore_errors=True)
    else:
        print(f"\n(kept the old vault at {src}; delete it once you've confirmed.)")

    print("\n✅ done. Restart your MCP clients (quit+reopen Claude Desktop, restart "
          "Claude Code) so they read the new location.")
    print(f"   For cross-machine sync, ensure {target} lives in a synced folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
