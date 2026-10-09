"""
eval_report.py —— Python 第三课（90 分钟）· acc_sim 的正式评测器

★ 位置说明：第 1、2 课的 student 文件在 python-101/，那是**练习题**。
  从这个文件起，你写的是**交付物**——它属于项目本体，所以直接生在 acc_sim/scripts/。

主题：真实数据 → 出指标 → 交叉分析 → 存结论

规则：**你自己敲。**
      卡住 → 先自己看 30 秒 → 还不会 → 再问我。卡住 3 分钟以上才准问。

跑法：
    cd D:/AI/myProject/learning/projects/acc_sim
    D:/TOOL/SIL/envs/sim/python.exe scripts/eval_report.py

数据（平台层产出，**只读，不许改**）：
    outputs/suite_results.csv     15 条用例 = 5 类场景 × 3 档 time_gap
    产生它的是 scripts/run_suite.py   ← 可以读，但**不要改**

⚠ 每次改完必须重新跑。Python 不会自动重载。
"""

# ============================================================
# 第 1 段（10 分钟）：热身 —— 先用眼睛，不用代码
# ------------------------------------------------------------
# 任务：打开 outputs/suite_results.csv（VSCode 里直接双击），扫 15 行，
#       写下你猜「哪几类场景会 FAIL」。
#
# ★ 关键一问：这份数据的 FAIL 分布，和上节课那份**人造 CSV** 一样吗？
#   上节人造数据里，旁车切入是重灾区；这一份呢？
#
# 把猜测写成 # 注释留在下面，写完再往下走 —— 有猜测才有"对答案"的快感。
# ============================================================

# 我的猜测（第一段写在这行下面 👇）
#  跟人造不一样，这一份明显对于旁车切入的场景都正常跟住前车了，没有发生碰撞情况，只是对于静止车和前车急刹出现问题。

# ============================================================
# 第 2 段（15 分钟）：读表 —— 复现第 2 课的老三样
# ------------------------------------------------------------
# 任务：读表 → 看规模 → 数 PASS/FAIL → 把 FAIL 的行捞出来
#
# 提示1：读表（注意路径：脚本在 scripts/ 下跑，数据在 outputs/ 下）
#         import pandas as pd
#         df = pd.read_csv("outputs/suite_results.csv")
# 提示2：看规模（行数列数）和列名
#         df.shape
#         df.columns
# 提示3：数 PASS / FAIL 各几条
#         df["result"].value_counts()
# 提示4：把 FAIL 的捞出来，只看关键几列
#         fails = df[df["result"] == "FAIL"]
#         print(fails[["test_id", "scenario", "time_gap_s", "min_gap_m", "fail_reason"]])
#
# ★ 停下来对一次第 1 段的猜测 —— 猜对了没？
# ============================================================

# 你的代码写在这行下面 👇
import pandas as pd
df = pd.read_csv("outputs/suite_results.csv")
print(df.shape)
print(df.columns)
print(df["result"].value_counts())
fails =df[df["result"]=="FAIL"]
print(fails[["test_id", "scenario", "time_gap_s", "min_gap_m", "fail_reason"]])







# ============================================================
# 第 3 段（20 分钟）：分组聚合 —— 15 行数字变成 5 条结论
# ------------------------------------------------------------
# 任务：按 scenario 分组，算出 每组的 条数 / 最小车距 / FAIL 条数
#
# 提示1：第 2 课学过的基础款
#         g = df.groupby("scenario")["min_gap_m"].agg(["count", "min", "mean"])
#         print(g.sort_values("min").round(2))
# 提示2：★ 但这里更该看的是「每组 FAIL 几条」，而不是平均车距
#         —— 因为平均车距会被 PASS 的那些撑得虚高
# ★ 提示3（新东西）：agg 里可以塞自定义函数
#         agg(["count", "min", lambda s: (s < 5).sum()])   ← 数每组的 FAIL 条数
#       或者更省事的写法：先造一列布尔，再对它求和（True=1, False=0）
#         df["is_fail"] = df["result"] == "FAIL"
#         df.groupby("scenario")["is_fail"].sum()
#
# ★ 完成这一段，你就把"15 行数字"压缩成了"5 条结论"。
# ============================================================

# 你的代码写在这行下面 👇
g = df.groupby("scenario")["min_gap_m"].agg(["count", "min", "mean"])
print(g.sort_values("min").round(2))
df["is_fail"] = df["result"] == "FAIL"
print(df.groupby("scenario")["is_fail"].sum())

