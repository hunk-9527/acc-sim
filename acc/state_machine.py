"""ACC 状态机：OFF <-> STANDBY <-> ACTIVE。

设计成"事件驱动"：只响应事件改变状态，本身不含控制逻辑。
好处：状态迁移可独立测试；控制逻辑放 controller，职责分离。
"""

from enum import Enum, auto


class State(Enum):
    OFF = auto()      # 关闭：任何输入无响应
    STANDBY = auto()  # 待机：ACC 已开但未激活（等待用户 SET 或激活条件满足）
    ACTIVE = auto()   # 激活：正在执行巡航/跟车控制


class ACCStateMachine:
    """状态迁移表：
        OFF     --turn_on-->  STANDBY
        STANDBY --turn_off--> OFF
        STANDBY --activate--> ACTIVE
        ACTIVE  --cancel----> STANDBY
        ACTIVE  --turn_off--> OFF
    """

    def __init__(self):
        self.state = State.OFF

    def turn_on(self):
        """开启 ACC（仅 OFF -> STANDBY）。"""
        if self.state is State.OFF:
            self.state = State.STANDBY

    def turn_off(self):
        """关闭 ACC（任何状态 -> OFF）。"""
        self.state = State.OFF

    def activate(self):
        """激活（仅 STANDBY -> ACTIVE）。"""
        if self.state is State.STANDBY:
            self.state = State.ACTIVE

    def cancel(self):
        """取消（仅 ACTIVE -> STANDBY）。"""
        if self.state is State.ACTIVE:
            self.state = State.STANDBY

    def is_active(self):
        return self.state is State.ACTIVE
