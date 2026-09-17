"""急刹场景探测：前车急刹时当前骨架控制器会发生什么？

结论预告：会撞。原因 = 控制器只用距离误差、忽略 rel_velocity，
对"接近速度"反应迟钝 —— 这正是量产 ACC 跟车控制必须有
相对速度项（阻尼/前馈）的原因，也是"前车急刹"必须进测试清单的原因。

场景：前车在平衡点（33m, 20m/s）1s 后以 -6 m/s^2 急刹
（比 ACC 最大减速度 -4 更狠）。观察 ACC 能否避免碰撞。

可以自己改 hard_brake_at / 减速度，看什么条件下不撞。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from acc import ACCSystem, AccConfig, FrontVehicle


def main():
    cfg = AccConfig(set_speed=20.0, time_gap=1.5, min_gap=3.0)
    sys = ACCSystem(cfg)
    sys.turn_on()
    sys.activate()

    dt = cfg.dt
    v_ego, x_ego = 20.0, 0.0
    v_front, x_front = 20.0, 33.0  # 从平衡点开始

    hard_brake_at = 1.0   # 1s 后前车急刹
    front_decel = 6.0     # 前车减速度 (m/s^2)，比 ACC 的 brake_max=4 更狠

    print("t(s)   dist    v_ego   v_front  accel   brk")
    print("-" * 48)
    collided = False
    for i in range(int(8.0 / dt)):
        t = i * dt
        if t >= hard_brake_at:
            v_front = max(0.0, v_front - front_decel * dt)
        target = FrontVehicle(x_front - x_ego, v_front - v_ego)
        out = sys.step(target, v_ego)
        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt
        if i % 10 == 0:
            print(f"{t:5.1f}  {x_front - x_ego:5.1f}  {v_ego:5.1f}   "
                  f"{v_front:5.1f}  {out.accel:5.2f}  {out.brake:4.2f}")
        if x_front - x_ego <= 0:
            print(f"\n>>> 碰撞！t={t:.1f}s，距离归零。")
            collided = True
            break

    if not collided:
        print("\n>>> 未碰撞，跟车成功。")


if __name__ == "__main__":
    main()
