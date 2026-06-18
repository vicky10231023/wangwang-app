"""
config.py —— 开心的望望 · 配置中心
改话术金额 / 目标 / 阈值 / 主题,都在这。
"""

# ── 基准(起算)──────────────────────────────────────────────────────────────
START_DATE = "2026-06-18"        # 起算日
START_CAPITAL = 1_000_000        # 起始本金(港币)= 基准 100%
CURRENCY = "港币"

# ── 三档年度目标(复利,以"翻几倍"表示:100%→1.0)──────────────────────────
TIERS = [
    {"name": "保底", "label": "保底 · 100%", "annual": 1.0, "color": "#3DD68C"},
    {"name": "进取", "label": "进取 · 300%", "annual": 3.0, "color": "#F5B544"},
    {"name": "梦想", "label": "梦想 · 900%", "annual": 9.0, "color": "#FF2D78"},
]

# ── 风控阈值(%)─────────────────────────────────────────────────────────────
RISK = {
    "take_profit_pct": 10,    # 单日浮盈 ≥ +10% → 强制止盈
    "drawdown_pct": -3,       # 回撤 ≤ -3% → 纪律清仓线
    "deadline_pct": -4,       # 回撤 ≤ -4% → 血红死线
}

# ── 女儿锚点(港币)——话术换算用,可改 ──────────────────────────────────────
ANCHORS = {
    "piano_year_hkd": 16000,  # 一年钢琴课 ≈ 1.6 万港币
    "braces_hkd": 38000,      # 一次牙齿矫正 ≈ 3.8 万港币
}

# ── Google Sheet ─────────────────────────────────────────────────────────────
SHEET_NAME = "望望数据库"
WORKSHEET = "daily_account"
HEADERS = ["date", "total_value", "day_pnl_pct", "cum_return_pct",
           "peak_value", "drawdown_pct", "note"]

# ── 密码(部署时在 Secrets 设 APP_PASSWORD;没设用这个)──────────────────────
DEFAULT_PASSWORD = "wangwang2026"

# ── 配色(Power Magenta 玫红力量)────────────────────────────────────────────
THEME = {
    "ink": "#15090f", "panel": "#1e0e17", "panel2": "#241019", "line": "#3a2030",
    "txt": "#f5eaf0", "muted": "#b89aaa",
    "magenta": "#ff2d78", "magenta2": "#e6007a",
    "green": "#3dd68c", "red": "#ff4d4d", "amber": "#f5b544", "gold": "#e8c8a0",
}
