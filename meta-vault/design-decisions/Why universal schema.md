---
tags: [design-decision]
---

# Why universal schema

*Decided during: v3.1*

The pre-v3.1 schema was shaped for hardware debugging — symptom,
cause, fix. That's a great template for a [[BARQ (the robot)|BARQ]]
debug session. It's a *terrible* template for:
- "we decided to use Postgres" (a decision)
- "what is a JWT refresh token?" (a concept)
- "we tried int8 quant on the IK model" (an experiment)

Forcing all of those into symptom/cause/fix loses the structure that
makes each type useful. The universal schema gives each kind its own
middle sections while sharing the outer shape (TL;DR / Context /
Related / See also).

## Related
- [[Universal note schema]]
- [[Note kinds]]
- [[BARQ (the robot)]]
