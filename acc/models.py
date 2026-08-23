"""公共数据模型。

本文件只定义"形状"，不写逻辑：
- FrontVehicle : 传感器/场景给出的前车状态（本阶段用脚本模拟输入）
- ControlOutput: 每个控制周期 ACC 输出的结果
- AccConfig    : ACC 参数配置（教科书式默认，后续按公司规范替换）
"""

from dataclasses import dataclass

from .state_machine import State


@dataclass
class FrontVehicle:
    """前车信息。

    distance      : 本车车头到前车车尾的距离 (m)
    rel_velocity  : 相对速度 v_front - v_ego (m/s)。>0 表示前车比我快。
    """

    distance: float
    rel_velocity: float


@dataclass
class ControlOutput:
    """一个控制周期的输出。"""

    state: State          # 当前 ACC 状态
    accel: float          # 请求加速度 (m/s^2)，正=加速，负=制动
    throttle: float       # 油门踏板 0~1（简化映射）
    brake: float          # 制动踏板 0~1（简化映射）
    mode: str             # 'cruise'(巡航) / 'follow'(跟车) / 'none'(未激活)


@dataclass
class AccConfig:
    """ACC 参数（教科书式默认值，均可用公司标定量替换）。"""

    set_speed: float = 30.0            # 默认设定速度 (m/s)，约 108 km/h
    max_speed: float = 40.0            # 超过此速度强制退出 ACC (m/s)
    time_gap: float = 1.5              # 跟车时距 (s)，constant time gap
    min_gap: float = 3.0               # 最小跟车距离 (m)
    accel_max: float = 2.0             # 最大加速度 (m/s^2)
    brake_max: float = -4.0            # 最大减速度 (m/s^2)
    follow_switch_dist: float = 60.0   # 前车距离超过此值 → 视为无前车，切巡航
    dt: float = 0.1                    # 控制周期 (s)

    # PID 参数（巡航与跟车各一套）
    kp_cruise: float = 1.0
    ki_cruise: float = 0.05
    kd_cruise: float = 0.1
    kp_follow: float = 1.0
    ki_follow: float = 0.05
    kd_follow: float = 0.2
