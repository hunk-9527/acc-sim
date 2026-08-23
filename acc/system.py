"""ACCSystem：把状态机 + 纵向控制器组装成完整的被测系统。

对外接口（下一步接 CARLA 就换这里的输入/输出）：
    输入  : step(target, v_ego)  ← 前车信息 + 本车速度（CARLA 传感器提供）
    输出  : ControlOutput        → 油门/制动（接到 CARLA 车辆控制）
"""

from .controller import LongitudinalController
from .models import AccConfig, ControlOutput, FrontVehicle
from .state_machine import ACCStateMachine, State


class ACCSystem:
    def __init__(self, cfg=None):
        self.cfg = cfg or AccConfig()
        self.fsm = ACCStateMachine()
        self.long = LongitudinalController(self.cfg)
        self.v_set = self.cfg.set_speed

    # ---------- 用户事件 ----------
    def turn_on(self):
        self.fsm.turn_on()

    def turn_off(self):
        self.fsm.turn_off()

    def activate(self):
        self.fsm.activate()

    def cancel(self):
        self.fsm.cancel()

    def set_speed(self, v):
        self.v_set = v

    @property
    def state(self):
        return self.fsm.state

    # ---------- 周期控制 ----------
    def step(self, target: FrontVehicle | None, v_ego: float) -> ControlOutput:
        """一个控制周期。target 为 None 表示无前车。

        返回本周期输出；若期间触发退出条件（超速），状态会变为 STANDBY。
        """
        if self.fsm.state is not State.ACTIVE:
            return ControlOutput(state=self.fsm.state, accel=0.0,
                                 throttle=0.0, brake=0.0, mode="none")

        # 安全监测：超速强制退出 ACC
        if v_ego > self.cfg.max_speed:
            self.fsm.cancel()
            return ControlOutput(state=self.fsm.state, accel=0.0,
                                 throttle=0.0, brake=0.0, mode="none")

        accel = self.long.control(v_ego, self.v_set, target)
        throttle, brake = self._map_pedals(accel)
        return ControlOutput(state=self.fsm.state, accel=accel,
                             throttle=throttle, brake=brake, mode=self.long.mode)

    def _map_pedals(self, accel):
        """加速度 -> 踏板（简化线性映射，正式用标定量替换）。"""
        if accel >= 0:
            return min(1.0, accel / self.cfg.accel_max), 0.0
        return 0.0, min(1.0, -accel / abs(self.cfg.brake_max))
