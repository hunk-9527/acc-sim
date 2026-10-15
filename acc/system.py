"""ACCSystem：把状态机 + 纵向控制器组装成完整的被测系统。

对外接口（下一步接 CARLA 就换这里的输入/输出）：
    输入  : step(target, v_ego)  ← 前车信息 + 本车速度（CARLA 传感器提供）
    输出  : ControlOutput        → 油门/制动（接到 CARLA 车辆控制）
"""

from .controller import LongitudinalController
from .models import AccConfig, ControlOutput, FrontVehicle
from .state_machine import ACCStateMachine, State


class ACCSystem:
    def __init__(self, cfg=None, pedal_map=None):
        """pedal_map : 可选的「加速度 -> 踏板」映射，签名 (accel, v) -> (throttle, brake)。

        ★ 为什么留这个口子：`_map_pedals` 的默认实现假设 `throttle = accel / accel_max`
        （线性）。这对本仓库的纯 Python 理想被控对象成立，但**真实车辆的踏板 -> 加速度
        通常既非线性、又随车速变化** —— 油门给的是"力"，阻力随速度增长，同一个踏板位置
        在不同速度上给的加速度不是一个数。所以接真实的被控对象 / 执行器模型时，
        把标定得到的逆映射从这里注入。

        ★ 本仓库只提供**接缝**，不绑定任何具体仿真器，也不在代码里断言某个平台的实测值。
        具体的测量与标定属于**被控对象侧**的工作，随其交付物一起给。

        ★ 默认 None = 沿用原线性映射 —— **纯 Python 用例的表现一字不变**。
        注入的是**可调用对象**而不是某个类，这样本模块不必 import 任何仿真器。
        """
        self.cfg = cfg or AccConfig()
        self.fsm = ACCStateMachine()
        self.long = LongitudinalController(self.cfg)
        self.v_set = self.cfg.set_speed
        self.pedal_map = pedal_map

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
        throttle, brake = self._map_pedals(accel, v_ego)
        return ControlOutput(state=self.fsm.state, accel=accel,
                             throttle=throttle, brake=brake, mode=self.long.mode)

    def _map_pedals(self, accel, v_ego=None):
        """加速度 -> 踏板。

        默认 = 简化线性映射（`throttle = accel / accel_max`）。
        v_ego 会被传给注入的 pedal_map —— 因为真实车辆的推力/阻力都随速度变，
        "要 1 m/s²"对应多少油门，10 m/s 和 30 m/s 上不是一个数。
        ★ 注意 ControlOutput.accel 是**请求值**，不是被控对象实际给到的值；
          pedal_map 可能饱和（请求 -4 只给得起 -2.7），要判实际表现必须用实测速度。
        """
        if self.pedal_map is not None:
            return self.pedal_map(accel, v_ego)
        if accel >= 0:
            return min(1.0, accel / self.cfg.accel_max), 0.0
        return 0.0, min(1.0, -accel / abs(self.cfg.brake_max))
