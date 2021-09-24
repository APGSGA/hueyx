# Release notes

### 1.0.2
- Updated for Huey 2.3
- Use built-in django autodiscover modules method
- Fixed "docker build"

### 1.0.1
- Extracted heartbeat methods into HeartBeatManager class

### 1.0.0
- Added support for huey 2.0 and its new signal system.
- Removed `fire_enqueued_events`. By default, hueyx will automatically report metrics to redis.
- Added migration document.

### 0.1.2
- Added `heartbeat_timeout` parameter for `db_task`

### 0.1.0

- Added the `EVENT_ENQUEUED` event when a task has been enqueued.
- Added support for [huey-exporter](https://github.com/APGSGA/huey-exporter).
- Rename `fire_enqueued_event` to `fire_enqueued_events`.
- Moved `fire_enqueued_events` to huey config.
