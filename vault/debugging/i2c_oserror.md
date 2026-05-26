---
memory_type: episodic
subsystem: imu
tags: [i2c, oserror, mpu6050, errno121]
date: 2026-05-24
---

# I2C OSError Errno 121

## Symptom
OSError Errno 121 during IMU reads after sustained operation.

## Cause
Vibration-loosened wiring or power brownout from servo current spikes.

## Fix Applied
Retry logic and last-known-value caching added to IMU reader.

## Status
Mitigated. Monitor under load.
