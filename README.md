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

## TODO
Record teleop cameras with gstreamer