"""
app.py — Concert Tracker dashboard (Streamlit + Plotly)
Old school tattoo flash aesthetic: cream/white background, black ink, red accents

Run:
    streamlit run app.py
"""

import math
import calendar
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from data_layer import get_data

# ── Color palette ──────────────────────────────────────────────────────────
# Tattoo flash: cream paper, black ink, red accent, gold highlight
CREAM       = "#F5F0E8"
CREAM_DARK  = "#EDE6D6"
BLACK       = "#1A1008"
RED         = "#C8231A"
RED_LIGHT   = "#E8453C"
GOLD        = "#C9963A"
GRAY        = "#8A8070"
GRAY_LIGHT  = "#D4CFC4"

# ── Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Mariah's Concert Tracker",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Special+Elite&family=Oswald:wght@400;600&display=swap');

  [data-testid="stAppViewContainer"] {{
      background: {CREAM};
  }}
  [data-testid="stSidebar"] {{
      background: {BLACK};
      border-right: 3px solid {RED};
  }}
  [data-testid="stSidebar"] * {{
      color: {CREAM} !important;
  }}
  [data-testid="stSidebar"] .stButton button {{
      background: {RED};
      color: {CREAM} !important;
      border: 2px solid {CREAM};
      font-family: 'Oswald', sans-serif;
      letter-spacing: 1px;
  }}
  h1, h2, h3 {{
      font-family: 'Special Elite', cursive !important;
      color: {BLACK} !important;
      letter-spacing: 1px;
  }}
  [data-testid="stMetricLabel"] {{
      color: {GRAY} !important;
      font-family: 'Oswald', sans-serif;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-size: 12px !important;
  }}
  [data-testid="stMetricValue"] {{
      color: {BLACK} !important;
      font-family: 'Special Elite', cursive !important;
      font-size: 28px !important;
  }}
  [data-testid="stTabs"] button {{
      font-family: 'Oswald', sans-serif;
      letter-spacing: 1px;
      color: {BLACK} !important;
      text-transform: uppercase;
  }}
  [data-testid="stTabs"] button[aria-selected="true"] {{
      color: {RED} !important;
      border-bottom: 3px solid {RED} !important;
  }}
  hr {{
      border-color: {GOLD};
      border-width: 2px;
  }}
  .stDataFrame {{
      border: 2px solid {BLACK};
  }}
  /* Metric boxes */
  [data-testid="metric-container"] {{
      background: {CREAM_DARK};
      border: 2px solid {BLACK};
      border-radius: 0px;
      padding: 12px;
      box-shadow: 3px 3px 0px {BLACK};
  }}
