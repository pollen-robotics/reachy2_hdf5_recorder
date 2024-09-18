# Reachy2 hdf5 recorder

Records through SDK.

Warning : Reachy1 script may not work out of the box

## Installation

```bash
pip install -r requirements.txt
```

## Usage

To launch a recording session :

```bash
python3 <reachy1/reachy2>_record_episode_hdf5.py -n <session_name> -l <episode_length> --robot_ip <robot_ip> (--gripper_input)
```

All recordings will be saved in `./data/<session_name/>`

For a given session, the script will create new episodes each time it is called in `./data/<session_name>/episode_<episode_number>.hdf5`

`--gripper_input` allows you to use the right gripper to trigger the start of the recording. Close the right gripper for 2 seconds to start the recording.

The script will play different sounds to indicate its state.

- three short beeps when it's ready to record
- a long beep when the recording starts
- two short beeps when the recording stops
