import argparse
import time
from typing import Optional

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst
from gst_signalling.utils import find_producer_peer_id_by_name


class GstRecorder:
    def __init__(
        self,
        signalling_host: str,
        signalling_port: int,
        peer_id: Optional[str] = None,
        peer_name: Optional[str] = None,
    ) -> None:
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("webRTC-recorder")
        self.source = Gst.ElementFactory.make("webrtcsrc")

        if not self.pipeline:
            print("Pipeline could be created.")
            exit(-1)

        if not self.source:
            print(
                "webrtcsrc component could not be created. Please make sure that the plugin is installed \
                (see https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc)"
            )
            exit(-1)

        self.pipeline.add(self.source)

        if peer_id is None:
            peer_id = find_producer_peer_id_by_name(
                signalling_host, signalling_port, peer_name
            )
            print(f"found peer id: {peer_id}")

        self.source.connect("pad-added", self.webrtcsrc_pad_added_cb)
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

    def webrtcsrc_pad_added_cb(self, webrtcsrc: Gst.Element, pad: Gst.Pad) -> None:
        if pad.get_name().startswith("video"):  # type: ignore[union-attr]
            videodepay = Gst.ElementFactory.make("rtph264depay")
            assert videodepay is not None
            gdppay = Gst.ElementFactory.make("gdppay")
            assert gdppay is not None
            filesink = Gst.ElementFactory.make("filesink")
            assert filesink is not None
            filesink.set_property("location", f"{pad.get_name()}.gdp")

            self.pipeline.add(videodepay)
            self.pipeline.add(gdppay)
            self.pipeline.add(filesink)
            videodepay.link(gdppay)
            gdppay.link(filesink)
            pad.link(videodepay.get_static_pad("sink"))  # type: ignore[arg-type]

            videodepay.sync_state_with_parent()
            gdppay.sync_state_with_parent()
            filesink.sync_state_with_parent()
        elif pad.get_name().startswith("audio"):  # type: ignore[union-attr]
            audiodepay = Gst.ElementFactory.make("rtpopusdepay")
            assert audiodepay is not None
            gdppay = Gst.ElementFactory.make("gdppay")
            assert gdppay is not None
            filesink = Gst.ElementFactory.make("filesink")
            assert filesink is not None
            filesink.set_property("location", f"{pad.get_name()}.gdp")

            self.pipeline.add(audiodepay)
            self.pipeline.add(gdppay)
            self.pipeline.add(filesink)
            audiodepay.link(gdppay)
            gdppay.link(filesink)
            pad.link(audiodepay.get_static_pad("sink"))  # type: ignore[arg-type]

            audiodepay.sync_state_with_parent()
            gdppay.sync_state_with_parent()
            filesink.sync_state_with_parent()

    def __del__(self) -> None:
        Gst.deinit()

    def get_bus(self) -> Gst.Bus:
        return self.pipeline.get_bus()

    def record(self) -> None:
        # Start playing
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Error starting playback.")
            exit(-1)
        print("recording ... (ctrl+c to quit)")

    def stop(self) -> None:
        print("stopping")
        self.pipeline.send_event(Gst.Event.new_eos())
        self.pipeline.set_state(Gst.State.NULL)


def process_msg(bus: Gst.Bus) -> bool:
    msg = bus.timed_pop_filtered(10 * Gst.MSECOND, Gst.MessageType.ANY)
    if msg:
        if msg.type == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print(f"Error: {err}, {debug}")
            return False
        elif msg.type == Gst.MessageType.EOS:
            print("End-Of-Stream reached.")
            return False
        # else:
        #    print(f"Message: {msg.type}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="webrtc gstreamer simple recorder")
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Gstreamer signaling host"
    )
    parser.add_argument(
        "--signaling-port", default=8443, help="Gstreamer signaling port"
    )
    parser.add_argument(
        "--remote-producer-peer-id",
        type=str,
        help="producer peer_id",
    )
    parser.add_argument(
        "--remote-producer-peer-name",
        type=str,
        help="producer name",
    )

    args = parser.parse_args()

    if args.remote_producer_peer_id is None and args.remote_producer_peer_name is None:
        exit("You must set either remote_producer_peer_id or remote_producer_peer_name")

    recorder = GstRecorder(
        args.signaling_host,
        args.signaling_port,
        args.remote_producer_peer_id,
        args.remote_producer_peer_name,
    )
    recorder.record()

    # Wait until error or EOS
    bus = recorder.get_bus()
    try:
        while True:
            if not process_msg(bus):
                break

    except KeyboardInterrupt:
        print("User exit")
        time.sleep(1)
    finally:
        # Free resources
        recorder.stop()
        time.sleep(1)


if __name__ == "__main__":
    main()

time.sleep(1)

"""
This will create video_x.gdp streams. You can mux them using:
gst-launch-1.0 \
    mp4mux name=mux ! filesink location=recording.mp4 \
    filesrc location=video_0.gdp ! gdpdepay ! h264parse ! queue ! mux. \
    filesrc location=video_1.gdp ! gdpdepay ! h264parse ! queue ! mux. \
    filesrc location=audio_0.gdp ! gdpdepay ! opusparse ! queue ! mux.
"""
