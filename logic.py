"""
logic.py —— 开心的望望 · 纯逻辑层(不依赖 streamlit,可单测)
口径:港币、复利、看整个账户。基准 = 起算日的账户总值。
"""
import datetime as dt


# ── 复利目标 ───────────────────────────────────────────────────────────────
def monthly_rate(annual_multiple):
    """年度目标(以"翻几倍"表示,100%→1.0)→ 复利月度收益率。"""
    return (1 + annual_multiple) ** (1 / 12) - 1


def expected_value(start_capital, annual_multiple, days_elapsed):
    """按复利,起算至今 days_elapsed 天后,该档目标"应到"的账户值。"""
    yrs = max(days_elapsed, 0) / 365.0
    return start_capital * ((1 + annual_multiple) ** yrs)


# ── 每日指标 ───────────────────────────────────────────────────────────────
def compute_row(start_capital, prev_value, prev_peak, total_value):
    """
    给定起始本金、昨日值、历史峰值、今日账户总值,算出:
    当日盈亏%、累计收益%、新峰值、当前回撤%。
    prev_value / prev_peak 为 None 时表示这是第一天(用 start_capital)。
    """
    base_prev = prev_value if prev_value else start_capital
    peak = max(prev_peak or start_capital, total_value)
    day_pnl = (total_value / base_prev - 1) * 100 if base_prev else 0.0
    cum = (total_value / start_capital - 1) * 100 if start_capital else 0.0
    dd = (total_value / peak - 1) * 100 if peak else 0.0   # ≤0
    return {
        "day_pnl_pct": round(day_pnl, 3),
        "cum_return_pct": round(cum, 3),
        "peak_value": round(peak, 2),
        "drawdown_pct": round(dd, 3),
    }


# ── 女儿锚点换算 ───────────────────────────────────────────────────────────
def describe_amount(hkd, anchors):
    """把一笔港币金额翻译成'她的几年钢琴课/几次牙齿矫正'。"""
    amt = abs(hkd)
    piano = anchors["piano_year_hkd"]
    braces = anchors["braces_hkd"]
    parts = []
    if amt >= braces:
        parts.append(f"{amt / braces:.1f} 次牙齿矫正")
    if amt >= piano:
        yrs = amt / piano
        parts.append(f"{yrs:.0f} 年钢琴课" if yrs >= 1 else f"{yrs*12:.0f} 个月钢琴课")
    if not parts:
        parts.append(f"{amt / piano * 12:.1f} 个月钢琴课")
    return " · ".join(parts)


# ── 风控判定 ───────────────────────────────────────────────────────────────
def evaluate_alerts(day_pnl_pct, drawdown_pct, cfg):
    """返回触发的警报列表:[(级别, 类型)]。级别 deadline>danger>warn>good。"""
    out = []
    if day_pnl_pct >= cfg["take_profit_pct"]:
        out.append(("good", "take_profit"))
    if drawdown_pct <= cfg["deadline_pct"]:
        out.append(("deadline", "deadline"))
    elif drawdown_pct <= cfg["drawdown_pct"]:
        out.append(("danger", "drawdown"))
    return out


# ── 话术(戳心,围绕"她") ─────────────────────────────────────────────────
def speak(kind, hkd_amount, anchors):
    """生成飒姐妹·女儿话术。hkd_amount 为相关金额(正数)。"""
    a = describe_amount(hkd_amount, anchors)
    amt = f"{abs(hkd_amount):,.0f} 港币"
    if kind == "take_profit":
        return (f"停一下,姐妹。今天浮盈 +{amt}。\n\n"
                f"这是给她的 {a}。落袋,它就真的为她攒下了;贪下去,明天可能就还回去。\n\n"
                f"她那么懂事让你存起来——现在,去止盈。💗")
    if kind == "drawdown":
        return (f"停。回撤 {amt} 了。\n\n"
                f"这是从她那儿拿走的 {a}。再到 -4% 死线,就更难补回来。\n\n"
                f"纪律不是束缚,是替她守住。清,现在。")
    if kind == "deadline":
        return (f"🚨 死线。回撤已达 -4%,{amt}。\n\n"
                f"这是她 {a}。不能再退了——立刻清仓,守住底线。")
    if kind == "monthly_good":
        return (f"本月 +{amt},稳稳的。够给她 {a} 了 ✅\n\n"
                f"不是赌来的,是你守着纪律一点点攒的——这就是给她最好的答案。别上头。")
    return ""


def daily_brief(cum_return_pct, tier_gaps):
    """没触发警报时的简洁日常播报。tier_gaps: {名称: 还差金额hkd}。"""
    gap = tier_gaps.get("保底", 0)
    s = f"今天累计 {cum_return_pct:+.2f}%。"
    if gap > 0:
        s += f" 离本月保底线还差 {gap:,.0f} 港币,稳住。"
    else:
        s += " 已超保底线,继续守纪律。"
    return s
