"""ACC 实时可视化：动态曲线窗口 + 自动保存 PNG。

场景与 simulate.py 一致（起步巡航 → 接近前车制动跟车 → 前车切出 → 恢复巡航）。

运行（弹窗实时刷新，关闭窗口后自动保存 PNG）：
    D:\\TOOL\\SIL\\envs\\sim\\python.exe scripts\\visualize.py

无界面模式（不弹窗，跑完直接存 PNG，用于 CI/验证）：
    D:\\TOOL\\SIL\\envs\\sim\\python.exe scripts\\visualize.py --headless

4 个面板（滚动显示最近 30 秒）：
    本车速度 / 跟车距离(实线) + 期望距离(虚线) / 油门 / 制动
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False

from acc import ACCSystem, AccConfig, FrontVehicle


def build_scenario():
    cfg = AccConfig(set_speed=25.0)
    acc = ACCSystem(cfg)
    acc.turn_on()
    acc.activate()
    return cfg, acc


def front_vehicle_speed(t):
    """前车行为脚本：0-15s 匀速 18，15-25s 减速到 8，之后保持 8。"""
    if t < 15:
        return 18.0
    if t < 25:
        return max(8.0, 18.0 - (t - 15.0))
    return 8.0


def run_scenario(cfg, acc, total_steps=400):
    """一次性跑完整场景，返回 (times, speeds, dists, d_sets, thrs, brks)。"""
    dt = cfg.dt
    v_ego, x_ego = 0.0, 0.0
    x_front = 60.0

    times, speeds, dists, d_sets, thrs, brks = [], [], [], [], [], []

    for step in range(total_steps):
        t = step * dt
        v_front = front_vehicle_speed(t)
        # 30s 后前车切出（无目标）
        target = FrontVehicle(x_front - x_ego, v_front - v_ego) if t < 30 else None
        out = acc.step(target, v_ego)

        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt

        times.append(t)
        speeds.append(v_ego)
        dists.append(x_front - x_ego)
        d_sets.append(cfg.min_gap + cfg.time_gap * v_ego)
        thrs.append(out.throttle)
        brks.append(out.brake)

    return times, speeds, dists, d_sets, thrs, brks


def setup_figure():
    """创建 4 面板画布，返回 (fig, axes)。"""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
    ax_v, ax_d, ax_thr, ax_brk = axes

    for ax, ylabel in ((ax_v, "速度"), (ax_d, "距离"), (ax_thr, "油门"), (ax_brk, "制动")):
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
    ax_brk.set_xlabel("时间 (s)")
    return fig, axes


def plot_all(axes, times, speeds, dists, d_sets, thrs, brks):
    """在 4 面板上画全部数据（用于 headless 静态图）。"""
    ax_v, ax_d, ax_thr, ax_brk = axes
    ax_v.plot(times, speeds, "b-", label="本车速度")
    ax_d.plot(times, dists, "g-", label="跟车距离")
    ax_d.plot(times, d_sets, "g--", label="期望距离")
    ax_thr.plot(times, thrs, "r-", label="油门")
    ax_brk.plot(times, brks, "m-", label="制动")
    for ax in axes:
        ax.legend(loc="upper left", fontsize=8)


def save_png(fig):
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, "acc_sim_result.png")
    fig.savefig(png, dpi=120)
    return os.path.normpath(png)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true",
                        help="不弹窗，跑完直接保存 PNG")
    args = parser.parse_args()

    if args.headless:
        matplotlib.use("Agg")
    else:
        matplotlib.use("TkAgg")  # 弹窗（依赖 tkinter，已确认可用）

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    cfg, acc = build_scenario()
    fig, axes = setup_figure()

    if args.headless:
        data = run_scenario(cfg, acc)
        plot_all(axes, *data)
        png = save_png(fig)
        print("已保存曲线图:", png)
        return

    # ---------- GUI 实时动画 ----------
    ax_v, ax_d, ax_thr, ax_brk = axes
    (line_v,) = ax_v.plot([], [], "b-", label="本车速度")
    (line_d,) = ax_d.plot([], [], "g-", label="跟车距离")
    (line_ds,) = ax_d.plot([], [], "g--", label="期望距离")
    (line_thr,) = ax_thr.plot([], [], "r-", label="油门")
    (line_brk,) = ax_brk.plot([], [], "m-", label="制动")
    for ax in axes:
        ax.legend(loc="upper left", fontsize=8)

    dt = cfg.dt
    v_ego, x_ego = 0.0, 0.0
    x_front = 60.0
    window = 30.0
    times, speeds, dists, d_sets, thrs, brks = [], [], [], [], [], []
    step = 0

    def update(_frame):
        nonlocal step, v_ego, x_ego, x_front
        t = step * dt
        v_front = front_vehicle_speed(t)
        target = FrontVehicle(x_front - x_ego, v_front - v_ego) if t < 30 else None
        out = acc.step(target, v_ego)

        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt

        times.append(t)
        speeds.append(v_ego)
        dists.append(x_front - x_ego)
        d_sets.append(cfg.min_gap + cfg.time_gap * v_ego)
        thrs.append(out.throttle)
        brks.append(out.brake)
        step += 1

        line_v.set_data(times, speeds)
        line_d.set_data(times, dists)
        line_ds.set_data(times, d_sets)
        line_thr.set_data(times, thrs)
        line_brk.set_data(times, brks)
        for ax in axes:
            ax.set_xlim(max(0.0, t - window), max(window, t))
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)
        return line_v, line_d, line_ds, line_thr, line_brk

    ani = FuncAnimation(fig, update, interval=dt * 1000,
                        blit=False, cache_frame_data=False)
    plt.show()

    png = save_png(fig)
    print("已保存曲线图:", png)


if __name__ == "__main__":
    main()
