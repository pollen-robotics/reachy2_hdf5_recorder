import argparse
import os
import time
from glob import glob

import cv2
import h5py
import numpy as np
from pollen_vision.camera_wrappers.depthai import SDKWrapper
from pollen_vision.camera_wrappers.depthai.utils import get_config_file_path
from reachy2_sdk import ReachySDK

parser = argparse.ArgumentParser("Record teleop episodes")
parser.add_argument(
    "-n",
    "--session-name",
    type=str,
    required=True,
)
parser.add_argument(
    "-r",
    "--sampling_rate",
    type=int,
    required=False,
    default=30,
    help="Sampling rate in Hz",
)
parser.add_argument(
    "-l",
    "--episode-length",
    type=int,
    required=False,
    default=10,
    help="Episode length in seconds",
)
parser.add_argument(
    "-ip",
    "--robot_ip",
    type=str,
    required=False,
    default="localhost",
    help="Robot IP address (default: localhost)",
)
args = parser.parse_args()

session_name = args.session_name + "_raw"
session_path = os.path.join("data", session_name)
os.makedirs(session_path, exist_ok=True)

episode_id = len(glob(f"{session_path}/*.hdf5"))

episode_path = os.path.join(session_path, f"episode_{episode_id}.hdf5")


# TODO these jpeg images are way too large
cam = SDKWrapper(get_config_file_path("CONFIG_SR"), jpeg_output=True)

reachy = ReachySDK(args.robot_ip)

time.sleep(1)

camera_names = ["cam_trunk"]

data_dict = {
    "/action": [],
    "/observations/qpos": [],
}

for camera_name in camera_names:
    data_dict[f"/observations/images/{camera_name}"] = []

current_episode_length = 0
start = time.time()
print("Recording ...")
elapsed = 0
while time.time() - start < args.episode_length:
    t = time.time() - start
    took_start = time.time()

    cam_data, _, _ = cam.get_data()

    left_rgb = cam_data["left"]
    # right_rgb = cam_data["right"]

    action = {
        "head_roll": reachy.head.neck.roll.goal_position,
        "head_pitch": reachy.head.neck.pitch.goal_position,
        "head_yaw": reachy.head.neck.yaw.goal_position,
        "l_arm_shoulder_pitch": reachy.l_arm.shoulder.pitch.goal_position,
        "l_arm_shoulder_roll": reachy.l_arm.shoulder.roll.goal_position,
        "l_arm_elbow_yaw": reachy.l_arm.elbow.yaw.goal_position,
        "l_arm_elbow_pitch": reachy.l_arm.elbow.pitch.goal_position,
        "l_arm_wrist_roll": reachy.l_arm.wrist.roll.goal_position,
        "l_arm_wrist_pitch": reachy.l_arm.wrist.pitch.goal_position,
        "l_arm_wrist_yaw": reachy.l_arm.wrist.yaw.goal_position,
        "r_arm_shoulder_pitch": reachy.r_arm.shoulder.pitch.goal_position,
        "r_arm_shoulder_roll": reachy.r_arm.shoulder.roll.goal_position,
        "r_arm_elbow_yaw": reachy.r_arm.elbow.yaw.goal_position,
        "r_arm_elbow_pitch": reachy.r_arm.elbow.pitch.goal_position,
        "r_arm_wrist_roll": reachy.r_arm.wrist.roll.goal_position,
        "r_arm_wrist_pitch": reachy.r_arm.wrist.pitch.goal_position,
        "r_arm_wrist_yaw": reachy.r_arm.wrist.yaw.goal_position,
        "r_gripper": reachy.r_arm.gripper.opening,
        "l_gripper": reachy.l_arm.gripper.opening,
    }

    qpos = {
        "head_roll": reachy.head.neck.roll.present_position,
        "head_pitch": reachy.head.neck.pitch.present_position,
        "head_yaw": reachy.head.neck.yaw.present_position,
        "l_arm_shoulder_pitch": reachy.l_arm.shoulder.pitch.present_position,
        "l_arm_shoulder_roll": reachy.l_arm.shoulder.roll.present_position,
        "l_arm_elbow_yaw": reachy.l_arm.elbow.yaw.present_position,
        "l_arm_elbow_pitch": reachy.l_arm.elbow.pitch.present_position,
        "l_arm_wrist_roll": reachy.l_arm.wrist.roll.present_position,
        "l_arm_wrist_pitch": reachy.l_arm.wrist.pitch.present_position,
        "l_arm_wrist_yaw": reachy.l_arm.wrist.yaw.present_position,
        "r_arm_shoulder_pitch": reachy.r_arm.shoulder.pitch.present_position,
        "r_arm_shoulder_roll": reachy.r_arm.shoulder.roll.present_position,
        "r_arm_elbow_yaw": reachy.r_arm.elbow.yaw.present_position,
        "r_arm_elbow_pitch": reachy.r_arm.elbow.pitch.present_position,
        "r_arm_wrist_roll": reachy.r_arm.wrist.roll.present_position,
        "r_arm_wrist_pitch": reachy.r_arm.wrist.pitch.present_position,
        "r_arm_wrist_yaw": reachy.r_arm.wrist.yaw.present_position,
        "r_gripper": reachy.r_arm.gripper.opening,  # replace by reachy.r_arm.gripper._goal_position ? is this in % too ?
        "l_gripper": reachy.l_arm.gripper.opening,  # replace by reachy.r_arm.gripper._goal_position ? is this in % too ?
    }

    data_dict["/action"].append(list(action.values()))
    data_dict["/observations/qpos"].append(list(qpos.values()))
    data_dict["/observations/images/cam_trunk"].append(list(left_rgb))

    took = time.time() - took_start
    if (1 / args.sampling_rate - took) < 0:
        print(f"Warning: frame took {took} seconds to record, expect frame drop")

    time.sleep(max(0, 1 / args.sampling_rate - took))

print("Done recording!")

# Pad the data to have the same length
# This assumes the images are compressed
print("Padding images ...")
for cam_name in camera_names:
    max_len = max([len(x) for x in data_dict[f"/observations/images/{cam_name}"]])
    for i in range(len(data_dict[f"/observations/images/{cam_name}"])):
        image = data_dict[f"/observations/images/{cam_name}"][i]
        if len(image) < max_len:
            pad = np.zeros(max_len - len(image), dtype="uint8")
            data_dict[f"/observations/images/{cam_name}"][i].extend(list(pad))


print(f"Saving episode in {episode_path} ...")
max_timesteps = len(data_dict["/action"])
with h5py.File(
    episode_path,
    "w",
    rdcc_nbytes=1024**2 * 2,
) as root:
    root.attrs["compress"] = True
    obs = root.create_group("observations")
    image = obs.create_group("images")
    for cam_name in camera_names:
        padded_size = max(
            [len(x) for x in data_dict[f"/observations/images/{cam_name}"]]
        )

        _ = image.create_dataset(
            cam_name,
            (max_timesteps, padded_size),
            dtype="uint8",
            chunks=(1, padded_size),
        )
    qpos = obs.create_dataset("qpos", (max_timesteps, 19))
    action = root.create_dataset("action", (max_timesteps, 19))

    for name, array in data_dict.items():
        root[name][...] = array

print("Saved!")
