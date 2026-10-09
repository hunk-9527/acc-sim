"""场景批量执行器（平台层）—— 跑一批场景，把结果落成一张表。

★ 角色边界（重要，别越界）：
    本脚本 = 平台层。只负责"把测试跑起来 + 把数据落盘"。
    eval_report.py = 评测层。负责"读这张表 → 出指标 → 下结论"。
    平台不解释数据，评测不改数据来源。两边混在一起，报告就不可信。

用法：
    D:\TOOL\SIL\envs\sim\python.exe scripts\run_suite.py
输出：
    outputs/suite_results.csv   ← 第 3 课的输入

判据初版（下面 PASS_CRITERIA 里写死的三条）是"教科书式"暂定值，
正式项目里这三条 = 需求部门给的验收准则，属于**你要评审的第一件事**。
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from acc import ACCSystem, AccConfig, FrontVehicle

# ---------------------------------------------------------------- 判据（暂定，待评审）
SAFE_GAP_MIN = 5.0          # 全程最小车距下限 (m)
FAIL_ON_COLLISION = True    # 车距归零 = 碰撞
TTC_WARN_S = 1.5            # 最小 TTC 告警线 (s)；只记录，不参与本次判定

OUT_CSV = os.path.join(os.path.dirname(__file__), "..", "outputs", "suite_results.csv")


# ---------------------------------------------------------------- 单次仿真
def simulate(cfg, gap0, v_ego0, lead_plan, t_end, v_front0=None, start_active=True):
    """跑一个场景，返回指标字典。

    cfg       : AccConfig（含 time_gap 等标定量）
    gap0      : 初始车距 (m)，前车在本车前方这么远
    v_ego0    : 本车初速度 (m/s)
    lead_plan : 前车行为脚本 fn(t, v_front) -> (v_front_new, present)
                present=False 表示"目标不在视野内"，此时前车保持 gap0 影子跟随，
                等它 present=True 的那一刻（切入）才真正变成目标
    t_end     : 仿真时长 (s)
    v_front0  : 前车初速度 (m/s)，默认与本车同速
    """
    sys_ = ACCSystem(cfg)
    sys_.turn_on()
    if start_active:
        sys_.activate()

    dt = cfg.dt
    v_ego, x_ego = v_ego0, 0.0
    v_front = v_ego0 if v_front0 is None else v_front0
    x_front = gap0

    min_gap = float("inf")
    ttc_min = float("inf")
    max_decel = 0.0
    collided = False

    for i in range(int(t_end / dt)):
        t = i * dt

        v_front, present = lead_plan(t, v_front)
        if not present:
            target = None
            x_front = x_ego + gap0      # 影子跟随：目标不在视野，间距保持不变
            v_front = v_ego
        else:
            target = FrontVehicle(distance=x_front - x_ego,
                                  rel_velocity=v_front - v_ego)

        out = sys_.step(target, v_ego)

        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt

        gap = x_front - x_ego
        if present:
            min_gap = min(min_gap, gap)
            closing = v_ego - v_front
            if gap > 0 and closing > 0.1:
                ttc_min = min(ttc_min, gap / closing)
            if gap <= 0:
                collided = True
                min_gap = gap
                break
        max_decel = min(max_decel, out.accel)

    if min_gap == float("inf"):
        min_gap = float("nan")      # 全程无前车（纯巡航场景）

    return {
        "min_gap_m": round(min_gap, 2) if min_gap == min_gap else "",
        "ttc_min_s": round(ttc_min, 2) if ttc_min != float("inf") else "",
        "max_decel_mps2": round(max_decel, 2),
        "collided": collided,
    }


# ---------------------------------------------------------------- 场景库
def make_steady_follow(time_gap):
    """稳态跟车：本车从前车后方 15m 处起步（偏近），观察是否退到期望距离。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)
    return cfg, dict(gap0=max(15.0, 3.0 + time_gap * 20), v_ego0=20.0,
                     lead_plan=lambda t, vf: (20.0, True), t_end=50.0)


