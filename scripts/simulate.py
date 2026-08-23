"""开环运动学模拟：展示 ACC 完整行为链。

场景脚本：
    0-15s   前车匀速 18 m/s，本车从 0 起步追赶
    15-25s  前车减速到 8 m/s → ACC 应该制动跟车
    25-30s  前车保持 8 m/s
    30s 起  前车切出（目标丢失）→ ACC 恢复巡航到设定速度 25 m/s

注意：这是最简运动学（没有坡度/空气阻力/传动），只为"看懂 ACC 怎么响应"。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from acc import ACCSystem, AccConfig, FrontVehicle


def main():
    cfg = AccConfig(set_speed=25.0)
    sys = ACCSystem(cfg)
    sys.turn_on()
    sys.activate()

    dt = cfg.dt
    v_ego, x_ego = 0.0, 0.0
    v_front, x_front = 18.0, 60.0  # 前车在前面 60m，速度 18

    print("t(s)   state   mode    v_ego   dist   accel  thr  brk")
    print("-" * 58)
    for i in range(400):
        t = i * dt

        # --- 前车行为脚本 ---
        if t < 15:
            v_front = 18.0
        elif t < 25:
            v_front = max(8.0, v_front - 1.0 * dt)  # 减速
        else:
            v_front = 8.0

        # 30s 后前车切出（无目标）
        target = FrontVehicle(x_front - x_ego, v_front - v_ego) if t < 30 else None

        out = sys.step(target, v_ego)

        # --- 简单车辆运动学 ---
        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt

        if i % 10 == 0:
            print(f"{t:5.1f}  {out.state.name:<7s} {out.mode:<7s} "
                  f"{v_ego:5.2f} {x_front - x_ego:5.1f} {out.accel:5.2f} "
                  f"{out.throttle:4.2f} {out.brake:4.2f}")

    print("\n模拟结束。30s 后目标切出，ACC 恢复巡航到设定速度 25 m/s。")


if __name__ == "__main__":
    main()
