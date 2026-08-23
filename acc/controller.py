"""纵向控制器：定速巡航 + 跟车（Constant Time Gap + PID）。

思路：
- 巡航：误差 = 设定速度 - 本车速度，PID 输出加速度。
- 跟车：期望距离 d_set = min_gap + time_gap * v_ego（时距越大越保守），
        误差 = 实测距离 - 期望距离，PID 输出加速度。
- 两种模式切换时清零对应 PID 积分，避免输出跳变。
"""


class PIDController:
    """位置式 PID（带积分钳位，防饱和）。"""

    def __init__(self, kp, ki, kd, dt, out_limit):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt
        self.out_limit = out_limit
        self._integral = 0.0
        self._prev_error = 0.0

    def reset(self):
        self._integral = 0.0
        self._prev_error = 0.0

    def compute(self, error):
        self._integral += error * self.dt
        self._integral = self._clamp(self._integral, self.out_limit)
        deriv = (error - self._prev_error) / self.dt
        self._prev_error = error
        out = self.kp * error + self.ki * self._integral + self.kd * deriv
        return self._clamp(out, self.out_limit)

    @staticmethod
    def _clamp(v, limit):
        return max(-limit, min(limit, v))


class LongitudinalController:
    """组合巡航 PID 与跟车 PID，并负责模式判定。"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.pid_cruise = PIDController(
            cfg.kp_cruise, cfg.ki_cruise, cfg.kd_cruise, cfg.dt, cfg.accel_max
        )
        self.pid_follow = PIDController(
            cfg.kp_follow, cfg.ki_follow, cfg.kd_follow, cfg.dt, abs(cfg.brake_max)
        )
        self.mode = "cruise"

    def reset(self):
        self.pid_cruise.reset()
        self.pid_follow.reset()

    def control(self, v_ego, v_set, target):
        """根据前车是否存在/远近，选择巡航或跟车，返回请求加速度。"""
        if target is None or target.distance > self.cfg.follow_switch_dist:
            # --- 巡航模式 ---
            self.mode = "cruise"
            self.pid_follow.reset()
            error = v_set - v_ego
            accel = self.pid_cruise.compute(error)
        else:
            # --- 跟车模式 ---
            self.mode = "follow"
            self.pid_cruise.reset()
            d_set = self.cfg.min_gap + self.cfg.time_gap * v_ego
            error = target.distance - d_set
            accel = self.pid_follow.compute(error)
        return self._clamp_accel(accel)

    def _clamp_accel(self, a):
        return max(self.cfg.brake_max, min(self.cfg.accel_max, a))
