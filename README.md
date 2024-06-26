# Reachy2 hdf5 recorder

Records through SDK. 
Right now there are issues with the trunk camera, so it needs to be plugged to the computer running the script.

## Installation

```bash
pip install -r requirements.txt
```

Not available on pypi, so you need to install the following packages manually:
- pollen-vision on branch develop https://github.com/pollen-robotics/pollen-vision, only extra [depthai_wrapper] needed
- reachy2_sdk https://github.com/pollen-robotics/reachy2-sdk
- install https://github.com/pollen-robotics/gst-signalling-py

## For gstreamer stuff
If on ubuntu 22.04, [compile gstreamer](gstreamer_stuff/compile_gstreamer.md) manually to have the right version : 1.22.8

On higher versions of ubuntu, you can install gstreamer through apt https://gstreamer.freedesktop.org/documentation/installing/on-linux.html?gi-language=c

TODO list plugins to install


## Usage
    
```bash
python3 <reachy1/reachy2>_record_episode_hdf5.py -n <session_name> -l <episode_length> --robot_ip <robot_ip>
```

All recordings will be saved in `./data/<session_name/>`

For a given session, the script will create new episodes each time it is called in `./data/<session_name/episode_<episode_number>.hdf5`

