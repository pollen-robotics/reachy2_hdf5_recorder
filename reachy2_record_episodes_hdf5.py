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
from reachy2_sdk import ReachySDK

from utils import GripperInput, play_sound

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
parser.add_argument(
    "-g",
    "--gripper_input",
    action="store_true",
    default=False,
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

reachy = ReachySDK(args.robot_ip)
time.sleep(1)

if args.gripper_input:
    gripper_input = GripperInput(reachy)


camera_names = ["cam_trunk", "cam_teleop"]
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

        # Ready sound
        play_sound(0.1, 400)
        play_sound(0.1, 500)
        play_sound(0.1, 600)
        current_episode_length = 0
        if not args.gripper_input:
            input("Press any key to start recording")
        else:
            print("Close the right gripper for 2 seconds to start recording ...")
            while not gripper_input.right_input():
                time.sleep(0.1)
            play_sound(0.5, 600)  # start recording sound
        print("Recording ...")
        elapsed = 0
        i = -1
        start = time.time()
        while time.time() - start < args.episode_length:
            i += 1
            t = time.time() - start
            took_start = time.time()

            # Acquire frames
            # TODO do something with the timestamps
            frames = {}

            get_frames_start = time.time()
            rgb_trunk, ts_trunk = reachy.cameras.depth.get_frame()
            rgb_teleop, ts_teleop = reachy.cameras.teleop.get_frame()
            print("get frames took", time.time() - get_frames_start)

            frames["cam_trunk"] = {"frame": rgb_trunk, "ts": ts_trunk}
            frames["cam_teleop"] = {"frame": rgb_teleop, "ts": ts_teleop}

            mobile_base_action = reachy.mobile_base.last_cmd_vel
            # mobile_base_action = {"x": 0, "y": 0, "theta": 0}  # TMP
            mobile_base_pos = reachy.mobile_base.odometry

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
                "mobile_base_vx": mobile_base_action["x"],
                "mobile_base_vy": mobile_base_action["y"],
                "mobile_base_vtheta": np.deg2rad(mobile_base_action["theta"]),
                "head_roll": np.deg2rad(reachy.head.neck.roll.goal_position),
                "head_pitch": np.deg2rad(reachy.head.neck.pitch.goal_position),
                "head_yaw": np.deg2rad(reachy.head.neck.yaw.goal_position),
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
                "mobile_base_vx": mobile_base_pos["vx"],
                "mobile_base_vy": mobile_base_pos["vy"],
                "mobile_base_vtheta": np.deg2rad(mobile_base_pos["vtheta"]),
                "head_roll": np.deg2rad(reachy.head.neck.roll.present_position),
                "head_pitch": np.deg2rad(reachy.head.neck.pitch.present_position),
                "head_yaw": np.deg2rad(reachy.head.neck.yaw.present_position),
            }

            data_dict["/action"].append(list(action.values()))
            data_dict["/observations/qpos"].append(list(qpos.values()))

            for cam_name in camera_names:
                data_dict[f"/observations/images_ids/{cam_name}"].append(i)
                frame = frames[cam_name]["frame"]
                images_queue.put(
                    (
                        frame,
                        f"{session_path}/images_episode_{episode_id}/{cam_name}_{i}.png",
                    )
                )

            took = time.time() - took_start
            if (1 / args.sampling_rate - took) < 0:
                print(
                    f"Warning: frame took {round(took, 4)} seconds to record with {round(1/args.sampling_rate, 4)}s per frame budget, expect frame drop"
                )

            time.sleep(max(0, 1 / args.sampling_rate - took))

        print("Done recording!")
        play_sound(0.1, 600)
        play_sound(0.1, 600)

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
                images_ids.create_dataset(cam_name, (max_timesteps,), dtype="int32")
            qpos = obs.create_dataset("qpos", (max_timesteps, 22))
            action = root.create_dataset("action", (max_timesteps, 22))

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
            try:
                os.rmdir(f"{session_path}/images_episode_{episode_id}")
            except:
                pass

        print("Saved!")
except KeyboardInterrupt:
    print("stop")
    exit()
