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
    default=50,
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


cam = SDKWrapper(get_config_file_path("CONFIG_SR"), fps=args.sampling_rate)

reachy = ReachySDK(args.robot_ip)
time.sleep(1)


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

        # give time to the auto-exposure to stabilize
        for i in range(10):
            cam_data, _, _ = cam.get_data()

        current_episode_length = 0
        input("Press any key to start recording")
        print("Recording ...")
        elapsed = 0
        i = -1
        start = time.time()
        while time.time() - start < args.episode_length:
            i += 1
            t = time.time() - start
            took_start = time.time()

            cam_data, _, _ = cam.get_data()

            left_rgb = cam_data["left"]
            # right_rgb = cam_data["right"]

            action = {
                "l_arm_shoulder_pitch": np.deg2rad(
                    reachy.l_arm.shoulder.pitch.goal_position
                ),
                "l_arm_shoulder_roll": np.deg2rad(
                    reachy.l_arm.shoulder.roll.goal_position
                ),
                "l_arm_elbow_yaw": np.deg2rad(reachy.l_arm.elbow.yaw.goal_position),
                "l_arm_elbow_pitch": np.deg2rad(reachy.l_arm.elbow.pitch.goal_position),
                "l_arm_wrist_roll": np.deg2rad(reachy.l_arm.wrist.roll.goal_position),
                "l_arm_wrist_pitch": np.deg2rad(reachy.l_arm.wrist.pitch.goal_position),
                "l_arm_wrist_yaw": np.deg2rad(reachy.l_arm.wrist.yaw.goal_position),
                "l_gripper": reachy.l_arm.gripper._goal_position,
                "r_arm_shoulder_pitch": np.deg2rad(
                    reachy.r_arm.shoulder.pitch.goal_position
                ),
                "r_arm_shoulder_roll": np.deg2rad(
                    reachy.r_arm.shoulder.roll.goal_position
                ),
                "r_arm_elbow_yaw": np.deg2rad(reachy.r_arm.elbow.yaw.goal_position),
                "r_arm_elbow_pitch": np.deg2rad(reachy.r_arm.elbow.pitch.goal_position),
                "r_arm_wrist_roll": np.deg2rad(reachy.r_arm.wrist.roll.goal_position),
                "r_arm_wrist_pitch": np.deg2rad(reachy.r_arm.wrist.pitch.goal_position),
                "r_arm_wrist_yaw": np.deg2rad(reachy.r_arm.wrist.yaw.goal_position),
                "r_gripper": reachy.r_arm.gripper._goal_position,
            }

            qpos = {
                "l_arm_shoulder_pitch": np.deg2rad(
                    reachy.l_arm.shoulder.pitch.present_position
                ),
                "l_arm_shoulder_roll": np.deg2rad(
                    reachy.l_arm.shoulder.roll.present_position
                ),
                "l_arm_elbow_yaw": np.deg2rad(reachy.l_arm.elbow.yaw.present_position),
                "l_arm_elbow_pitch": np.deg2rad(
                    reachy.l_arm.elbow.pitch.present_position
                ),
                "l_arm_wrist_roll": np.deg2rad(
                    reachy.l_arm.wrist.roll.present_position
                ),
                "l_arm_wrist_pitch": np.deg2rad(
                    reachy.l_arm.wrist.pitch.present_position
                ),
                "l_arm_wrist_yaw": np.deg2rad(reachy.l_arm.wrist.yaw.present_position),
                "l_gripper": reachy.l_arm.gripper._present_position,
                "r_arm_shoulder_pitch": np.deg2rad(
                    reachy.r_arm.shoulder.pitch.present_position
                ),
                "r_arm_shoulder_roll": np.deg2rad(
                    reachy.r_arm.shoulder.roll.present_position
                ),
                "r_arm_elbow_yaw": np.deg2rad(reachy.r_arm.elbow.yaw.present_position),
                "r_arm_elbow_pitch": np.deg2rad(
                    reachy.r_arm.elbow.pitch.present_position
                ),
                "r_arm_wrist_roll": np.deg2rad(
                    reachy.r_arm.wrist.roll.present_position
                ),
                "r_arm_wrist_pitch": np.deg2rad(
                    reachy.r_arm.wrist.pitch.present_position
                ),
                "r_arm_wrist_yaw": np.deg2rad(reachy.r_arm.wrist.yaw.present_position),
                "r_gripper": reachy.r_arm.gripper._present_position,
            }

            data_dict["/action"].append(list(action.values()))
            data_dict["/observations/qpos"].append(list(qpos.values()))
            data_dict["/observations/images_ids/cam_trunk"].append(i)

            images_queue.put(
                (
                    left_rgb,
                    f"{session_path}/images_episode_{episode_id}/cam_trunk_{i}.png",
                )
            )

            took = time.time() - took_start
            if (1 / args.sampling_rate - took) < 0:
                print(
                    f"Warning: frame took {round(took, 4)} seconds to record with {round(1/args.sampling_rate, 4)}s per frame budget, expect frame drop"
                )

            time.sleep(max(0, 1 / args.sampling_rate - took))

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
            qpos = obs.create_dataset("qpos", (max_timesteps, 16))
            action = root.create_dataset("action", (max_timesteps, 16))

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

        print("Saved!")
except KeyboardInterrupt:
    print("stop")
    exit()
