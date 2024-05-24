import argparse

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class GstRecorder:
    def __init__(
        self, signalling_host: str, signalling_port: int, peer_id: str
    ) -> None:
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("webRTC-recorder")
        source = Gst.ElementFactory.make("webrtcsrc")
        print(source)

        if not self.pipeline or not source:
            print("Not all elements could be created.")
            exit(-1)

        self.pipeline.add(source)

        source.connect("pad-added", self.webrtcsrc_pad_added_cb)
        signaller = source.get_property("signaller")
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
        required=True,
    )

    args = parser.parse_args()

    recorder = GstRecorder(
        args.signaling_host, args.signaling_port, args.remote_producer_peer_id
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
    finally:
        # Free resources
        recorder.stop()


if __name__ == "__main__":
    main()

"""
This will create video_x.gdp streams. You can mux them using:
gst-launch-1.0 \
    mp4mux name=mux ! filesink location=recording.mp4 \
    filesrc location=video_0.gdp ! gdpdepay ! h264parse ! queue ! mux. \
    filesrc location=video_1.gdp ! gdpdepay ! h264parse ! queue ! mux.
"""
