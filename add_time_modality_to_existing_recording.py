import argparse
import os
from glob import glob
from pathlib import Path

import h5py
import numpy as np

parser = argparse.ArgumentParser("")
parser.add_argument(
    "-s",
    "--session",
    type=str,
    required=True,
)
args = parser.parse_args()

assert os.path.exists(args.session), f"Session {args.session} does not exist"
assert "_raw" in args.session, f"Session {args.session} is not a raw session"
session_path = args.session.strip("/")

print(f"Processing session {session_path}")
new_session_name = session_path[: -len("_raw")] + "_with_time" + "_raw"
print(f"Creating new session {new_session_name}")
os.makedirs(new_session_name, exist_ok=True)

for file in glob(f"{session_path}/*.hdf5"):
    episode_id = Path(file).stem.split("_")[-1]
    new_episode_path = Path(new_session_name) / f"episode_{episode_id}.hdf5"
    data = h5py.File(file, "r")
    max_timesteps = len(data["/action"])

    actions = np.array(data["/action"]).copy()
    observations_images = np.array(data["/observations/images_ids/cam_trunk"]).copy()
    observations_qpos = np.array(data["/observations/qpos"]).copy()

    actions = list(actions)
    for i in range(len(actions)):
        actions[i] = list(actions[i])
    for i in range(len(actions)):
        actions[i].append(np.round(i / max_timesteps, 2))
    for i in range(len(actions)):
        actions[i] = np.array(actions[i])
    actions = np.array(actions)
    data_dict = {
        "/action": actions,
        "/observations/qpos": observations_qpos,
    }

    for camera_name in ["cam_trunk"]:
        data_dict[f"/observations/images_ids/{camera_name}"] = observations_images

        with h5py.File(
            new_episode_path,
            "w",
            rdcc_nbytes=1024**2 * 2,
        ) as root:
            root.attrs["compress"] = True
            obs = root.create_group("observations")
            images_ids = obs.create_group("images_ids")
            for cam_name in ["cam_trunk"]:
                images_ids.create_dataset("cam_trunk", (max_timesteps,), dtype="int32")
            qpos = obs.create_dataset("qpos", (max_timesteps, 22))
            action = root.create_dataset("action", (max_timesteps, 23))

            for name, array in data_dict.items():
                root[name][...] = array

videos_paths = glob(f"{session_path}/*.mp4")
for video_path in videos_paths:
    episode_id = Path(video_path).stem.split("_")[1]
    new_video_path = Path(new_session_name) / f"episode_{episode_id}_cam_trunk.mp4"
    # print(f"cp {video_path} {new_video_path}")
    os.system(f"cp {video_path} {new_video_path}")
