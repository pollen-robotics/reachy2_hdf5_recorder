import argparse
import os
import time
from pathlib import Path

import cv2
import h5py
import numpy as np
from reachy2_sdk import ReachySDK

freq = 30

parser = argparse.ArgumentParser("Replay teleop episodes")
parser.add_argument(
    "-e",
    "--episode",
    type=str,
    required=True,
)
args = parser.parse_args()

episode_parent = Path(args.episode).parent
episode_id = Path(args.episode).stem
camera_names = ["cam_trunk", "cam_teleop"]
caps = {}
for cam_name in camera_names:
    caps[cam_name] = cv2.VideoCapture(
        os.path.join(episode_parent, f"{episode_id}_{cam_name}.mp4")
    )


# reachy = ReachySDK("192.168.1.51")
reachy = ReachySDK("localhost")
reachy.turn_on()

data = h5py.File(args.episode, "r")
# start = time.time()
for i in range(len(data["/action"])):
    action = data["/action"][i]
    for cam_name in camera_names:
        _, image = caps[cam_name].read()
        cv2.imshow(cam_name, image)
    # _, image = cap.read()
    image_id = data["/observations/images_ids/cam_trunk"][i]
    # image = cv2.imdecode(data["/observations/images/cam_trunk"][i], cv2.IMREAD_COLOR)
    reachy.l_arm.shoulder.pitch.goal_position = np.rad2deg(action[0]).astype(float)
    reachy.l_arm.shoulder.roll.goal_position = np.rad2deg(action[1]).astype(float)
    reachy.l_arm.elbow.yaw.goal_position = np.rad2deg(action[2]).astype(float)
    reachy.l_arm.elbow.pitch.goal_position = np.rad2deg(action[3]).astype(float)
    reachy.l_arm.wrist.roll.goal_position = np.rad2deg(action[4]).astype(float)
    reachy.l_arm.wrist.pitch.goal_position = np.rad2deg(action[5]).astype(float)
    reachy.l_arm.wrist.yaw.goal_position = np.rad2deg(action[6]).astype(float)
    reachy.l_arm.gripper.set_opening(min(100, max(0, action[7] / 2.26 * 100)))

    reachy.r_arm.shoulder.pitch.goal_position = np.rad2deg(action[8]).astype(float)
    reachy.r_arm.shoulder.roll.goal_position = np.rad2deg(action[9]).astype(float)
    reachy.r_arm.elbow.yaw.goal_position = np.rad2deg(action[10]).astype(float)
    reachy.r_arm.elbow.pitch.goal_position = np.rad2deg(action[11]).astype(float)
    reachy.r_arm.wrist.roll.goal_position = np.rad2deg(action[12]).astype(float)
    reachy.r_arm.wrist.pitch.goal_position = np.rad2deg(action[13]).astype(float)
    reachy.r_arm.wrist.yaw.goal_position = np.rad2deg(action[14]).astype(float)
    reachy.r_arm.gripper.set_opening(min(100, max(0, action[15] / 2.26 * 100)))

    reachy.send_goal_positions()
    # cv2.imshow("image", image)
    cv2.waitKey(1)

    # time.sleep(1 / 30)
