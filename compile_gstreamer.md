Clone gstreamer version 1.22.8 https://gitlab.freedesktop.org/gstreamer/gstreamer.git

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends flex bison libasound2-dev alsa-utils \
    python3-tomli ninja-build libffi7 ssh libx11-dev libxv-dev libxt-dev nasm libgl1 libwebrtc-audio-processing-dev \
    libgirepository1.0-dev libsrtp2-dev libcairo2-dev
```

```bash
sudo pip install -U pip
```

```bash
sudo pip install meson 
```

Install Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y
```

```bash
cargo install cargo-c
```


```bash
./fix-rs-plugin-version.sh <...>/gstreamer/
```

```bash
cd <...>/gstreamer # cloned repo
```

(You can add `--prefix=/opt/gstreamer` (for example) if you want to control where this is installed)

```bash
meson setup --buildtype=release -Dauto_features=disabled -Dgstreamer:tools=enabled \
                    -Dtools=enabled -Drs=enabled -Dgst-plugins-rs:webrtc=enabled \
                    -Drs:webrtc=enabled -Dlibnice=enabled -Dlibnice:gstreamer=enabled \
                    -Dintrospection=enabled -Dgst-plugins-bad:webrtc=enabled \
                    -Dgst-plugins-bad:webrtcdsp=enabled -Dgst-plugins-bad:videoparsers=enabled \
                    -Dgst-plugins-bad:audiolatency=enabled -Dgpl=enabled -Dgst-plugins-bad:sctp=enabled\
                    -Dgst-plugins-base:alsa=enabled -Dgst-plugins-base:playback=enabled \
                    -Dgst-plugins-base:app=enabled -Dbad=enabled -Dgst-plugins-base:opus=enabled \
                    -Dgst-plugins-bad:opus=enabled -Dgood=enabled -Dgst-plugins-good:rtpmanager=enabled \
                    -Dgst-plugins-good:rtp=enabled -Dgst-plugins-bad:rtp=enabled -Dgst-plugins-bad:srtp=enabled \
                    -Dgst-plugins-rs:rtp=enabled -Dgst-plugins-bad:dtls=enabled -Dgst-plugins-base:audioresample=enabled -Dgst-plugins-base:audioconvert=enabled \
                    -Dgst-plugins-base:audiotestsrc=enabled -Dgst-plugins-base:audiomixer=enabled -Dgst-plugins-base:videotestsrc=enabled -Dgst-plugins-base:playback=enabled\
                    -Dgst-plugins-ugly:x264=enabled -Dgst-plugins-base:videoconvertscale=enabled -Dgst-plugins-good:autodetect=enabled\
                    -Dgst-plugins-base:xvideo=enabled -Dgst-plugins-base:x11=enabled -Dgst-plugins-bad:openh264=enabled -Dgst-plugins-good:matroska=enabled\
                    -Dgst-plugins-bad:gdp=enabled\
                    -Dgst-plugins-good:isomp4=enabled\
                    builddir/
```

```bash
meson compile -C builddir
```

```bash
meson install -C builddir
```

Set the environment variables
```bash
GST_PLUGIN_PATH /<path_to_installed_gstreamer>/lib/x86_64-linux-gnu/:\$GST_PLUGIN_PATH" >> ~/.bashrc
LD_LIBRARY_PATH /<path_to_installed_gstreamer>/lib/x86_64-linux-gnu/:\$LD_LIBRARY_PATH" >> ~/.bashrc
GI_TYPELIB_PATH /<path_to_installed_gstreamer>/lib/x86_64-linux-gnu/girepository-1.0:\$GI_TYPELIB_PATH" >> ~/.bashrc
```

<path_to_installed_gstreamer> can be `/usr/local/` if you didn't specify a prefix in the meson setup command.

Test the installation 

```bash
gst-inspect-1.0 --version
```

You should get 

```
gst-inspect-1.0 version 1.22.8
GStreamer 1.22.8
```

```bash
gst-inspect-1.0 webrtcsrc
```

You should get a lot of stuff :)

