import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import itertools
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Taiwan 50 Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def _client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

@st.cache_data(ttl=1800)
def load_data(days: int) -> pd.DataFrame:
    since = (datetime.now() - timedelta(days=days)).date().isoformat()
    result = (
        _client()
        .table("stock_daily")
        .select("ticker,date,open,high,low,close,volume,daily_return,ma20,ma60,rsi,volatility,name,sector")
        .gte("date", since)
        .order("date")
        .execute()
    )
    df = pd.DataFrame(result.data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        num_cols = ["open","high","low","close","daily_return","ma20","ma60","rsi","volatility"]
        df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df

@st.cache_data(ttl=300)
def last_refresh() -> str:
    result = (
        _client()
        .table("refresh_log")
        .select("refreshed_at")
        .order("refreshed_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["refreshed_at"][:16].replace("T", " ") + " UTC"
    return "Not yet run"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Taiwan 50\nStock Intelligence")
    st.divider()
    page = st.radio(
        "Navigate",
        [
            "Market Overview",
            "Stock Explorer",
            "Technical Signals",
            "Sector Analysis",
            "Correlation",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    days = st.select_slider(
        "Lookback period",
        options=[30, 60, 90, 180, 365],
        value=90,
        format_func=lambda x: f"{x} days",
    )
    st.caption(f"Last pipeline run\n{last_refresh()}")
    if st.button("Clear cache"):
        st.cache_data.clear()
        st.rerun()

df = load_data(days)

if df.empty:
    st.error("No data in database. Run `python pipeline.py` first.")
    st.stop()

latest = df.sort_values("date").groupby("ticker").last().reset_index()

# ── Page 1: Market Overview ───────────────────────────────────────────────────
if page == "Market Overview":
    st.title("Taiwan 50 - Market Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stocks tracked", len(latest))
    n_up = int((latest["daily_return"] > 0).sum())
    n_dn = int((latest["daily_return"] < 0).sum())
    c2.metric("Gainers", n_up)
    c3.metric("Losers", n_dn)
    avg_r = latest["daily_return"].mean()
    c4.metric("Avg daily return", f"{avg_r:+.2f}%")

    st.divider()
    st.subheader("Performance heatmap")
    fig_map = px.treemap(
        latest,
        path=[px.Constant("Taiwan 50"), "sector", "name"],
        values="volume",
        color="daily_return",
        color_continuous_scale=["#1a9850", "#f7f7f7", "#d73027"],
        color_continuous_midpoint=0,
        hover_data={"daily_return": ":.2f", "close": ":,.0f"},
    )
    fig_map.update_layout(height=480, margin=dict(t=10, l=0, r=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 gainers")
        top = (latest.nlargest(5, "daily_return")
               [["name","close","daily_return","volume"]]
               .rename(columns={"name":"Company","close":"Price (TWD)","daily_return":"Return %","volume":"Volume"}))
        top["Return %"] = top["Return %"].map("{:+.2f}%".format)
        st.dataframe(top, hide_index=True, use_container_width=True)
    with col2:
        st.subheader("Top 5 losers")
        bot = (latest.nsmallest(5, "daily_return")
               [["name","close","daily_return","volume"]]
               .rename(columns={"name":"Company","close":"Price (TWD)","daily_return":"Return %","volume":"Volume"}))
        bot["Return %"] = bot["Return %"].map("{:+.2f}%".format)
        st.dataframe(bot, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader(f"Cumulative returns - top 5 stocks (last {days} days)")
    top5_tkrs = df.groupby("ticker")["daily_return"].mean().nlargest(5).index.tolist()
    df5 = df[df["ticker"].isin(top5_tkrs)].sort_values(["ticker","date"]).copy()
    first_close = df5.groupby("ticker")["close"].transform("first")
    df5["cum_ret"] = (df5["close"] / first_close - 1) * 100
    fig_cum = px.line(df5, x="date", y="cum_ret", color="name",
                      labels={"cum_ret": "Cumulative return (%)", "date": ""})
    fig_cum.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
    fig_cum.update_layout(height=360, legend_title_text="")
    st.plotly_chart(fig_cum, use_container_width=True)

# ── Page 2: Stock Explorer ────────────────────────────────────────────────────
elif page == "Stock Explorer":
    st.title("Stock Explorer")

    tickers = sorted(df["ticker"].unique())
    name_map = df[["ticker","name"]].drop_duplicates().set_index("ticker")["name"].to_dict()
    sel = st.selectbox("Select a stock", tickers,
                       format_func=lambda t: f"{t}  {name_map.get(t,t)}")

    s = df[df["ticker"] == sel].sort_values("date")
    if s.empty:
        st.warning("No data for selected stock.")
        st.stop()

    row = s.iloc[-1]
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Close (TWD)", f"{row['close']:,.1f}", f"{row['daily_return']:+.2f}%")
    c2.metric("MA20", f"{row['ma20']:,.1f}")
    c3.metric("MA60", f"{row['ma60']:,.1f}")
    rsi_val = row["rsi"]
    rsi_lbl = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
    c4.metric("RSI 14", f"{rsi_val:.1f}", rsi_lbl)
    c5.metric("Ann. volatility", f"{row['volatility']:.1f}%")

    fig_cs = go.Figure()
    fig_cs.add_trace(go.Candlestick(
        x=s["date"], open=s["open"], high=s["high"], low=s["low"], close=s["close"],
        increasing_line_color="#e74c3c", decreasing_line_color="#2ecc71", name="OHLC"))
    fig_cs.add_trace(go.Scatter(x=s["date"], y=s["ma20"], name="MA20",
                                line=dict(color="#f39c12", width=1.5)))
    fig_cs.add_trace(go.Scatter(x=s["date"], y=s["ma60"], name="MA60",
                                line=dict(color="#3498db", width=1.5)))
    fig_cs.update_layout(title=f"{sel} - {name_map.get(sel,'')}",
                         height=420, xaxis_rangeslider_visible=False,
                         template="plotly_white", legend=dict(orientation="h", y=1.02))
    st.plotly_chart(fig_cs, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        colors = ["#e74c3c" if r >= 0 else "#2ecc71" for r in s["daily_return"].fillna(0)]
        fig_vol = go.Figure(go.Bar(x=s["date"], y=s["volume"], marker_color=colors))
        fig_vol.update_layout(title="Volume", height=260, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_vol, use_container_width=True)
    with col2:
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.06, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.06, line_width=0)
        fig_rsi.add_trace(go.Scatter(x=s["date"], y=s["rsi"], name="RSI",
                                     line=dict(color="#9b59b6", width=1.5)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.8)
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8)
        fig_rsi.update_layout(title="RSI (14)", height=260, template="plotly_white",
                               yaxis=dict(range=[0,100]), showlegend=False)
        st.plotly_chart(fig_rsi, use_container_width=True)

# ── Page 3: Technical Signals ─────────────────────────────────────────────────
elif page == "Technical Signals":
    st.title("Technical Signals Scanner")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RSI alerts")
        oversold   = latest[latest["rsi"] < 30][["name","ticker","rsi","close"]].sort_values("rsi")
        overbought = latest[latest["rsi"] > 70][["name","ticker","rsi","close"]].sort_values("rsi", ascending=False)
        st.markdown("**Oversold - RSI < 30 (potential buy zone)**")
        if not oversold.empty:
            st.dataframe(oversold.rename(columns={"name":"Company","close":"Price (TWD)"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("No oversold stocks at this time.")
        st.markdown("**Overbought - RSI > 70 (potential sell zone)**")
        if not overbought.empty:
            st.dataframe(overbought.rename(columns={"name":"Company","close":"Price (TWD)"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("No overbought stocks at this time.")
    with col2:
        st.subheader("Risk-return scatter")
        fig_rr = px.scatter(latest, x="volatility", y="daily_return", color="sector",
                            hover_name="name", hover_data={"ticker": True, "close": ":,.0f"},
                            labels={"volatility":"Ann. volatility (%)","daily_return":"Daily return (%)"})
        fig_rr.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
        fig_rr.update_layout(height=340, legend_title_text="Sector")
        st.plotly_chart(fig_rr, use_container_width=True)

    st.divider()
    st.subheader("MA crossover signals")
    latest["signal"] = np.where(latest["ma20"] > latest["ma60"],
                                "Golden cross (MA20 > MA60)",
                                "Death cross (MA20 < MA60)")
    sig_df = latest[["name","ticker","close","ma20","ma60","signal"]].copy()
    sig_df.columns = ["Company","Ticker","Price (TWD)","MA20","MA60","Signal"]
    st.dataframe(sig_df, hide_index=True, use_container_width=True)

# ── Page 4: Sector Analysis ───────────────────────────────────────────────────
elif page == "Sector Analysis":
    st.title("Sector Analysis")

    sector = (latest.groupby("sector")
              .agg(avg_return=("daily_return","mean"), avg_rsi=("rsi","mean"),
                   avg_vol=("volatility","mean"), count=("ticker","count"),
                   total_volume=("volume","sum"))
              .reset_index().round(2))

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(sector.sort_values("avg_return"),
                         x="avg_return", y="sector", orientation="h",
                         color="avg_return",
                         color_continuous_scale=["#1a9850","#f7f7f7","#d73027"],
                         color_continuous_midpoint=0,
                         title="Average daily return by sector (%)",
                         labels={"avg_return":"Return (%)","sector":""})
        fig_bar.update_coloraxes(showscale=False)
        fig_bar.update_layout(height=380)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        fig_scat = px.scatter(sector, x="avg_vol", y="avg_return",
                              size="count", color="sector", text="sector",
                              title="Sector risk-return profile",
                              labels={"avg_vol":"Avg volatility (%)","avg_return":"Avg return (%)"})
        fig_scat.update_traces(textposition="top center")
        fig_scat.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
        fig_scat.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_scat, use_container_width=True)

    st.subheader("Sector summary table")
    sector.columns = ["Sector","Avg return (%)","Avg RSI","Avg volatility (%)","# stocks","Total volume"]
    st.dataframe(sector, hide_index=True, use_container_width=True)

# ── Page 5: Correlation ───────────────────────────────────────────────────────
elif page == "Correlation":
    st.title("Correlation Analysis")

    st.info(
        "Correlation measures how similarly two stocks move. "
        "Close to +1 = move together (concentrated risk). "
        "Close to -1 = move oppositely (good for diversification). "
        "Close to 0 = independent."
    )

    pivot = df.pivot_table(index="date", columns="ticker", values="daily_return")
    name_map = df[["ticker","name"]].drop_duplicates().set_index("ticker")["name"].to_dict()
    pivot.columns = [name_map.get(t, t) for t in pivot.columns]
    corr = pivot.corr().round(2)

    fig_corr = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        zmin=-1, zmax=1,
        title=f"Return correlation matrix (last {days} days)",
        text_auto=True,
        aspect="auto",
    )
    fig_corr.update_layout(height=620)
    st.plotly_chart(fig_corr, use_container_width=True)

    st.divider()
    st.subheader("Correlation ranking")
    pairs = []
    cols_list = list(corr.columns)
    for i, j in itertools.combinations(range(len(cols_list)), 2):
        pairs.append({"Stock A": cols_list[i], "Stock B": cols_list[j],
                      "Correlation": corr.iloc[i, j]})
    pairs_df = pd.DataFrame(pairs).sort_values("Correlation", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Highest positive correlation (concentrated risk)**")
        st.dataframe(pairs_df.head(5).reset_index(drop=True),
                     hide_index=True, use_container_width=True)
    with c2:
        st.markdown("**Lowest correlation (best diversification)**")
        st.dataframe(pairs_df.tail(5).reset_index(drop=True),
                     hide_index=True, use_container_width=True)
