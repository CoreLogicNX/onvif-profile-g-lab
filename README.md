# ONVIF Profile G — Recording Discovery & RTSP Replay Diagnostics

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

A **technical demonstration** for CCTV, NVR and third-party VMS integrators. It shows how to discover ONVIF services, list `RecordingToken` values, request a replay URI and optionally test the returned RTSP endpoint with FFprobe. The implementation is vendor-neutral **in intent**, but actual compatibility depends on device firmware, ONVIF services and WSDL/client versions. **Not validated against a physical NVR.**

> Only connect to devices you own or are authorized to test. Do not publish device credentials, live RTSP links or customer network details.

## Why live view can work while playback fails

Live video usually uses the ONVIF Media service (`GetStreamUri`) and a **Media ProfileToken**. Recorded-video replay uses **RecordingToken** values from Recording Control and the Replay service (`GetReplayUri`). An NVR can support the first without fully implementing the second. Search-session tokens are a third, unrelated token type.

```text
ONVIF Device Service: GetServices
             |
             v
Recording Control: GetRecordings -> RecordingToken
             |
             v
Replay Service: GetReplayUri(RecordingToken, StreamSetup)
             |
             v
RTSP endpoint: DESCRIBE -> SETUP -> PLAY [Range: clock=...] -> TEARDOWN
```

`GetReplayUri` returning a URI is **not** proof that playback succeeds. For actual time-range replay, the RTSP client must support ONVIF replay semantics, including the `onvif-replay` feature tag and appropriate `Range` headers. FFprobe below is a **connectivity/stream probe**, not a complete Profile G conformance test.

## Repository layout

```text
src/onvif_profile_g/core.py    # service discovery, recording tokens, replay URI
src/onvif_profile_g/cli.py     # command-line client and optional FFprobe
src/onvif_profile_g/__main__.py
examples/soap_requests.xml    # illustrative SOAP bodies
examples/sample_output.txt    # synthetic example; no customer data
docs/TECHNICAL_GUIDE.md       # service flow and token explanation
docs/TROUBLESHOOTING.md       # systematic diagnosis
docs/LINKEDIN_POST.md         # caption to accompany your carousel
tests/test_core.py            # offline mock tests
```

## Installation (Windows / Linux)

Install Python 3.10+ and, optionally, FFmpeg (for `ffprobe`).

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest -q
```

Linux/macOS: `source .venv/bin/activate` instead of the Windows activation command.

`onvif-zeep` depends on ONVIF WSDL definitions. If your installation does not bundle a usable WSDL directory, download trusted WSDLs and supply `--wsdl PATH_TO_WSDL_DIRECTORY`. Ensure the directory contains the Recording and Replay WSDLs and their imports.

## Quick start

```powershell
# PowerShell: avoid putting the password in shell history
$env:ONVIF_USER="admin"
$env:ONVIF_PASSWORD=Read-Host "ONVIF password"

# Discover services and list recording tokens
onvif-profile-g --host 192.0.2.10 --port 80 --list-only

# Request a replay URI for the first recording; URI is redacted by default
onvif-profile-g --host 192.0.2.10 --index 0

# Optional RTSP endpoint probe (requires ffprobe in PATH)
onvif-profile-g --host 192.0.2.10 --index 0 --ffprobe

# Explicitly choose a RecordingToken discovered from the SAME NVR
onvif-profile-g --host 192.0.2.10 --token 'recording-123'
```

Replace `192.0.2.10` (documentation-only address) with your authorized NVR's IP. Without `ONVIF_PASSWORD`, the CLI prompts interactively. Avoid `--show-uri` when sharing terminal output; even redacted output can expose internal hostnames and recording paths.

### FFprobe limitations

- Some NVRs require RTSP Digest/Basic authentication separate from ONVIF SOAP authentication. The CLI does **not** automatically insert credentials into the URI.
- FFprobe may fail on replay-specific streams even when a compliant ONVIF playback client succeeds. Verify the device's documented RTSP replay behavior.
- To test a specific recording interval, use an ONVIF-compatible RTSP client that sends UTC `Range: clock=...` and `Require: onvif-replay` when required. See `docs/TECHNICAL_GUIDE.md`.
- The code does not download recordings, perform export, bypass TLS certificate verification, or claim Profile G conformance.

## Common errors

| Symptom | Investigation |
|---|---|
| `InvalidToken` | Verify token came from `GetRecordings` on the same NVR, not `GetProfiles` or search session. |
| No recordings returned | Check recording status, user permissions and Recording service implementation. |
| Replay operation missing | Inspect `GetServices` for Replay service XAddr and operation support. |
| URI returned; RTSP 401 | Check RTSP credentials/auth scheme. |
| URI returned; RTSP 404/454 | Check endpoint validity, session state and device replay implementation. |
| No frames at requested time | Check UTC range, NVR clock, recording availability and RTSP replay support. |

See [Technical Guide](docs/TECHNICAL_GUIDE.md) and [Troubleshooting](docs/TROUBLESHOOTING.md).

## Official references

- [ONVIF specifications](https://www.onvif.org/profiles/specifications/)
- [ONVIF Profile G](https://www.onvif.org/profiles/profile-g/)
- [ONVIF Core Specifications](https://www.onvif.org/specs/core/ONVIF-Core-Specification.pdf)

## Publishing to GitHub

Create an empty GitHub repository (for example `onvif-profile-g-lab`) and run from this directory:

```bash
git init
git add .
git commit -m "Initial ONVIF Profile G diagnostic example"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/onvif-profile-g-lab.git
git push -u origin main
```

Never commit real `.env`, `.pcap`, passwords, live RTSP URIs or customer IP addresses. Replace the license copyright placeholder with your chosen attribution before publication.
