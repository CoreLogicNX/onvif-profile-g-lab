# ONVIF Profile G troubleshooting checklist

## Step 1 — Confirm service discovery

Record model, firmware, ONVIF user privileges, device time and `GetServices` output. Check that Recording and Replay endpoints are advertised and reachable. A marketing claim of Profile G is not a substitute for operation-level testing.

## Step 2 — Verify the correct token

Call Recording Control `GetRecordings`. Use its `RecordingToken` with Replay `GetReplayUri`. Do not pass the Media `ProfileToken` or the Search `SearchToken`. After reboot or configuration changes, rediscover tokens rather than assuming they persist.

## Step 3 — Inspect SOAP faults

Capture a sanitized request/response. Distinguish `ActionNotSupported`, `InvalidArgVal`/invalid token, authorization failure and network timeout. Compare with the exact WSDL and firmware; SOAP fault strings differ by vendor.

## Step 4 — Verify RTSP independently

If `GetReplayUri` returns a URI, test it with an authorized RTSP client. Check DNS/IP reachability, RTSP authentication, `DESCRIBE` SDP, `SETUP` transport and `PLAY` response. A successful DESCRIBE alone does not prove playback works.

## Step 5 — Verify time-based replay

Confirm the NVR has recording for the requested interval. Compare camera/NVR/client clock, timezone and UTC conversion. Use an ONVIF-aware RTSP client that sends the appropriate replay `Range` and `Require` headers. FFprobe is only a basic endpoint probe.

## Step 6 — Capture safe evidence

Share: firmware version, advertised services, sanitized SOAP fault, RTSP status codes, requested UTC range, and whether playback works in the vendor client. Redact IPs, passwords, cookies, session IDs, customer identifiers and URI query tokens before posting publicly.

## Decision tree

```text
Does GetServices advertise Recording + Replay?
  No  -> Check firmware, ONVIF account and supported profiles.
  Yes -> Does GetRecordings return a RecordingToken?
           No  -> Check recording configuration, rights and service support.
           Yes -> Does GetReplayUri return a URI?
                    No  -> Check token type, SOAP fault and Replay endpoint.
                    Yes -> Does RTSP SETUP/PLAY succeed?
                             No  -> Check auth, transport and replay headers.
                             Yes -> Does requested UTC interval have video?
                                      No  -> Check clock/range/recording gaps.
                                      Yes -> Record successful integration evidence.
```
