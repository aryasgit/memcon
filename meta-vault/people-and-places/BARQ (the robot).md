---
tags: [place, project]
---

# BARQ (the robot)

Autonomous quadruped robot project. The reason memcon exists.

## Why memcon was built for BARQ

A quadruped is a debugging machine. Every gait test surfaces something
weird: a servo overheating, an IMU drift, a power brownout, a planner
edge case. Each finding is small, but they accumulate. The pre-memcon
flow was: figure it out, file it in your head, forget it three weeks
later, re-debug from scratch.

Memcon's job is to make those findings *survive* into future sessions —
specifically into [[Claude (Anthropic)|Claude]] sessions, which is
where most of the debugging actually happens.

## How BARQ shaped memcon

- The original [[Subsystems]] list was BARQ-shaped (servo, imu, gait,
  power, vision, voice, slam, ik). [[v3.1 — Rich notes, hybrid recall|v3.1]]
  made the list optional.
- The 4-field schema (symptom / cause / fix) was perfect for BARQ debugs.
  But terrible for everything else — see [[Why universal schema]].
- The [[Note kinds|new note kinds]] (concept, reference, meeting,
  breakthrough) generalize beyond the debug-session shape.

## Related
- [[Subsystems]]
- [[Aryaman (aryasgit)]]
- [[The story]]
