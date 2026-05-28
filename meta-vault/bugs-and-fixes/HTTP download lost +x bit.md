---
tags: [bug-fix]
---

# HTTP download lost +x bit

**Downloading `memcon-install.command` over HTTP stripped the executable bit. Double-click did nothing.**

The macOS installer was a single `.command` file (which is just a
shell script with an extension Finder treats as runnable). Worked great
when copied locally with `cp`. Distributed via the landing page download
button: the browser saved it without the `+x` bit. Double-click silently
no-op'd.

**Fix:** ship a `.zip` instead. `cp -p` (or `zip -9` and `unzip`)
preserves the executable bit. Users now download `memcon-install-mac.zip`,
unzip it, then right-click → Open the `.command` file.

The actual canonical install path is the `curl | bash` one-liner; the
zip is the fallback for users who refuse to pipe-into-shell (fair).

**Lesson:** HTTP transit doesn't preserve POSIX permissions. Use a
container format that does, or do the chmod client-side as part of an
installer.

## Related
- [[bootstrap.sh]]
- [[install.sh]]
