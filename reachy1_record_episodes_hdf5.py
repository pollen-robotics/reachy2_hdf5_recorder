import argparse
import os
import subprocess
import time
from glob import glob
from pathlib import Path
from queue import Queue
from threading import Thread

import cv2
import h5py
import numpy as np

# from reachy2_sdk import ReachySDK
from reachy_sdk import ReachySDK

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
    default="10.42.0.124",
    help="Robot IP address (default: localhost)",
)
args = parser.parse_args()

images_queue = Queue()


def write_images_to_disk_worker():
    while True:
        image, path = images_queue.get()
        cv2.imwrite(path, image)
        images_queue.task_done()


Thread(target=write_images_to_disk_worker, daemon=True).start()


session_name = args.session_name + "_raw"
session_path = os.path.join("data", session_name)
os.makedirs(session_path, exist_ok=True)


reachy = ReachySDK("10.42.0.124")
reachy.turn_off_smoothly("r_arm")
time.sleep(2)
reachy.turn_on("r_arm")
reachy.turn_on("head")
reachy.joints.neck_roll.goal_position = 0
reachy.joints.neck_pitch.goal_position = 0
reachy.joints.neck_yaw.goal_position = 0
reachy.turn_off("head")
camera_names = ["cam_trunk"]
try:
    while True:
        episode_id = len(glob(f"{session_path}/*.hdf5"))
        episode_path = os.path.join(session_path, f"episode_{episode_id}.hdf5")

        data_dict = {
            "/action": [],
            "/observations/qpos": [],
        }

        for camera_name in camera_names:
            data_dict[f"/observations/images_ids/{camera_name}"] = []
            os.makedirs(f"{session_path}/images_episode_{episode_id}", exist_ok=True)

        current_episode_length = 0
        os.system('spd-say "ready?"')
        time.sleep(1)
        os.system('spd-say "3"')
        time.sleep(1)
        os.system('spd-say "2"')
        time.sleep(1)
        os.system('spd-say "1"')
        time.sleep(1)
        os.system('spd-say "start"')
        print("Recording ...")
        elapsed = 0
        i = -1
        start = time.time()
        while time.time() - start < args.episode_length:
            i += 1
            t = time.time() - start
            took_start = time.time()
            left_rgb = reachy.right_camera.last_frame
            # TODO set reachy1 on the right branches to get this
            # mobile_base_action = reachy.mobile_base.last_cmd_vel
            # mobile_base_pos = reachy.mobile_base.odometry

            left_pos = {
                "l_shoulder_pitch": np.deg2rad(
                    reachy.joints.l_shoulder_pitch.present_position
                ),
                "l_shoulder_roll": np.deg2rad(
                    reachy.joints.l_shoulder_roll.present_position
                ),
                "l_arm_yaw": np.deg2rad(reachy.joints.l_arm_yaw.present_position),
                "l_elbow_pitch": np.deg2rad(
                    reachy.joints.l_elbow_pitch.present_position
                ),
                "l_forearm_yaw": -np.deg2rad(
                    reachy.joints.l_forearm_yaw.present_position
                ),
                "l_wrist_pitch": -np.deg2rad(
                    reachy.joints.l_wrist_pitch.present_position
                ),
                "l_wrist_roll": -np.deg2rad(
                    reachy.joints.l_wrist_roll.present_position
                ),
                "l_gripper": -reachy.joints.l_gripper.present_position,
                # "neck_roll": np.deg2rad(reachy.joints.neck_roll.present_position),
                # "neck_pitch": np.deg2rad(reachy.joints.neck_pitch.present_position),
                # "neck_yaw": np.deg2rad(reachy.joints.neck_yaw.present_position),
            }
            qpos = {
                "r_shoulder_pitch": np.deg2rad(
                    reachy.joints.r_shoulder_pitch.present_position
                ),
                "r_shoulder_roll": np.deg2rad(
                    reachy.joints.r_shoulder_roll.present_position
                ),
                "r_arm_yaw": np.deg2rad(reachy.joints.r_arm_yaw.present_position),
                "r_elbow_pitch": np.deg2rad(
                    reachy.joints.r_elbow_pitch.present_position
                ),
                "r_forearm_yaw": np.deg2rad(
                    reachy.joints.r_forearm_yaw.present_position
                ),
                "r_wrist_pitch": np.deg2rad(
                    reachy.joints.r_wrist_pitch.present_position
                ),
                "r_wrist_roll": np.deg2rad(reachy.joints.r_wrist_roll.present_position),
                "r_gripper": reachy.joints.r_gripper.present_position,
                # "mobile_base_vx": mobile_base_pos["vx"],
                # "mobile_base_vy": mobile_base_pos["vy"],
                # "mobile_base_vtheta": np.deg2rad(mobile_base_pos["vtheta"]),
                # "neck_roll": np.deg2rad(reachy.joints.neck_roll.present_position),
                # "neck_pitch": np.deg2rad(reachy.joints.neck_pitch.present_position),
                # "neck_yaw": np.deg2rad(reachy.joints.neck_yaw.present_position),
            }
            reachy.joints.r_shoulder_pitch.goal_position = np.rad2deg(
                left_pos["l_shoulder_pitch"]
            )
            reachy.joints.r_shoulder_roll.goal_position = np.rad2deg(
                left_pos["l_shoulder_roll"]
            )
            reachy.joints.r_arm_yaw.goal_position = np.rad2deg(left_pos["l_arm_yaw"])
            reachy.joints.r_elbow_pitch.goal_position = np.rad2deg(
                left_pos["l_elbow_pitch"]
            )
            reachy.joints.r_forearm_yaw.goal_position = np.rad2deg(
                left_pos["l_forearm_yaw"]
            )
            reachy.joints.r_wrist_pitch.goal_position = np.rad2deg(
                left_pos["l_wrist_pitch"]
            )
            reachy.joints.r_wrist_roll.goal_position = np.rad2deg(
                left_pos["l_wrist_roll"]
            )
            reachy.joints.r_gripper.goal_position = left_pos["l_gripper"]
            # reachy.joints.neck_roll.goal_position = 0
            # reachy.joints.neck_pitch.goal_position = 0
            # reachy.joints.neck_yaw.goal_position = 0

            took = time.time() - took_start
            data_dict["/action"].append(list(left_pos.values()))
            data_dict["/observations/qpos"].append(list(qpos.values()))
            data_dict["/observations/images_ids/cam_trunk"].append(i)

            images_queue.put(
                (
                    left_rgb,
                    f"{session_path}/images_episode_{episode_id}/cam_trunk_{i}.png",
                )
            )

            time.sleep(max(0, 1 / args.sampling_rate - took))
        os.system('spd-say "stop"')

        print("Done recording!")

        print(f"Saving episode in {episode_path} ...")
        max_timesteps = len(data_dict["/action"])
        with h5py.File(
            episode_path,
            "w",
            rdcc_nbytes=1024**2 * 2,
        ) as root:
            root.attrs["compress"] = True
            obs = root.create_group("observations")
            images_ids = obs.create_group("images_ids")
            for cam_name in camera_names:
                images_ids.create_dataset("cam_trunk", (max_timesteps,), dtype="int32")
            qpos = obs.create_dataset(
                "qpos", (max_timesteps, 8)
            )  # TODO change this to 22 when adding mobile base
            action = root.create_dataset(
                "action", (max_timesteps, 8)
            )  # TODO change this to 22 when adding mobile base

            for name, array in data_dict.items():
                root[name][...] = array

        print("Waiting for all images to be saved...")
        images_queue.join()  # Block until all tasks are done.

        def encode_video_frames(
            imgs_dir: Path, video_path: Path, fps: int, cam_name: str
        ):
            """More info on ffmpeg arguments tuning on `lerobot/common/datasets/_video_benchmark/README.md`"""
            video_path = Path(video_path)
            video_path.parent.mkdir(parents=True, exist_ok=True)

            ffmpeg_cmd = (
                f"ffmpeg -r {fps} "
                "-f image2 "
                "-loglevel error "
                f"-i {str(imgs_dir)}/{cam_name}_%d.png "
                "-vcodec libx264 "
                "-g 2 "
                "-pix_fmt yuv444p "
                f"{str(video_path)}"
            )

            subprocess.run(ffmpeg_cmd.split(" "), check=True)

        print("Encoding video ...")
        for cam_name in camera_names:
            encode_video_frames(
                Path(f"{session_path}/images_episode_{episode_id}"),
                Path(f"{session_path}/episode_{episode_id}_{cam_name}.mp4"),
                args.sampling_rate,
                cam_name,
            )
        print("Done encoding video!")

        print("Removing raw images ...")
        for cam_name in camera_names:
            for f in glob(
                f"{session_path}/images_episode_{episode_id}/{cam_name}_*.png"
            ):
                os.remove(f)
            os.rmdir(f"{session_path}/images_episode_{episode_id}")

        print("Saved!")
except KeyboardInterrupt:
    print("stop")
    exit()