def make_hard_brake(time_gap):
    """前车急刹：从平衡点出发，1s 后前车以 -6 m/s² 急刹（比 ACC 的 -4 更狠）。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)

    def plan(t, vf):
        return (max(0.0, vf - 6.0 * cfg.dt), True) if t >= 1.0 else (20.0, True)

    return cfg, dict(gap0=3.0 + time_gap * 20, v_ego0=20.0,
                     lead_plan=plan, t_end=8.0)


def make_stationary_target(time_gap):
    """静止目标：前方 40m 处有静止车辆，本车 20 m/s 接近。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)
    return cfg, dict(gap0=40.0, v_ego0=20.0, v_front0=0.0,
                     lead_plan=lambda t, vf: (0.0, True), t_end=12.0)


def make_cut_in(time_gap, cut_in_at):
    """旁车切入：本车定速巡航中，3s 时旁车以 15 m/s 切入到前方 20m 处。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)

    def plan(t, vf):
        if t < cut_in_at:
            return (0.0, False)          # 切入前无目标 → 本车在巡航
        return (15.0, True)

    return cfg, dict(gap0=20.0, v_ego0=20.0,
                     lead_plan=plan, t_end=12.0)


def make_cut_out(time_gap):
    """前车切出：跟着跟得好好的，5s 时前车切出 → ACC 应恢复巡航。"""
    cfg = AccConfig(set_speed=20.0, time_gap=time_gap, min_gap=3.0)
    return cfg, dict(gap0=3.0 + time_gap * 20, v_ego0=20.0,
                     lead_plan=lambda t, vf: (20.0, t < 5.0), t_end=20.0)


SCENARIOS = [
    # (场景名, 用例构造器)
    ("稳态跟车",   make_steady_follow),
    ("前车急刹",   make_hard_brake),
    ("静止目标",   make_stationary_target),
    ("前车切出",   make_cut_out),
]

TIME_GAPS = (0.8, 1.5, 2.0)


def judge(min_gap, collided):
    """按上面暂定判据给出 PASS / FAIL（返回 结果, 原因）。"""
    if collided and FAIL_ON_COLLISION:
        return "FAIL", "碰撞"
    if min_gap != "" and min_gap < SAFE_GAP_MIN:
        return "FAIL", f"最小车距 {min_gap}m < {SAFE_GAP_MIN}m"
    return "PASS", ""


def main():
    rows = []
    idx = 0

    for name, maker in SCENARIOS:
        for gap in TIME_GAPS:
            idx += 1
            cfg, kw = maker(gap)
            m = simulate(cfg, **kw)
            result, reason = judge(m["min_gap_m"], m["collided"])
            rows.append({
                "test_id": f"T{idx:03d}",
                "scenario": name,
                "set_speed_kmh": int(cfg.set_speed * 3.6),
                "time_gap_s": gap,
                "min_gap_m": m["min_gap_m"],
                "ttc_min_s": m["ttc_min_s"],
                "max_decel_mps2": m["max_decel_mps2"],
                "result": result,
                "fail_reason": reason,
            })

    # 旁车切入单独跑（切入时机也是一维变量，不是 time_gap 的从属）
    for gap in TIME_GAPS:
        idx += 1
        cfg, kw = make_cut_in(gap, cut_in_at=3.0)
        m = simulate(cfg, **kw)
        result, reason = judge(m["min_gap_m"], m["collided"])
        rows.append({
            "test_id": f"T{idx:03d}",
            "scenario": "旁车切入",
            "set_speed_kmh": int(cfg.set_speed * 3.6),
            "time_gap_s": gap,
            "min_gap_m": m["min_gap_m"],
            "ttc_min_s": m["ttc_min_s"],
            "max_decel_mps2": m["max_decel_mps2"],
            "result": result,
            "fail_reason": reason,
        })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n_fail = sum(1 for r in rows if r["result"] == "FAIL")
    print(f"跑了 {len(rows)} 条用例 → {OUT_CSV}")
    print(f"PASS {len(rows) - n_fail} / FAIL {n_fail}")
    print("\n（平台到此为止。这些数字意味着什么 —— 是 eval_report.py 的事。）")


if __name__ == "__main__":
    main()