</style>
""", unsafe_allow_html=True)


# ── Load data ──────────────────────────────────────────────────────────────

df = get_data()

# ── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 16px 0 8px 0;'>
      <div style='font-size:48px;'>🎸</div>
      <div style='font-family:"Special Elite",cursive; font-size:20px;
                  color:{CREAM}; letter-spacing:2px; margin-top:6px;'>
        MARIAH'S CONCERT TRACKER
      </div>
      <div style='width:80%; height:2px; background:{RED};
                  margin:10px auto;'></div>
      <div style='font-family:"Oswald",sans-serif; font-size:11px;
                  color:{GOLD}; letter-spacing:2px; text-transform:uppercase;'>
        Jan — Dec 2026
      </div>
    </div>
    """, unsafe_allow_html=True)

    month_names = {m: calendar.month_abbr[m] for m in range(1, 13)}

    selected_months = st.multiselect(
        "Months",
        options=list(range(1, 13)),
        default=list(range(1, 13)),
        format_func=lambda m: month_names[m],
    )

    plan_filter = st.multiselect(
        "Plan to attend",
        options=["Yes", "Maybe", "No"],
        default=["Yes", "Maybe"],
    )

    attended_filter = st.multiselect(
        "Attended",
        options=["Yes", "No"],
        default=["Yes", "No"],
    )

    st.markdown("---")
    if st.button("🔄 Refresh from Ticketmaster"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Ticketmaster Discovery API + watchlist.xlsx")

# ── Filter ─────────────────────────────────────────────────────────────────

mask = (
    df["show_date"].dt.month.isin(selected_months) &
    df["plan_to_attend"].isin(plan_filter) &
    df["attended"].isin(attended_filter)
)
filtered = df[mask].copy()

# ── Header ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style='text-align:center; padding: 8px 0 4px 0;'>
  <h1 style='font-size:38px; margin-bottom:2px;'>🎸 Mariah's Concert Tracker</h1>
  <div style='width:200px; height:3px; background:{RED}; margin:0 auto 16px auto;'></div>
</div>
""", unsafe_allow_html=True)

# ── Summary metrics ────────────────────────────────────────────────────────

attended_df  = filtered[filtered["attended"] == "Yes"]
total_shows  = len(filtered)
attended_cnt = len(attended_df)
total_spent  = attended_df["actual"].sum()
total_budget = filtered["budget"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Shows tracked",    total_shows)
c2.metric("Attended",         attended_cnt)
c3.metric("Total spent",      f"${total_spent:,.0f}" if not math.isnan(total_spent or float("nan")) else "—")
c4.metric("Budget remaining", f"${(total_budget or 0) - (total_spent or 0):,.0f}" if not math.isnan((total_budget or 0) - (total_spent or 0)) else "—")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────

tab_calendar, tab_map, tab_table = st.tabs(["🎸  Calendar", "📍  Map", "💵  Tracker"])


# ╔══════════════════════════════════════════════════════╗
# ║  CALENDAR VIEW                                       ║
# ╚══════════════════════════════════════════════════════╝

with tab_calendar:
    st.subheader("Show Calendar — Jan through Dec 2026")

    cal_df = filtered.dropna(subset=["show_date"]).copy()
    cal_df["month"] = cal_df["show_date"].dt.month
    cal_df["day"]   = cal_df["show_date"].dt.day

    month_range = list(range(1, 13))
    cols_per_row = 3
    month_rows = [month_range[i:i+cols_per_row] for i in range(0, len(month_range), cols_per_row)]

    STATUS_COLORS = {
        "Yes-Yes":  RED,        # attended
        "Yes-No":   BLACK,      # planning
        "Maybe-No": GOLD,       # maybe
        "No-No":    GRAY,       # not planning
    }

    STATUS_FILLS = {
        "Yes-Yes":  "#F5D5D3",
        "Yes-No":   "#D8D4CC",
        "Maybe-No": "#F5EDD3",
        "No-No":    CREAM_DARK,
    }

    def status_color(row):
        key = f"{row.plan_to_attend}-{row.attended}"
        return STATUS_COLORS.get(key, BLACK)

    def status_fill(row):
        key = f"{row.plan_to_attend}-{row.attended}"
        return STATUS_FILLS.get(key, CREAM_DARK)

    for row_months in month_rows:
        cols = st.columns(cols_per_row)
        for col, month in zip(cols, row_months):
            with col:
                st.markdown(
                    f"<div style='font-family:Oswald,sans-serif; font-size:14px;"
                    f"letter-spacing:2px; text-transform:uppercase; color:{BLACK};"
                    f"border-bottom:2px solid {RED}; padding-bottom:4px; margin-bottom:4px;'>"
                    f"{calendar.month_name[month].upper()}</div>",
                    unsafe_allow_html=True
                )
                month_data = cal_df[cal_df["month"] == month]

                year = 2026
                first_dow, num_days = calendar.monthrange(year, month)

                grid = []
                week = [None] * first_dow
                for day in range(1, num_days + 1):
                    week.append(day)
                    if len(week) == 7:
                        grid.append(week)
                        week = []
                if week:
                    week += [None] * (7 - len(week))
                    grid.append(week)

                fig = go.Figure()
                day_labels = ["M", "T", "W", "T", "F", "S", "S"]

                for col_idx, lbl in enumerate(day_labels):
                    fig.add_annotation(
                        x=col_idx, y=len(grid),
                        text=f"<b>{lbl}</b>",
                        showarrow=False,
                        font=dict(size=10, color=GRAY),
                    )

                for row_idx, week_days in enumerate(grid):
                    for col_idx, day in enumerate(week_days):
                        if day is None:
                            continue

                        shows_today = month_data[month_data["day"] == day]
                        y_pos = len(grid) - 1 - row_idx

                        if shows_today.empty:
                            fig.add_shape(type="rect",
                                x0=col_idx-0.45, x1=col_idx+0.45,
                                y0=y_pos-0.45, y1=y_pos+0.45,
                                line=dict(color=GRAY_LIGHT, width=0.5),
                                fillcolor=CREAM,
                                opacity=1.0,
                            )
                            fig.add_annotation(
                                x=col_idx, y=y_pos,
                                text=str(day), showarrow=False,
                                font=dict(size=9, color=GRAY),
                            )
                        else:
                            show  = shows_today.iloc[0]
                            color = status_color(show)
                            fill  = status_fill(show)
                            tooltip = (
                                f"{show['artist']}<br>"
                                f"{show['venue'] or ''}<br>"
                                f"{show['city'] or ''}, {show['state'] or ''}"
                            )
                            fig.add_shape(type="rect",
                                x0=col_idx-0.45, x1=col_idx+0.45,
                                y0=y_pos-0.45, y1=y_pos+0.45,
                                line=dict(color=color, width=2),
                                fillcolor=fill,
                                opacity=1.0,
                            )
                            fig.add_trace(go.Scatter(
                                x=[col_idx], y=[y_pos],
                                mode="markers+text",
                                marker=dict(size=1, color="rgba(0,0,0,0)"),
                                text=[str(day)],
                                textfont=dict(size=9, color=color),
                                hovertext=[tooltip],
                                hoverinfo="text",
                                showlegend=False,
                            ))
                            short = show["artist"].split()[0][:8]
                            fig.add_annotation(
                                x=col_idx, y=y_pos - 0.28,
                                text=short,
                                showarrow=False,
                                font=dict(size=7, color=color),
                            )

                fig.update_layout(
                    height=200,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor=CREAM,
                    plot_bgcolor=CREAM,
                    xaxis=dict(visible=False, range=[-0.6, 6.6]),
                    yaxis=dict(visible=False, range=[-0.6, len(grid) + 0.6]),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"cal_{month}")

    st.markdown(
        f"<div style='font-size:12px; font-family:Oswald,sans-serif; letter-spacing:1px;'>"
        f"<span style='color:{RED}'>■</span> Attended &nbsp;&nbsp;"
        f"<span style='color:{BLACK}'>■</span> Planning to go &nbsp;&nbsp;"
        f"<span style='color:{GOLD}'>■</span> Maybe"
        f"</div>",
        unsafe_allow_html=True,
    )


# ╔══════════════════════════════════════════════════════╗
# ║  MAP VIEW                                            ║
# ╚══════════════════════════════════════════════════════╝

with tab_map:
    st.subheader("Venue Locations")

    city_coords = {
        ("Sacramento",    "CA"): (38.5816, -121.4944),
        ("San Francisco", "CA"): (37.7749, -122.4194),
        ("San Jose",      "CA"): (37.3382, -121.8863),
        ("Mountain View", "CA"): (37.3861, -122.0839),
        ("Inglewood",     "CA"): (33.9617, -118.3531),
        ("Los Angeles",   "CA"): (34.0522, -118.2437),
        ("Oakland",       "CA"): (37.8044, -122.2712),
        ("San Diego",     "CA"): (32.7157, -117.1611),
        ("Wheatland",     "CA"): (39.0046, -121.4227),
        ("Concord",       "CA"): (37.9780, -122.0311),
        ("Las Vegas",     "NV"): (36.1699, -115.1398),
        ("Reno",          "NV"): (39.5296, -119.8138),
    }

    # Fill in fallback coords for any row missing lat/lon
    map_df = filtered.dropna(subset=["city"]).copy()
    for idx, row in map_df.iterrows():
        if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
            key = (row.get("city", ""), row.get("state", ""))
            coords = city_coords.get(key)
            if coords:
                map_df.at[idx, "lat"] = coords[0]
                map_df.at[idx, "lon"] = coords[1]

    map_df = map_df.dropna(subset=["lat", "lon"])

    if not map_df.empty:
        map_df["show_date_str"] = map_df["show_date"].dt.strftime("%b %d, %Y")

        fig_map = px.scatter_mapbox(
            map_df,
            lat="lat", lon="lon",
            hover_name="artist",
            hover_data={
                "venue": True, "city": True, "state": True,
                "show_date_str": True, "plan_to_attend": True,
                "attended": True, "lat": False, "lon": False,
            },
            color="plan_to_attend",
            color_discrete_map={"Yes": RED, "Maybe": GOLD, "No": GRAY},
            size_max=18,
            zoom=5,
            center={"lat": 37.5, "lon": -119.5},
        )
        fig_map.update_traces(marker=dict(size=14))
        fig_map.update_layout(
            mapbox_style="carto-positron",
            paper_bgcolor=CREAM,
            margin=dict(l=0, r=0, t=0, b=0),
            height=560,
            legend=dict(
                bgcolor=CREAM_DARK,
                bordercolor=BLACK,
                borderwidth=2,
                font=dict(color=BLACK, family="Oswald"),
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True)

        venue_counts = (
            map_df.groupby(["venue", "city", "state"])
            .agg(shows=("artist", "count"))
            .reset_index()
            .sort_values("shows", ascending=False)
        )
        if len(venue_counts) > 0:
            st.markdown(f"<div style='font-family:Oswald,sans-serif; font-size:13px; letter-spacing:1px; text-transform:uppercase; color:{BLACK}; margin-top:12px;'>Shows per venue</div>", unsafe_allow_html=True)
            st.dataframe(venue_counts, use_container_width=True, hide_index=True)


# ╔══════════════════════════════════════════════════════╗
# ║  TRACKER TABLE                                       ║
# ╚══════════════════════════════════════════════════════╝

with tab_table:
    st.subheader("Budget Tracker")

    tracker_df = filtered.copy()
    tracker_df["show_date_fmt"] = tracker_df["show_date"].dt.strftime("%b %d, %Y")

    display_cols = {
        "artist":          "Artist",
        "show_date_fmt":   "Date",
        "venue":           "Venue",
        "city":            "City",
        "state":           "ST",
        "plan_to_attend":  "Plan",
        "attended":        "Attended",
        "budget":          "Budget/ticket",
        "actual":          "Actual/ticket",
        "dollar_variance": "$ +/–",
        "pct_variance":    "% +/–",
        "tm_url":          "Ticketmaster",
        "notes":           "Notes",
    }

    table = tracker_df[list(display_cols.keys())].rename(columns=display_cols)

    def style_pct(val):
        if pd.isna(val):
            return ""
        if val > 0:
            return f"color: {RED}; font-weight: bold"
        if val < 0:
            return f"color: {GOLD}; font-weight: bold"
        return ""

    styled = (
        table.style
        .applymap(style_pct, subset=["% +/–"])
        .format({
            "Budget/ticket": lambda v: f"${v:,.0f}" if pd.notna(v) else "—",
            "Actual/ticket": lambda v: f"${v:,.0f}" if pd.notna(v) else "—",
            "$ +/–":         lambda v: f"${v:+,.0f}" if pd.notna(v) else "—",
            "% +/–":         lambda v: f"{v:+.1%}"   if pd.notna(v) else "—",
        })
    )

    st.dataframe(styled, use_container_width=True, hide_index=True, column_config={
        "Ticketmaster": st.column_config.LinkColumn("Ticketmaster", display_text="🎸 Buy tickets"),
    })

    # Budget bar chart
    budget_chart_df = tracker_df.dropna(subset=["budget"]).copy()
    budget_chart_df["show_label"] = (
        budget_chart_df["artist"] + " (" +
        budget_chart_df["show_date"].dt.strftime("%b %d") + ")"
    )

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Budget",
        x=budget_chart_df["show_label"],
        y=budget_chart_df["budget"],
        marker_color=BLACK,
        marker_line_color=BLACK,
        marker_line_width=1,
    ))
    fig_bar.add_trace(go.Bar(
        name="Actual",
        x=budget_chart_df["show_label"],
        y=budget_chart_df["actual"],
        marker_color=RED,
        marker_line_color=BLACK,
        marker_line_width=1,
    ))
    fig_bar.update_layout(
        barmode="group",
        paper_bgcolor=CREAM,
        plot_bgcolor=CREAM,
        font=dict(color=BLACK, family="Oswald"),
        xaxis=dict(tickangle=-30, gridcolor=GRAY_LIGHT, linecolor=BLACK),
        yaxis=dict(title="$ per ticket", gridcolor=GRAY_LIGHT, linecolor=BLACK),
        legend=dict(
            bgcolor=CREAM_DARK,
            bordercolor=BLACK,
            borderwidth=1,
        ),
        height=350,
        margin=dict(l=0, r=0, t=10, b=80),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Totals
    total_budget_display = tracker_df["budget"].sum()
    total_actual_display = tracker_df["actual"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total budget", f"${total_budget_display:,.0f}" if pd.notna(total_budget_display) else "—")
    col2.metric("Total actual", f"${total_actual_display:,.0f}" if pd.notna(total_actual_display) else "—")
    if pd.notna(total_budget_display) and pd.notna(total_actual_display) and total_budget_display:
        delta_pct = (total_actual_display - total_budget_display) / total_budget_display
        col3.metric("Overall variance", f"{delta_pct:+.1%}", delta=f"${total_actual_display - total_budget_display:+,.0f}")