# Release notes

### 0.2.0
- Added support for huey 2.0 and its new signal system.
- Removed `fire_enqueued_events`. By default, hueyx will automatically report metrics to prometheus if installed.
- [huey-exporter](https://github.com/APGSGA/huey-exporter) is not supported anymore.
- Added Prometheus support.
    - Added new command 'run_hueyx_prometheus'.

### 0.1.2
- Added `heartbeat_timeout` parameter for `db_task`

### 0.1.0

- Added the `EVENT_ENQUEUED` event when a task has been enqueued.
- Added support for [huey-exporter](https://github.com/APGSGA/huey-exporter).
- Rename `fire_enqueued_event` to `fire_enqueued_events`.
- Moved `fire_enqueued_events` to huey config.