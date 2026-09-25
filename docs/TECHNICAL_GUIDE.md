# Technical guide: ONVIF Profile G recording and replay

## 1. Scope

Profile G addresses recording, search and replay. Live streaming through a Media profile is a separate workflow. A device may advertise endpoints yet fail a particular operation; test each operation independently.

## 2. Tokens are not interchangeable

| Token | Obtained from | Purpose |
|---|---|---|
| Media `ProfileToken` | Media `GetProfiles` | Live `GetStreamUri` |
| `RecordingToken` | Recording `GetRecordings` or Recording Search results | Replay `GetReplayUri` |
| `SearchToken` | Search `FindRecordings` | Poll `GetRecordingSearchResults`, then `EndSearch` |

Recording Search is **optional for this example**: `GetRecordings` is the simpler discovery path. For time-filtered discovery, implement `FindRecordings` → `GetRecordingSearchResults` → `EndSearch` using your device's WSDL and check the resulting recording tokens and time ranges.

## 3. SOAP operation sequence

1. `GetServices(IncludeCapability=True)` to inspect advertised service namespaces and XAddr values.
2. `GetRecordings()` on the Recording Control service. Select a returned `RecordingToken`.
3. `GetReplayUri(RecordingToken, StreamSetup)` on the Replay service, typically requesting RTP unicast over RTSP.
4. Parse the returned URI; establish a separate RTSP session and authenticate as needed.
5. For time-specific playback, use an ONVIF-aware RTSP client capable of the device's required replay headers, UTC clock ranges and scale support.

## 4. RTSP handshake

```text
Client                                    NVR
  |---- DESCRIBE rtsp://... --------------->|
  |<--- 200 OK + SDP ----------------------|
  |---- SETUP (Transport: RTP/AVP/TCP) --->|
  |<--- 200 OK + Session ------------------|
  |---- PLAY + Range: clock=... ---------->|
  |<--- 200 OK / RTP media ----------------|
  |---- TEARDOWN -------------------------->|
```

ONVIF replay commonly uses `Require: onvif-replay` on RTSP replay requests. The exact negotiated transport and required headers depend on device implementation. Use UTC for absolute clock ranges. Example `Range: clock=20260925T080000Z-20260925T081000Z` is illustrative, not proof that a recording exists then.

## 5. Security and operational limits

- The example never disables TLS certificate verification. If an HTTPS endpoint has a private CA, install its trusted CA instead of globally bypassing validation.
- Some clients and NVRs require WS-Security username tokens and synchronized clocks. Authentication behavior depends on firmware.
- The CLI redacts URI userinfo and query strings by default, but the recording tokens and service endpoints may still be sensitive. Sanitize logs before sharing.
- No automatic RTSP credential injection is implemented. Use a secure player configuration for RTSP authentication.
- Device service port (often 80/443) and RTSP port (often 554) are distinct; discover rather than assume.

## 6. Limits of this implementation

`GetRecordings` may not provide per-interval metadata. This tool does not implement time-based `FindRecordings`, RTSP Range playback, `GetReplayConfiguration`, export/download or ONVIF conformance certification. Its mock tests validate client logic, not hardware compatibility. Verify WSDL support and device responses on your specific NVR.
