#!/usr/bin/env python3
"""Subscribe to a Sahayak channel and count received playback audio frames.

Proves the backend voice broadcaster's PCM audio is actually delivered by Agora.
"""

import os
import sys
import time

sys.path.insert(
    0,
    "/Users/macbook/Desktop/sahayak-live/backend/classroom",
)
sys.path.insert(0, "/Users/macbook/Library/Python/3.14/lib/python/site-packages")

from agora.rtc.agora_base import (  # noqa: E402
    AudioProfileType,
    AudioScenarioType,
    AudioPublishType,
    AudioSubscriptionOptions,
    ClientRoleType,
    ChannelProfileType,
    RTCConnConfig,
    RtcConnectionPublishConfig,
    VideoPublishType,
)
from agora.rtc.audio_frame_observer import IAudioFrameObserver  # noqa: E402
from agora.rtc.agora_service import AgoraService, AgoraServiceConfig  # noqa: E402

APP_ID = os.environ["AGORA_APP_ID"]
CERT = os.environ["AGORA_APP_CERTIFICATE"]
CHANNEL = os.environ.get("CHANNEL", "sahayak-audiotest2")
UID = os.environ.get("SUB_UID", "777001")
DURATION = float(os.environ.get("DURATION", "25"))

from agora_token_builder import RtcTokenBuilder  # noqa: E402

frames = []
samples_total = {"n": 0}


class Observer(IAudioFrameObserver):
    def on_playback_audio_frame(self, agora_local_user, channelId, frame):
        samples_total["n"] += frame.samples_per_channel
        frames.append(time.time())
        return 0


def main():
    token = RtcTokenBuilder.buildTokenWithUid(APP_ID, CERT, CHANNEL, int(UID), 1, int(time.time()) + 3600)

    conn_conf = RTCConnConfig(
        client_role_type=ClientRoleType.CLIENT_ROLE_BROADCASTER,
        channel_profile=ChannelProfileType.CHANNEL_PROFILE_LIVE_BROADCASTING,
        auto_subscribe_audio=1,
        audio_subs_options=AudioSubscriptionOptions(
            packet_only=0,
            pcm_data_only=0,
            bytes_per_sample=2,
            number_of_channels=1,
            sample_rate_hz=16000,
        ),
    )
    pub_conf = RtcConnectionPublishConfig(
        audio_profile=AudioProfileType.AUDIO_PROFILE_DEFAULT,
        audio_scenario=AudioScenarioType.AUDIO_SCENARIO_AI_SERVER,
        is_publish_audio=False,
        is_publish_video=False,
        audio_publish_type=AudioPublishType.AUDIO_PUBLISH_TYPE_PCM,
        video_publish_type=VideoPublishType.VIDEO_PUBLISH_TYPE_NONE,
    )

    cfg = AgoraServiceConfig()
    cfg.appid = APP_ID
    svc = AgoraService()
    svc.initialize(cfg)

    conn = svc.create_rtc_connection(conn_conf, pub_conf)
    rc = conn.connect(token, CHANNEL, UID)
    print(f"connect rc={rc}", flush=True)
    if rc != 0:
        sys.exit(1)

    lu = conn.get_local_user()
    lu.set_playback_audio_frame_parameters(1, 16000, 2, 960)
    observer = Observer()
    lu._register_audio_frame_observer(observer, 0, None)
    print("observer registered", flush=True)

    deadline = time.time() + DURATION
    while time.time() < deadline:
        time.sleep(0.5)
        if samples_total["n"] > 0:
            print(f"received samples so far: {samples_total['n']}", flush=True)

    print(f"FINAL samples={samples_total['n']} (~{samples_total['n'] / 16000:.2f}s audio) over {DURATION}s", flush=True)

    try:
        conn.disconnect()
        conn.release()
        svc.release()
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()