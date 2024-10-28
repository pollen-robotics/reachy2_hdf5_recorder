import argparse
import time
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

IP = "localhost"
# IP = "10.0.0.250"
reachy = ReachySDK(IP)
reachy.turn_on()

fake = IP == "localhost"


def get_action_list(action):
    """
    Converts from rad 2 deg
    """
    action_list = []

    for i, a in enumerate(action):
        if i == 7 or i == 15:
            pass
        elif i != 16 and i != 17:
            action_list.append(np.rad2deg(a))
        else:
            action_list.append(a)
    return action_list


data = h5py.File(args.episode, "r")

first_action = get_action_list(data["/action"][0])

reachy.l_arm.goto(first_action[:7], duration=5)
reachy.r_arm.goto(first_action[7 : 7 + 7], duration=5)
reachy.head.goto(first_action[17:], duration=5, wait=True)
if not fake:
    reachy.mobile_base.reset_odometry()

for i in range(len(data["/action"])):
    s = time.time()
    action = data["/action"][i]

    for cam_name in camera_names:
        _, image = caps[cam_name].read()
        cv2.imshow(cam_name, image)

    image_id = data["/observations/images_ids/cam_trunk"][i]
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

    reachy.head.neck.roll.goal_position = np.rad2deg(action[19]).astype(float)
    reachy.head.neck.pitch.goal_position = np.rad2deg(action[20]).astype(float)
    reachy.head.neck.yaw.goal_position = np.rad2deg(action[21]).astype(float)

    if not fake:
        reachy.mobile_base.set_goal_speed(
            float(action[16]), float(action[17]), float(np.rad2deg(action[18]))
        )
        reachy.mobile_base.send_speed_command()

    reachy.send_goal_positions(check_positions=False)

    # cv2.imshow("image", image)
    cv2.waitKey(1)

    took = time.time() - s

    time.sleep(max(0, (1 / freq) - took))
