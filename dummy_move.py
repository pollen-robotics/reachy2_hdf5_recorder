import time

import numpy as np
from reachy2_sdk import ReachySDK

reachy = ReachySDK("localhost")
reachy.turn_on()
freq = 30

while True:

    reachy.r_arm.shoulder.pitch.goal_position = np.rad2deg(
        np.sin(2 * np.pi * freq * time.time())
    )
    time.sleep(1 / freq)
