"""ONVIF Profile G discovery and replay diagnostics.

This example deliberately uses service operations, not a guessed vendor RTSP URL.
A recording token is NOT a live Media ProfileToken or search-session token.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class Recording:
    token: str
    source: str


def redact_uri(uri: str) -> str:
    """Avoid exposing userinfo and query parameters in logs or screenshots."""
    parts = urlsplit(uri)
    hostname = parts.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = hostname + (f":{parts.port}" if parts.port else "")
    if parts.username or parts.password:
        netloc = "***:***@" + netloc
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def service_summary(camera: Any) -> list[dict[str, str]]:
    """List advertised ONVIF services; availability != functional conformance."""
    result = []
    for svc in camera.devicemgmt.GetServices({"IncludeCapability": True}):
        result.append({
            "namespace": str(getattr(svc, "Namespace", "")),
            "xaddr": str(getattr(svc, "XAddr", "")),
        })
    return result


def discover_recordings(camera: Any) -> list[Recording]:
    """Use Recording Control GetRecordings; no recording-search token confusion."""
    service = camera.create_recording_service()
    raw = service.GetRecordings()
    result = []
    for item in raw or []:
        token = getattr(item, "RecordingToken", None)
        if not token:
            continue
        cfg = getattr(item, "Configuration", None)
        source = getattr(cfg, "Source", None) if cfg is not None else None
        result.append(Recording(str(token), str(source) if source is not None else ""))
    return result


def get_replay_uri(camera: Any, recording_token: str, transport: str = "RTSP") -> str:
    if not recording_token:
        raise ValueError("A nonempty RecordingToken is required")
    replay = camera.create_replay_service()
    req = replay.create_type("GetReplayUri")
    req.RecordingToken = recording_token
    req.StreamSetup = {"Stream": "RTP-Unicast", "Transport": {"Protocol": transport}}
    response = replay.GetReplayUri(req)
    uri = getattr(response, "Uri", None)
    if not uri:
        raise RuntimeError("Replay service returned no URI")
    return str(uri)


def explain_failure(exc: Exception) -> str:
    """Offer investigation steps, never assert a root cause from one exception."""
    message = str(exc)
    lower = message.lower()
    if "token" in lower or "invalidargval" in lower:
        return ("Check that the token came from GetRecordings on this NVR, "
                "not GetProfiles or a recording-search session. Re-discover after reboot; "
                "inspect the exact SOAP fault and permissions.")
    if "401" in lower or "notauthorized" in lower or "unauthorized" in lower:
        return "Check ONVIF account permissions, credentials and device/client clock synchronization."
    if "404" in lower or "actionnotsupported" in lower:
        return "Confirm the device advertises the Recording and Replay service endpoints and implements the requested operation."
    if "timeout" in lower or "connection" in lower:
        return "Check routing, service XAddr reachability, firewall, port and TLS settings."
    return "Capture the SOAP fault, device model/firmware and service capabilities; inspect the response before drawing conclusions."
