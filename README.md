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

If on ubuntu 22.04, [compile gstreamer](compile_gstreamer.md) manually to have the right version : 1.22.8


## Usage
    
```bash
python3 record_episode_hdf5.py -n <session_name> -l <episode_length> --robot_ip <robot_ip>
```

All recordings will be saved in `./data/<session_name/>`

For a given session, the script will create new episodes each time it is called in `./data/<session_name/episode_<episode_number>.hdf5`



## TODO
- Record teleop cameras with gstreamer
- Ensure synchronization (run everything on the robot ?)