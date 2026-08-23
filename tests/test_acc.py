"""ACC 系统 pytest 用例：状态迁移 + 纵向控制行为。

运行：
    D:\\TOOL\\SIL\\envs\\sim\\python.exe -m pytest tests/ -v
"""

from acc import ACCSystem, AccConfig, FrontVehicle


def make_system(**kwargs):
    return ACCSystem(AccConfig(**kwargs))


# ================= 状态迁移 =================

def test_initial_state_off():
    sys = make_system()
    assert sys.state.name == "OFF"


def test_turn_on_goes_standby():
    sys = make_system()
    sys.turn_on()
    assert sys.state.name == "STANDBY"


def test_activate_requires_standby():
    sys = make_system()
    sys.activate()  # OFF 下激活无效
    assert sys.state.name == "OFF"
    sys.turn_on()
    sys.activate()
    assert sys.state.name == "ACTIVE"


def test_cancel_from_active_returns_standby():
    sys = make_system()
    sys.turn_on()
    sys.activate()
    sys.cancel()
    assert sys.state.name == "STANDBY"


def test_turn_off_from_any_state():
    for act in (lambda s: None, lambda s: s.turn_on(), lambda s: (s.turn_on(), s.activate())):
        sys = make_system()
        act(sys)
        sys.turn_off()
        assert sys.state.name == "OFF"


# ================= 非激活无控制输出 =================

def test_standby_outputs_no_control():
    sys = make_system()
    sys.turn_on()
    out = sys.step(None, 10.0)
    assert out.mode == "none"
    assert out.throttle == 0.0
    assert out.brake == 0.0


# ================= 控制行为 =================

def test_cruise_accelerates_when_slow():
    sys = make_system()
    sys.turn_on()
    sys.activate()
    out = sys.step(None, 10.0)  # 设定 30，本车 10 → 应加速
    assert out.mode == "cruise"
    assert out.accel > 0
    assert out.throttle > 0


def test_follow_brakes_when_too_close():
    sys = make_system()
    sys.turn_on()
    sys.activate()
    target = FrontVehicle(distance=5.0, rel_velocity=0.0)  # 远小于期望距离
    out = sys.step(target, 20.0)
    assert out.mode == "follow"
    assert out.accel < 0
    assert out.brake > 0


def test_cruise_when_target_far():
    sys = make_system()
    sys.turn_on()
    sys.activate()
    target = FrontVehicle(distance=100.0, rel_velocity=0.0)  # 超过切巡航阈值
    out = sys.step(target, 20.0)
    assert out.mode == "cruise"


def test_target_lost_switches_to_cruise_but_stay_active():
    sys = make_system()
    sys.turn_on()
    sys.activate()
    target = FrontVehicle(distance=10.0, rel_velocity=0.0)
    out1 = sys.step(target, 20.0)
    assert out1.mode == "follow"
    out2 = sys.step(None, 20.0)  # 目标丢失 → 恢复巡航
    assert out2.mode == "cruise"
    assert sys.state.name == "ACTIVE"


def test_exceeding_max_speed_exits_active():
    sys = make_system(max_speed=25.0)
    sys.turn_on()
    sys.activate()
    out = sys.step(None, 30.0)
    assert sys.state.name == "STANDBY"
    assert out.mode == "none"


# ================= 运动学收敛（跟车最终收敛到时距） =================

def test_follow_converges_to_constant_time_gap():
    """前车匀速，ACC 应把距离收敛到 d_set = min_gap + time_gap * v_ego。"""
    sys = make_system(set_speed=20.0, time_gap=1.5, min_gap=3.0)
    sys.turn_on()
    sys.activate()

    dt = sys.cfg.dt
    v_ego, x_ego = 20.0, 0.0
    v_front, x_front = 20.0, 15.0  # 起始 15m，偏近 → 应后退到期望距离

    for _ in range(500):
        target = FrontVehicle(distance=x_front - x_ego, rel_velocity=v_front - v_ego)
        out = sys.step(target, v_ego)
        v_ego = max(0.0, v_ego + out.accel * dt)
        x_ego += v_ego * dt
        x_front += v_front * dt  # 前车匀速

    d_final = x_front - x_ego
    d_set = 3.0 + 1.5 * v_ego
    assert abs(d_final - d_set) < 1.0, f"d={d_final:.2f}, d_set={d_set:.2f}"
