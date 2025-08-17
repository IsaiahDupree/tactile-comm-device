# Data Mode Infrastructure (M8)

This document outlines the planned "Data Mode": a binary, resumable, secure protocol enabling external apps to control and update the device over Serial and future transports (TCP/WebSocket).

## Goals
- Binary framing with CRC and windowed ACKs
- Transport abstraction (Serial now; TCP/WS later)
- Authenticated session handshake
- Resumable uploads, journaling, atomic commit/rollback
- Peripherals control API and telemetry
- Robust desktop client with retries/backoff and diagnostics

## Components
- Protocol framing: header {ver,flags,seq,ack,type,win,len} + CRC32 trailer
- Transport: `ITransport` interface with Serial and future WS/TCP implementations
- Session: handshake, flow control, timeouts, watchdogs
- File updates: staging, journal, commit, rollback, path safety, quotas
- Telemetry: GET_INFO, STREAM_LOGS, counters, health

## Message Types (draft)
- CTRL: GET_INFO, AUTH_INIT, AUTH_PROVE, PING, BYE
- FS: FS_BEGIN, FS_PUT, FS_DATA, FS_RESUME, FS_DONE, FS_COMMIT, FS_ABORT, ROLLBACK_LAST
- DIAG: SD_FREE, I2C_SCAN, READ_BUTTONS, SET_VOLUME, BEEP, LED
- LOG: STREAM_LOGS start/stop, chunk

## Security (draft)
- Token-based auth (mode.cfg) + nonce challenge; optional HMAC for sensitive operations
- Single-client guard with backoff on auth failures
- Path normalization, root whitelists, and quotas

## Desktop Client
- Serial-first transport; pluggable strategy for TCP/WS
- Robust updater (resume, retries, progress, hash)
- Diagnostics suite and token storage via OS keychain

## Tasks
See: `docs/tasks/data_mode_infra_tasks.csv` for the detailed task list (T-30..T-49).

## Notes
- Place firmware scaffolding under `firmware/datamode/` to avoid affecting Arduino builds
- JS stubs for Electron app live under `src/lib/datamode/`
- Everything starts as stubs with TODOs and unit-testable helpers
