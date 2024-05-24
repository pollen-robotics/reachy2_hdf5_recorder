import argparse
import time

import cv2
import h5py
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

reachy = ReachySDK("localhost")
data = h5py.File(args.episode, "r")
reachy.turn_on()
time.sleep(1)

# start = time.time()
for i in range(len(data["/action"])):
    action = data["/action"][i]
    image_id = data["/observations/images_ids/cam_trunk"][i]

    # image = cv2.imdecode(data["/observations/images/cam_trunk"][i], cv2.IMREAD_COLOR)

    reachy.head.neck.roll.goal_position = action[0]
    reachy.head.neck.pitch.goal_position = action[1]
    reachy.head.neck.yaw.goal_position = action[2]

    reachy.l_arm.shoulder.pitch.goal_position = action[3]
    reachy.l_arm.shoulder.roll.goal_position = action[4]
    reachy.l_arm.elbow.yaw.goal_position = action[5]
    reachy.l_arm.elbow.pitch.goal_position = action[6]
    reachy.l_arm.wrist.roll.goal_position = action[7]
    reachy.l_arm.wrist.pitch.goal_position = action[8]
    reachy.l_arm.wrist.yaw.goal_position = action[9]

    reachy.r_arm.shoulder.pitch.goal_position = action[10]
    reachy.r_arm.shoulder.roll.goal_position = action[11]
    reachy.r_arm.elbow.yaw.goal_position = action[12]
    reachy.r_arm.elbow.pitch.goal_position = action[13]
    reachy.r_arm.wrist.roll.goal_position = action[14]
    reachy.r_arm.wrist.pitch.goal_position = action[15]
    reachy.r_arm.wrist.yaw.goal_position = action[16]

    reachy.r_arm.gripper.set_opening(action[17])
    reachy.l_arm.gripper.set_opening(action[18])

    cv2.imshow("image", image)
    cv2.waitKey(1)

    time.sleep(0.01)
