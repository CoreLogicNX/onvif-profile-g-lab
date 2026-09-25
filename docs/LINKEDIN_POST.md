# LinkedIn caption

**ONVIF Profile G: Why Does Live Streaming Work but Recording Playback Fail?**

A successful ONVIF connection doesn't guarantee complete interoperability between an NVR and a third-party VMS.

In this technical walkthrough, I explore the complete troubleshooting path:

- Discover ONVIF Recording and Replay services.
- Retrieve a valid `RecordingToken`.
- Request a replay URI using `GetReplayUri`.
- Diagnose SOAP faults and inspect the RTSP `DESCRIBE → SETUP → PLAY` handshake.
- Validate UTC recording ranges and distinguish connectivity from successful playback.

I've also prepared a Python demonstration, sample SOAP requests and a troubleshooting checklist. The code is educational and should be validated on each target NVR before production use.

**GitHub:** https://github.com/YOUR_USERNAME/onvif-profile-g-lab

Have you encountered invalid recording tokens or replay failures in third-party VMS integration?

#ONVIF #ONVIFProfileG #RTSP #CCTV #VMS #Python #VideoSurveillance #NVR #SystemIntegration #NetworkEngineering #Troubleshooting
