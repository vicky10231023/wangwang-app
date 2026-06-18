"""
app.py —— 开心的望望 · V1 核心纪律
今日打卡 → 三档复利目标进度 → 止盈/回撤/死线警报 + 女儿话术 → 存 Google Sheet
运行: streamlit run app.py
"""
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import config as C
import logic as L

st.set_page_config(page_title="开心的望望", page_icon="💗", layout="wide")
T = C.THEME


# ════════════════════════════════════════════════════════════════════════════
# 主题
# ════════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap');
    .stApp {{ background: radial-gradient(1100px 600px at 80% -10%, #2a0f1f 0%, {T['ink']} 55%); }}
    .block-container {{ padding-top: 2rem; max-width: 1120px; }}
    h1,h2,h3 {{ color:{T['txt']}; font-family:'Space Grotesk',-apple-system,system-ui,sans-serif; }}
    .brand {{ font-size:34px; font-weight:700; color:{T['magenta']}; letter-spacing:-.01em; }}
    .tag {{ color:{T['muted']}; font-size:13px; }}
    .mc-row {{ display:flex; flex-wrap:wrap; gap:12px; margin:8px 0 16px; }}
    .mc {{ flex:1 1 150px; min-width:150px; background:{T['panel']}; border:1px solid {T['line']};
           border-radius:14px; padding:13px 16px; }}
    .mc .nm {{ font-size:12px; color:{T['muted']}; }}
    .mc .vl {{ font-size:23px; font-weight:700; color:{T['txt']};
              font-family:'JetBrains Mono',monospace; margin-top:3px; }}
    .alert {{ border-radius:16px; padding:18px 20px; margin:10px 0; white-space:pre-wrap;
             font-size:15px; line-height:1.7; font-weight:500; }}
    .alert.good {{ background:linear-gradient(135deg,#3a1228,#2a0f1f); border:2px solid {T['magenta']}; color:#ffe3ef; }}
    .alert.danger {{ background:#2a0f12; border:2px solid {T['red']}; color:#ffd9d9; }}
    .alert.deadline {{ background:#3a0a0a; border:3px solid {T['red']}; color:#ffcaca;
                      box-shadow:0 0 0 3px rgba(255,77,77,.25); }}
    .pill {{ display:inline-block; padding:5px 14px; border-radius:999px; font-weight:700; font-size:13px; }}
    .prog {{ background:{T['panel2']}; border-radius:999px; height:12px; overflow:hidden; margin:4px 0; }}
    .progfill {{ height:100%; border-radius:999px; }}
    .note {{ background:{T['panel2']}; border:1px solid {T['line']}; border-radius:12px;
            padding:12px 16px; color:{T['muted']}; font-size:13px; }}
    </style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Google Sheet 数据层
# ════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_ws():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open(C.SHEET_NAME)
    try:
        ws = sh.worksheet(C.WORKSHEET)
    except Exception:
        ws = sh.add_worksheet(title=C.WORKSHEET, rows=1000, cols=len(C.HEADERS))
    # 确保表头
    first = ws.row_values(1)
    if first != C.HEADERS:
        ws.update(values=[C.HEADERS], range_name="A1")
    return ws


@st.cache_data(ttl=60, show_spinner=False)
def read_df():
    ws = get_ws()
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").reset_index(drop=True)
    return df


def upsert_today(date, total_value, note=""):
    """按日期写入/更新一行;自动算盈亏、累计、峰值、回撤。"""
    ws = get_ws()
    df = read_df()
    if df.empty or "date" not in df.columns:
        prev_value, prev_peak, existing = None, None, []
    else:
        prev = df[df["date"] < date]
        prev_value = float(prev.iloc[-1]["total_value"]) if not prev.empty else None
        prev_peak = float(prev["peak_value"].max()) if not prev.empty else None
        existing = df.index[df["date"] == date].tolist()
    m = L.compute_row(C.START_CAPITAL, prev_value, prev_peak, float(total_value))
    row = [str(date), float(total_value), m["day_pnl_pct"], m["cum_return_pct"],
           m["peak_value"], m["drawdown_pct"], note]
    # 同日存在则更新,否则追加
    if existing:
        r = existing[0] + 2  # +2: 表头 + 0索引
        ws.update(values=[row], range_name=f"A{r}")
    else:
        ws.append_row(row)
    read_df.clear()  # 写入后清缓存,下次读最新
    return m


# ════════════════════════════════════════════════════════════════════════════
# 密码门
# ════════════════════════════════════════════════════════════════════════════
def password():
    try:
        return st.secrets.get("APP_PASSWORD", C.DEFAULT_PASSWORD)
    except Exception:
        return C.DEFAULT_PASSWORD


def gate():
    if st.session_state.get("ok"):
        return True
    st.markdown('<div class="brand">开心的望望 💗</div>', unsafe_allow_html=True)
    st.caption("私人作战室 · 请输入密码")
    pw = st.text_input("密码", type="password", label_visibility="collapsed")
    if st.button("进入"):
        if pw == password():
            st.session_state["ok"] = True; st.rerun()
        else:
            st.error("密码不对")
    return False


# ════════════════════════════════════════════════════════════════════════════
# 页面块
# ════════════════════════════════════════════════════════════════════════════
def cards(items):
    html = '<div class="mc-row">'
    for nm, vl, color in items:
        html += f'<div class="mc"><div class="nm">{nm}</div><div class="vl" style="color:{color}">{vl}</div></div>'
    st.markdown(html + '</div>', unsafe_allow_html=True)


def section_checkin():
    st.markdown("### 📌 今日打卡")
    st.caption(f"填一个数就好:你富途里**港币计价的账户总资产**。基准 = {C.START_CAPITAL:,.0f} {C.CURRENCY}(起算 {C.START_DATE})")
    c1, c2 = st.columns([1, 2])
    with c1:
        d = st.date_input("日期", value=dt.date.today())
    with c2:
        tv = st.number_input("账户总值(港币)", min_value=0.0, step=1000.0,
                             value=float(C.START_CAPITAL), format="%.0f")
    note = st.text_input("一句话备注(可选)", placeholder="今天做了什么 / 心情")
    if st.button("✅ 记录今天", type="primary"):
        try:
            upsert_today(d, tv, note)
            st.success("记好了。下面看看战况 👇")
            st.rerun()
        except Exception as e:
            st.error(f"写入失败:{e}")


def section_alerts(latest):
    if latest is None:
        return
    alerts = L.evaluate_alerts(latest["day_pnl_pct"], latest["drawdown_pct"], C.RISK)
    if not alerts:
        gaps = tier_gaps(latest)
        st.markdown(f'<div class="note">{L.daily_brief(latest["cum_return_pct"], gaps)}</div>',
                    unsafe_allow_html=True)
        return
    for level, kind in alerts:
        if kind == "take_profit":
            amt = latest["total_value"] - (latest["total_value"] / (1 + latest["day_pnl_pct"] / 100))
            msg = L.speak("take_profit", amt, C.ANCHORS)
        elif kind == "drawdown":
            amt = latest["peak_value"] - latest["total_value"]
            msg = L.speak("drawdown", amt, C.ANCHORS)
        else:
            amt = latest["peak_value"] - latest["total_value"]
            msg = L.speak("deadline", amt, C.ANCHORS)
        st.markdown(f'<div class="alert {level}">{msg}</div>', unsafe_allow_html=True)


def tier_gaps(latest):
    days = (dt.date.today() - dt.date.fromisoformat(C.START_DATE)).days
    gaps = {}
    for t in C.TIERS:
        exp = L.expected_value(C.START_CAPITAL, t["annual"], days)
        gaps[t["name"]] = max(exp - latest["total_value"], 0)
    return gaps


def section_progress(df, latest):
    st.markdown("### 🎯 目标进度(三档复利)")
    days = (dt.date.today() - dt.date.fromisoformat(C.START_DATE)).days
    # 卡片
    cards([
        ("当前账户", f'{latest["total_value"]:,.0f}', T["txt"]),
        ("累计收益", f'{latest["cum_return_pct"]:+.2f}%',
         T["green"] if latest["cum_return_pct"] >= 0 else T["red"]),
        ("当日盈亏", f'{latest["day_pnl_pct"]:+.2f}%',
         T["green"] if latest["day_pnl_pct"] >= 0 else T["red"]),
        ("当前回撤", f'{latest["drawdown_pct"]:.2f}%',
         T["red"] if latest["drawdown_pct"] <= -3 else T["muted"]),
    ])
    # 三档进度条
    for t in C.TIERS:
        mr = L.monthly_rate(t["annual"]) * 100
        exp = L.expected_value(C.START_CAPITAL, t["annual"], days)
        # 完成度 = 实际累计涨幅 / 目标至今应涨幅
        target_gain = exp - C.START_CAPITAL
        actual_gain = latest["total_value"] - C.START_CAPITAL
        pct = (actual_gain / target_gain * 100) if target_gain > 0 else 0
        pct_clamped = max(min(pct, 100), 0)
        ahead = "超前 🔥" if pct >= 100 else f"达成 {pct:.0f}%"
        st.markdown(
            f'<div style="margin-top:10px"><b style="color:{t["color"]}">{t["label"]}</b>'
            f'<span class="tag"> · 月需 {mr:.1f}% · 至今应到 {exp:,.0f} · {ahead}</span></div>'
            f'<div class="prog"><div class="progfill" style="width:{pct_clamped}%;background:{t["color"]}"></div></div>',
            unsafe_allow_html=True)
    # 曲线
    if len(df) >= 2:
        st.markdown("#### 累计走势 vs 三档目标线")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["total_value"], name="实际",
                                 line=dict(color=T["magenta"], width=3)))
        xs = list(df["date"])
        start_d = dt.date.fromisoformat(C.START_DATE)
        for t in C.TIERS:
            ys = [L.expected_value(C.START_CAPITAL, t["annual"], (d - start_d).days) for d in xs]
            fig.add_trace(go.Scatter(x=xs, y=ys, name=t["label"],
                                     line=dict(color=t["color"], width=1.5, dash="dot")))
        fig.update_layout(height=340, margin=dict(l=8, r=8, t=10, b=8),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color=T["muted"], size=11, family="JetBrains Mono"),
                          legend=dict(orientation="h", y=1.12),
                          xaxis=dict(gridcolor=T["line"]), yaxis=dict(gridcolor=T["line"]))
        st.plotly_chart(fig, use_container_width=True)


def section_history(df):
    if df.empty:
        return
    with st.expander("📒 历史记录"):
        show = df[["date", "total_value", "day_pnl_pct", "cum_return_pct", "drawdown_pct", "note"]].copy()
        show.columns = ["日期", "账户总值", "当日%", "累计%", "回撤%", "备注"]
        st.dataframe(show.iloc[::-1], hide_index=True, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    if not gate():
        return
    st.markdown('<div class="brand">开心的望望 💗</div>', unsafe_allow_html=True)
    st.markdown('<div class="tag">看清环境 · 有纪律地下注 · 守住纪律拿结果 —— 为她,稳稳地。</div>',
                unsafe_allow_html=True)
    st.write("")

    try:
        df = read_df()
    except Exception as e:
        msg = str(e)
        if "429" in msg or "Quota" in msg:
            st.warning("读取太频繁,撞到 Google 每分钟限速。等 1 分钟再刷新即可(已加缓存,后面不会再频繁了)。")
        else:
            st.error(f"连不上 Google Sheet:{e}")
            st.markdown('<div class="note">检查:① Secrets 里 gcp_service_account 填好了吗 '
                        '② 表「望望数据库」共享给 bot 邮箱(编辑者)了吗 ③ Sheets/Drive API 开了吗</div>',
                        unsafe_allow_html=True)
        return

    latest = df.iloc[-1].to_dict() if not df.empty else None

    section_checkin()
    st.divider()
    if latest:
        section_alerts(latest)
        section_progress(df, latest)
        section_history(df)
    else:
        st.markdown('<div class="note">还没有记录。在上面填今天的账户总值,开始第一天打卡 💗</div>',
                    unsafe_allow_html=True)

    st.markdown(f'<div style="color:{T["muted"]};font-size:11px;margin-top:24px;'
                f'border-top:1px solid {T["line"]};padding-top:12px">'
                f'开心的望望 · V1 · 仅供自我纪律,不构成投资建议 · 数据存你自己的 Google Sheet</div>',
                unsafe_allow_html=True)


main()


