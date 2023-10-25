import pygame
import time
import math
from pymycobot import MyCobot
from threading import Thread
from enum import Enum
import typing as T

mc = MyCobot("/dev/ttyAMA0", "1000000")
mc.set_fresh_mode(1)

context = {"running": True}
arm_speed = 50
sampling_rate = 10
arm_angle_table = {"init": [0, 0, -90, 0, 0, 0]}
global_states = {
    "enable": True,
    "initialized": True,
    "origin": None,
    "gripper_val": 0,
    "pump": False,
}


class JoyStickKey(Enum):
    StartKey = 7
    SelectKey = 6
    ModeKey = 8
    RLeftKey = 2
    RRightKey = 1
    RTopKey = 3
    RBottomKey = 0
    R1 = 5
    L1 = 4
    LJoyStickKey = 9
    RJoyStickKey = 10
    ArrowUp = (0, 1)
    ArrowDown = (0, -1)
    ArrowLeft = (-1, 0)
    ArrowRight = (1, 0)
    ArrowReleased = (0, 0)


class JoyStickContinous(Enum):
    LeftXAxis = 0
    LeftYAxis = 1
    L2 = 2
    RightXAxis = 3
    RightYAxis = 4
    R2 = 5


joystick_key_map = {
    0: JoyStickKey.RBottomKey,
    1: JoyStickKey.RRightKey,
    2: JoyStickKey.RLeftKey,
    3: JoyStickKey.RTopKey,
    4: JoyStickKey.L1,
    5: JoyStickKey.R1,
    6: JoyStickKey.SelectKey,
    7: JoyStickKey.StartKey,
    8: JoyStickKey.ModeKey,
    9: JoyStickKey.LJoyStickKey,
    10: JoyStickKey.RJoyStickKey,
    (0, 1): JoyStickKey.ArrowUp,
    (0, -1): JoyStickKey.ArrowDown,
    (1, 0): JoyStickKey.ArrowRight,
    (-1, 0): JoyStickKey.ArrowLeft,
    (0, 0): JoyStickKey.ArrowReleased,
}

joystick_continous_map = {
    0: JoyStickContinous.LeftXAxis,
    1: JoyStickContinous.LeftYAxis,
    2: JoyStickContinous.L2,
    3: JoyStickContinous.RightXAxis,
    4: JoyStickContinous.RightYAxis,
    5: JoyStickContinous.R2,
}


def get_init_key_hold_timestamp():
    return {
        JoyStickKey.L1: -1,
        JoyStickKey.R1: -1,
        JoyStickContinous.L2: -1,
        JoyStickContinous.R2: -1,
    }


key_hold_timestamp = get_init_key_hold_timestamp()


def get_joystick():
    pygame.init()
    pygame.joystick.init()

    try:
        joystick = pygame.joystick.Joystick(0)
    except:
        print("Please connect the handle first.")
        exit(1)
    joystick.init()
    return joystick


def dispatch_key_action(key: T.Union[JoyStickKey, JoyStickContinous], value: float):
    global mc, arm_angle_table, global_states
    print(f"key : {key} value : {value}")

    not_zero = lambda x: x < -0.1 or x > 0.1
    is_zero = lambda x: -0.1 < x < 0.1

    if key == JoyStickKey.StartKey:
        if mc.is_all_servo_enable() != 1:
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(255, 0, 0)
            time.sleep(0.5)
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(255, 0, 0)
            time.sleep(0.5)
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(255, 0, 0)
        else:
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(0, 255, 0)
            time.sleep(0.5)
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(0, 255, 0)
            time.sleep(0.5)
            mc.set_color(0, 0, 0)
            time.sleep(0.5)
            mc.set_color(0, 255, 0)
            global_states["initialized"] = True
    elif key == JoyStickKey.R1:
        mc.send_angles(arm_angle_table["init"], arm_speed)
        global_states["enable"] = True
        time.sleep(3)

    if global_states["enable"] and global_states["initialized"]:
        # 坐标移动
        if key in [
            JoyStickContinous.LeftXAxis,
            JoyStickContinous.LeftYAxis,
            JoyStickContinous.RightYAxis,
            JoyStickKey.ArrowUp,
            JoyStickKey.ArrowDown,
            JoyStickKey.ArrowLeft,
            JoyStickKey.ArrowRight,
            JoyStickContinous.RightXAxis,
        ]:
            if global_states["origin"] is None:
                coords = []
                for _ in range(5):
                    coords = mc.get_coords()
                    if len(coords) != 0:
                        break

                if len(coords) != 0:
                    global_states["origin"] = coords
                else:
                    print("Can't get coords.")
                    return

            if is_zero(value):
                global_states["origin"] = None
                return

            x, y, z, rx, ry, rz = global_states["origin"]

            # Y coord
            if key == JoyStickContinous.LeftXAxis:
                mc.send_coord(2, y - value * 10, 10)
                global_states["origin"][1] += value
                time.sleep(0.05)
            # X coord
            elif key == JoyStickContinous.LeftYAxis:
                mc.send_coord(1, x - value * 10, 10)
                global_states["origin"][0] += value
                time.sleep(0.05)
            # Z coord
            elif key == JoyStickContinous.RightYAxis:
                mc.send_coord(3, z - value * 10, 10)
                global_states["origin"][2] += value
                time.sleep(0.05)
            elif key == JoyStickContinous.RightXAxis:
                mc.send_coord(6, rz - value * 10, 10)
                global_states["origin"][5] += value
                time.sleep(0.05)
            elif key == JoyStickKey.ArrowUp:
                mc.send_coord(4, rx + 10, 10)
                global_states["origin"][3] += 10
                time.sleep(0.05)
            elif key == JoyStickKey.ArrowDown:
                mc.send_coord(4, rx - 10, 10)
                global_states["origin"][3] -= 10
                time.sleep(0.05)
            elif key == JoyStickKey.ArrowLeft:
                mc.send_coord(5, ry - 10, 10)
                global_states["origin"][4] -= 10
                time.sleep(0.05)
            elif key == JoyStickKey.ArrowRight:
                mc.send_coord(5, ry + 10, 10)
                global_states["origin"][4] += 10
                time.sleep(0.05)

    # 功能性
    if key == JoyStickContinous.L2 and not_zero(value):
        print(123)
        mc.release_all_servos()
        time.sleep(0.03)
    elif key == JoyStickContinous.R2 and not_zero(value):
        mc.power_on()
        time.sleep(0.03)


def dispatch_continous_key_action(key: JoyStickContinous, value: float):
    print(f"{key}:{value}")


def retreive_joystick_input(joystick, context):
    while context["running"]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                context["running"] = False
            elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                n = joystick.get_numbuttons()
                for key_id in range(n):
                    button_status = joystick.get_button(key_id)
                    if not button_status:
                        continue
                    dispatch_key_action(joystick_key_map[key_id], 1.0)

            elif event.type == pygame.JOYAXISMOTION:
                axes = joystick.get_numaxes()
                for key_id in range(axes):
                    axis = joystick.get_axis(key_id)

                    if (
                        joystick_continous_map[key_id] == JoyStickContinous.L2
                        or joystick_continous_map[key_id] == JoyStickContinous.R2
                    ):
                        axis = math.ceil(axis)
                        if int(axis) == -1:
                            continue

                    dispatch_key_action(joystick_continous_map[key_id], axis)

            elif event.type == pygame.JOYHATMOTION:
                hat = joystick.get_hat(0)
                dispatch_key_action(joystick_key_map[hat], 1.0)


if __name__ == "__main__":
    joystick = get_joystick()
    Thread(target=retreive_joystick_input, args=(joystick, context)).start()
