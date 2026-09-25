from types import SimpleNamespace as NS
import pytest
from onvif_profile_g.core import discover_recordings, get_replay_uri, redact_uri, explain_failure
from onvif_profile_g.cli import build_parser

class FakeRecording:
    def GetRecordings(self):
        return [NS(RecordingToken="rec-123", Configuration=NS(Source="cam-1")),
                NS(RecordingToken="rec-456", Configuration=None)]

class FakeReplay:
    def __init__(self): self.request = None
    def create_type(self, name):
        assert name == "GetReplayUri"
        return NS(RecordingToken=None, StreamSetup=None)
    def GetReplayUri(self, req):
        self.request = req
        return NS(Uri="rtsp://device.example/recording")

class FakeCamera:
    def __init__(self): self.replay = FakeReplay()
    def create_recording_service(self): return FakeRecording()
    def create_replay_service(self): return self.replay

def test_recording_discovery():
    assert [r.token for r in discover_recordings(FakeCamera())] == ["rec-123", "rec-456"]

def test_replay_request_uses_recording_token():
    camera = FakeCamera()
    assert get_replay_uri(camera, "rec-123") == "rtsp://device.example/recording"
    assert camera.replay.request.RecordingToken == "rec-123"
    assert camera.replay.request.StreamSetup["Transport"]["Protocol"] == "RTSP"

def test_empty_token():
    with pytest.raises(ValueError): get_replay_uri(FakeCamera(), "")

def test_redaction():
    assert redact_uri("rtsp://user:secret@192.0.2.1:554/play?token=abc") == "rtsp://***:***@192.0.2.1:554/play"

def test_failure_hint():
    assert "GetRecordings" in explain_failure(Exception("Invalid recording token"))

def test_cli_defaults():
    args = build_parser().parse_args(["--host", "192.0.2.1"])
    assert args.port == 80 and args.index == 0
