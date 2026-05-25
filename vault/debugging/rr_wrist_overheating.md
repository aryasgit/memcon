---
memory_type: episodic
subsystem: servo
tags: [rr_wrist, overheating, gait, backward]
date: 2026-05-24
---

# RR Wrist Servo Overheating

## Symptom
RR wrist servo overheats during backward gait, causing torque loss and snap to default angle.

## Suspected Cause
Unequal static load distribution. RR leg bearing more weight than others during backward motion.

## Diagnostics Planned
- Paper-slip foot contact test to check static weight distribution
- IMU roll/pitch logging during backward gait to detect lean

## Status
Open. No fix applied yet.