# ============================================================
# 第 4 段（20 分钟）：★ 交叉分析 —— time_gap 到底救了谁？
# ------------------------------------------------------------
# 任务：做一张表 —— 行 = 场景，列 = time_gap(0.8 / 1.5 / 2.0)，
#       格子里填 最小车距。一眼看出"调标定量"对哪类场景有用、对哪类没用。
#
# 提示1：这一步叫「透视」，pandas 里叫 pivot_table
#         df.pivot_table(index="scenario", columns="time_gap_s",
#                        values="min_gap_m", aggfunc="min")
# 提示2：打印时四舍五入，负值一眼就看得见
#         .round(2)
# 提示3（也可以）：想看 PASS/FAIL 而不是车距，就换 values 和 aggfunc
#         pd.crosstab(df["scenario"], df["time_gap_s"], values=df["result"],
#                     aggfunc="first")
#
# ★ 写完盯着这张表看 30 秒，然后回答（写在代码下面）：
#     time_gap 从 0.8 调到 2.0，哪几类场景的车距明显变好？
#     哪几类**不管怎么调都还是撞**？
#     这说明"调标定量"能解决什么、不能解决什么？
# ============================================================

# 你的代码写在这行下面 👇
print(df.pivot_table(index="scenario", columns="time_gap_s",values="min_gap_m", aggfunc="min").round(2))
# 前车切出，前车急刹，稳态跟车明显变好了，静止目标还是撞，表达量能解决前车急刹场景下的碰撞问题，静止车无法改变。



# ============================================================
# 第 5 段（15 分钟）：出图 + 存 PNG ★ 本课主产出
# ------------------------------------------------------------
# 任务：画一张横向柱状图 —— 每个场景一根柱子，长度 = 该场景最小车距；
#       负值（撞上）标红；★ 再画一条判据线（5.0m）当"验收门槛"。
#
# 提示1：第 2 课的老配方（中文那两行必须加，见 pitfalls P-VIS-01）
#         import matplotlib
#         matplotlib.use("Agg")
#         import matplotlib.pyplot as plt
#         plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
#         plt.rcParams["axes.unicode_minus"] = False
# 提示2：算出每个场景的最差车距，从小到大排
#         worst = df.groupby("scenario")["min_gap_m"].min().sort_values()
# 提示3：颜色 —— 负值红、正值蓝
#         colors = ["#C0392B" if v < 0 else "#2E86C1" for v in worst.values]
# 提示4：画横向柱子
#         fig, ax = plt.subplots(figsize=(8, 4.5))
#         bars = ax.barh(worst.index, worst.values, color=colors)
# 提示5：★ 本段和上节课唯一的新东西 —— 两条参考线
#         ax.axvline(0, color="black", linewidth=1, linestyle="--")      # 碰撞线
#         ax.axvline(5.0, color="#C0392B", linewidth=1, linestyle=":")   # 判据线
#       加完你就会看到：**有些柱子过了碰撞线，但没过判据线** —— 这就是"没撞"和"过了"的区别
# 提示6：标题/轴标签，然后存文件
#         ax.set_title("...")   ax.set_xlabel("...")
#         plt.savefig("outputs/eval_min_gap_by_scenario.png", dpi=150)
#
# 加分项：柱旁标数值（第 2 课的 for b, v in zip(bars, worst.values) 那段可以直接抄）
# ============================================================

# 你的代码写在这行下面 👇
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
worst = df.groupby("scenario")["min_gap_m"].min().sort_values()
colors = ["#C0392B" if v < 0 else "#2E86C1" for v in worst.values]
fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(worst.index, worst.values, color=colors)
ax.axvline(0, color="black", linewidth=1, linestyle="--") 
ax.axvline(5.0, color="#C0392B", linewidth=1, linestyle=":")
ax.set_title("ACC测试：各类场景最小车距（红 = 撞上）")
ax.set_xlabel("最小车距 min_gap (m)")
ax.set_xlim(worst.min() - 4, worst.max() + 6)
for b, v in zip(bars, worst.values):
    y = b.get_y() + b.get_height() / 2
    if v < 0:
        ax.text(v - 0.6, y, f"{v:.1f}", va="center", ha="right", color="#C0392B")
    else:
        ax.text(v + 0.6, y, f"{v:.1f}", va="center", ha="left")
plt.savefig("outputs/eval_min_gap_by_scenario.png", dpi=150)

