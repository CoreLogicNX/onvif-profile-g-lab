"""CLI for a lab NVR you are authorized to test."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

from .core import discover_recordings, explain_failure, get_replay_uri, redact_uri, service_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ONVIF Profile G recording/replay diagnostic")
    parser.add_argument("--host", required=True, help="NVR IP address or hostname")
    parser.add_argument("--port", type=int, default=80, help="ONVIF device service port")
    parser.add_argument("--username", default=os.getenv("ONVIF_USER", "admin"))
    parser.add_argument("--token", help="Use a known RecordingToken; otherwise select from GetRecordings")
    parser.add_argument("--index", type=int, default=0, help="Zero-based recording index")
    parser.add_argument("--list-only", action="store_true", help="List advertised services and recordings")
    parser.add_argument("--show-uri", action="store_true", help="Reveal URI; may contain sensitive tokens")
    parser.add_argument("--ffprobe", action="store_true", help="Probe RTSP endpoint (requires ffprobe in PATH)")
    parser.add_argument("--rtsp-transport", choices=["tcp", "udp"], default="tcp")
    parser.add_argument("--wsdl", help="Local WSDL directory if your onvif-zeep installation needs it")
    return parser


def probe(uri: str, transport: str) -> int:
    if urlsplit(uri).scheme.lower() not in {"rtsp", "rtsps"}:
        print("Skipping ffprobe: returned URI is not RTSP/RTSPS", file=sys.stderr)
        return 2
    if not shutil.which("ffprobe"):
        print("ffprobe not found. Install FFmpeg and add its bin directory to PATH.", file=sys.stderr)
        return 2
    # URI is passed as a subprocess argument, never through a shell.
    # ffprobe may need separate authentication on devices that return unauthenticated URIs.
    cmd = ["ffprobe", "-v", "error", "-rtsp_transport", transport,
           "-show_entries", "stream=index,codec_name,codec_type", "-of", "json", uri]
    print("Running ffprobe (URI hidden)...")
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=25, check=False)
    except subprocess.TimeoutExpired:
        print("ffprobe timed out; check reachability and RTSP transport.", file=sys.stderr)
        return 2
    if completed.returncode:
        # Avoid printing raw stderr because ffprobe errors may echo credentialed URLs.
        print(f"ffprobe failed (exit {completed.returncode}); inspect locally with redacted logs.", file=sys.stderr)
        return completed.returncode
    print(completed.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.port <= 65535 or args.index < 0:
        print("Invalid port or recording index", file=sys.stderr)
        return 2
    password = os.getenv("ONVIF_PASSWORD")
    if password is None:
        password = getpass.getpass("ONVIF password (not displayed): ")
    try:
        from onvif import ONVIFCamera
        camera = ONVIFCamera(args.host, args.port, args.username, password,
                             wsdl_dir=args.wsdl) if args.wsdl else ONVIFCamera(
                                 args.host, args.port, args.username, password)
        print("Advertised services:")
        print(json.dumps(service_summary(camera), indent=2))
        recordings = discover_recordings(camera)
        print("Recording tokens:")
        for idx, rec in enumerate(recordings):
            print(f"  [{idx}] {rec.token}")
        if args.list_only:
            return 0
        if args.token:
            token = args.token
        elif recordings and args.index < len(recordings):
            token = recordings[args.index].token
        else:
            raise RuntimeError("No recording at that index; check --list-only or supply --token")
        uri = get_replay_uri(camera, token)
        print("Replay URI:", uri if args.show_uri else redact_uri(uri))
        if args.ffprobe:
            return probe(uri, args.rtsp_transport)
        print("URI returned. RTSP playback is NOT yet verified; use --ffprobe or VLC.")
        return 0
    except Exception as exc:
        # Some SOAP fault messages can contain sensitive request data. Do not print them verbatim.
        print(f"Diagnostic failed ({type(exc).__name__}). {explain_failure(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
