import os
import time
from threading import Thread

from reachy2_sdk import ReachySDK


def play_sound(duration, freq):
    os.system("play -nq -t alsa synth {} sine {}".format(duration, freq))


class GripperInput:
    def __init__(self, reachy: ReachySDK):
        self.reachy = reachy
        self.left_gripper_closed = False
        self.right_gripper_closed = False
        self.right_gripper_closed_time = time.time()
        self.left_gripper_closed_time = time.time()
        self.right_input_sent = False
        self.left_input_sent = False
        Thread(target=self.tick, daemon=True).start()

    def is_closed(self, left=False):
        return self.left_gripper_closed if left else self.right_gripper_closed

    def left_input(self, seconds_threshold=2):
        if not self.left_input_sent:
            if time.time() - self.left_gripper_closed_time > seconds_threshold:
                self.left_input_sent = True
                return True
        return False

    def right_input(self, seconds_threshold=2):
        if not self.right_input_sent:
            if time.time() - self.right_gripper_closed_time > seconds_threshold:
                self.right_input_sent = True
                return True
        return False

    def tick(self):
        while True:
            self.left_gripper_closed = (
                self.reachy.l_arm.gripper.opening < 10
            )  # opening in %
            self.right_gripper_closed = (
                self.reachy.r_arm.gripper.opening < 10
            )  # opening in %

            if not self.left_gripper_closed:
                self.left_gripper_closed_time = time.time()
                self.left_input_sent = False
            if not self.right_gripper_closed:
                self.right_gripper_closed_time = time.time()
                self.right_input_sent = False

            time.sleep(0.05)


if __name__ == "__main__":

    play_sound(0.1, 400)
    play_sound(0.1, 500)
    play_sound(0.1, 600)
    # reachy = ReachySDK("192.168.1.42")
    # time.sleep(1)
    # gripper_input = GripperInput(reachy)
    # while True:
    #     if gripper_input.left_input():
    #         print("left INPUT")
    #         play_sound(0.5, 600)
    #     if gripper_input.right_input():
    #         print("right INPUT")
    #         play_sound(0.2, 600)
    #         play_sound(0.2, 600)
    #     time.sleep(0.1)
