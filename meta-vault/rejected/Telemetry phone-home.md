---
tags: [rejected]
---

# Telemetry phone-home *(rejected)*

> Memcon could report anonymized usage stats. How many writes per
> session, which tool is most popular, install successes vs failures.
> Useful for prioritizing what to build.

## Why no

It would break the "nothing leaves your machine" guarantee. Even with
opt-in consent, even with anonymous data, the moment the binary is
*capable* of phoning home, the trust is gone — savvy users will run
network monitors to verify, and the promise becomes "trust us about
the toggle."

Useful product analytics without phone-home: log to a local file the
user can inspect. Show it themselves if they want to share. Never
emit network traffic the user didn't initiate.

## Related
- [[Local-first]]
- [[SaaS-first version]]
- [[Why local LLM not cloud]]
