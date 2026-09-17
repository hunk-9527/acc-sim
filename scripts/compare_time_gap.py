"""标定量实验：改 time_gap 看稳态跟车距离。

体验"改标定量 → 看行为变化"：
    期望距离 d_set = min_gap + time_gap * v_ego
    time_gap 越大 → 跟车距离越大（更保守）；越小 → 跟得更近（更激进）。

跑同一收敛场景（前车匀速 20 m/s，本车从 15m 偏近位置退出到稳态），
对比三个 time_gap 值的稳态跟车距离，验证公式并观察收敛过程。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from acc import ACCSystem, AccConfig, FrontVehicle


def run_to_steady(time_gap: float, n_steps: int = 500) -> tuple[float, float]:
    """返回 (稳态距离, 稳态速度)。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)
    sys = ACCSystem(cfg)
    sys.turn_on()
    sys.activate()

    dt = cfg.dt
    v_ego, x_ego = 20.0, 0.0
    v_front, x_front = 20.0, 15.0  # 起始 15m，偏近 → ACC 应退到期望距离

    for _ in range(n_steps):
        target = FrontVehicle(distance=x_front - x_ego, rel_velocity=v_front - v_ego)
        out = sys.step(target, v_ego)
        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt

    return x_front - x_ego, v_ego


def main():
    print("标定量实验：time_gap 对稳态跟车距离的影响（v_ego≈20 m/s, min_gap=3.0）")
    print("-" * 60)
    print(f"{'time_gap(s)':<12}{'d_set 理论(m)':<14}{'稳态距离(m)':<14}{'偏差(m)':<10}")
    print("-" * 60)

    for gap in (0.8, 1.5, 2.0):
        d_final, v_final = run_to_steady(gap)
        d_set = 3.0 + gap * v_final  # 用实际稳态速度算理论值
        print(f"{gap:<12.1f}{d_set:<14.1f}{d_final:<14.2f}{d_final - d_set:<+10.2f}")

    print("-" * 60)
    print("time_gap=0.8 → 跟车 19m（激进）；1.5 → 33m（常用）；2.0 → 43m（保守）")
    print("这就是'标定量改动 → 跟车时距/舒适性/安全性'的直接映射。")


if __name__ == "__main__":
    main()
