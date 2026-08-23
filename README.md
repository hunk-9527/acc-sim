# acc_sim — 简化 ACC（自适应巡航）被测系统

> 用途：**9 月 Python 练习 + 测试环境验证 + 2026.10 CARLA 闭环的被测系统**。
> 说明：这是一个**教科书式的简化 ACC**（Constant Time Gap + PID 纵向控制），目的是把"测试对象 + 测试用例 + 控制逻辑"这条链路跑通。业务细节（跟车策略、参数、场景规范）后续按你的公司量产规范替换。

## 这是什么

一个模拟的 ACC 功能，包含：
- **状态机**：OFF ↔ STANDBY ↔ ACTIVE（ACC 的启停/激活/取消逻辑）
- **纵向控制器**：定速巡航 + 跟车（无前车巡航，有前车按"期望跟车距离"PID 控制）
- **测试用例**：pytest 覆盖状态迁移 + 控制行为

## 目录结构

```
acc_sim/
├── acc/                  # 被测系统本体
│   ├── models.py         # 数据模型（前车信息、控制输出、参数配置）
│   ├── state_machine.py  # ACC 状态机
│   ├── controller.py     # PID 控制器 + 巡航/跟车策略
│   └── system.py         # 组装：状态机 + 控制器 = ACCSystem
├── tests/
│   └── test_acc.py       # pytest 用例
├── scripts/
│   └── simulate.py       # 简单运动学模拟（前车减速→跟车→切出→恢复巡航）
└── README.md
```

## 怎么跑

```bash
cd D:\AI\myProject\learning\projects\acc_sim

# 跑全部测试
D:\TOOL\SIL\envs\sim\python.exe -m pytest tests/ -v

# 跑模拟场景（看 ACC 跟车/巡航行为）
D:\TOOL\SIL\envs\sim\python.exe scripts\simulate.py
```

## 功能规格（教科书式，可替换）

**状态机**
| 当前状态 | 事件 | 迁移到 |
|---|---|---|
| OFF | turn_on | STANDBY |
| STANDBY | turn_off | OFF |
| STANDBY | activate | ACTIVE |
| ACTIVE | cancel | STANDBY |
| ACTIVE | turn_off | OFF |
| ACTIVE | 超速/故障（step 内检测） | STANDBY |

**控制策略**
- 巡航：误差 = 设定速度 − 本车速度，PID → 加速度
- 跟车：期望距离 `d_set = min_gap + time_gap × v_ego`，误差 = 实测距离 − 期望距离，PID → 加速度
- 模式切换时清零 PID 积分，避免跳变
- 加速度钳位到 [brake_max, accel_max]（默认 −4 ~ +2 m/s²）

## 后续替换点（按公司规范/量产要求）

| 本骨架（教科书式） | 公司量产版可替换为 |
|---|---|
| CTG + 单 PID | 分段 PID / 模型预测控制（MPC）/ 参数标定表 |
| 固定 time_gap=1.5s | 按速度分档的跟车时距表 |
| 简化的 pedal 映射 | 标定量（CANape 标定的油门/制动曲线） |
| 无故障处理 | 传感器失效、控制器诊断、降级策略 |
| 单前车 | 多目标（最近可跟踪目标选择） |

## 扩展路线

1. **2026.10 接 CARLA**：本 ACC 的 `step(target, v_ego)` 输入改为从 CARLA 传感器取（前车距离/相对速度），输出油门/制动接到车辆控制 → 变成真正的闭环仿真被测系统
2. 加状态：Follow-To-Stop（跟到停）、起步（前车走了自己跟上去）
3. 加测试：边界值、随机化模糊测试、状态迁移全覆盖

> 代码注释用中文，结构刻意保持小而清晰，方便你逐行读懂后改造。