# ============================================================
# 第 6 段（10 分钟）：写结论 —— 这才是交付物
# ------------------------------------------------------------
# 任务：不看代码，对着图和表，写一段话回答：
#
#   「这套 ACC 在 15 条用例里表现如何？问题集中在哪？根因定到哪一层？」
#
# ⚠⚠ 本课最值钱的一条纪律（第 2 课那条，别忘）：
#   **「数据结论」和「工程推断」必须分开写。**
#   数据说的 → 用"数据显示"开头，每个数字都能在表里指出来。
#   你推的   → 用"据工程经验推断"开头，并写清需要什么才能验证。
#
#   上节课你把工程推断写成了数据结论，这次别再犯。
#
# ⚠ 还有一条新的（本课新增）：
#   **引用判据时必须带出处**。写成「按当前判据（最小车距 < 5.0m 判 FAIL）……」
#   而不是「ACC 不合格」—— 判据是需求侧给的，不是脚本自己定的。
# ============================================================

# 你的结论写在这行下面 👇
#
# ── 一、数据显示（每个数字都能在 suite_results.csv / 透视表里指出来）──
# 按当前判据（**最小车距 < 5.0m 判 FAIL**），15 条用例通过 9 条、失败 6 条。
# 失败全部集中在两类场景，且均为 3/3 全挂：
#     前车急刹   -0.49 / -0.33 /  3.21 m   （time_gap = 0.8 / 1.5 / 2.0）
#     静止目标   -1.52 / -0.42 / -0.60 m
# 其余三类（稳态跟车、前车切出、旁车切入）9 条全通过。
#
# time_gap 从 0.8 调到 2.0 的敏感度（见第 4 段透视表）：
#     前车急刹   单调改善（-0.49 → 3.21），但 2.0 档仍未达判据（3.21 < 5.0）
#     静止目标   非单调（-1.52 → -0.42 → -0.60），2.0 档反而比 1.5 档差
#     旁车切入   1.5 档后饱和（17.12 → 17.12）
#
# ── 二、据工程经验推断（以下为推断，非数据结论）──
# 两类失败的性质不同，不应合并处理：
#   前车急刹：调 time_gap 有效 → 部分根因在**标定层**；但纯靠标定无法达判据。
#   静止目标：调参方向无效 → 根因**不在参数层**，初步怀疑在感知（远距离静止
#             目标检出）或控制（减速度上限）环节。
#   ⚠ 本数据集为黑盒指标（min_gap / ttc_min / max_decel），**不足以定位到具体
#     模块**。验证本推断需补充：感知侧目标检出日志（目标首次被识别的时刻）、
#     控制侧实际减速度指令。在此之前只能说"怀疑范围"，不能说"根因定位"。
#
# ── 三、结论边界（本数据集回答不了的问题）──
#   1) 旁车切入的切入时刻固定在第 3 秒，**不随 time_gap 变化**，因此无法回答
#      "time_gap 增大是否更易被切入"。需新增"切入时机随参数变化"的用例。
#   2) 图中每场景取最差档（groupby.min），**T006（前车急刹 / 2.0 档 / 3.21m）
#      未单独呈现** —— 它是本数据集里唯一"未碰撞但未达判据"的边界用例，被
#      -0.49 吃掉了。聚合口径决定哪些数据"看得见"，报告不该漏掉被吃掉的边界例。
#
# ── 四、对"把 time_gap 调到 3.0 是不是就过了"的答复 ──
#   不能一概而论：急刹场景趋势向上，或可通过，但属**外推**，不可拍板；
#   静止目标方向无效，**调到多少都不会过**。要回答这个问题，需要真跑 3.0 档。

# ============================================================
# 本课结束时的验收标准（自己能回答就算过）：
#
#   1. FAIL 集中在哪几类场景？和上节课那份人造 CSV 一样吗？
#   2. time_gap 从 0.8 调到 2.0，为什么在急刹场景里救不了场？
#   3. min_gap 出现负值、ttc 出现 0.01 —— 两个数各在说什么？
#      哪个对老板更有说服力？
#   4. ★ 哪半句是这份数据说的，哪半句是你从工程经验推的？
#   5. ★★ 老板说"把 time_gap 调到 3.0 再跑一遍应该就过了"——
#      你手上这份数据，能不能回答"调了会不会过"？
#      （提示：我们已经跑过一次类似的实验了，想想 brake_max 那次）
#
# 下一课：CARLA step1 —— client 连上 → spawn 车 → 截图 → 02_spawn_vehicle.py
# ============================================================
