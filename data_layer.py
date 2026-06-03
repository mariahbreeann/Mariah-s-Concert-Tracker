"""
data_layer.py — loads the watchlist, enriches with Ticketmaster data,
and returns a single merged DataFrame used by all dashboard views.
"""

import os
import json
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from ticketmaster import search_all_regions

CACHE_DIR = Path(".cache")
CACHE_TTL_HOURS = 12          # re-fetch from TM after this many hours
WATCHLIST_PATH = Path("watchlist.xlsx")


# ── Watchlist ──────────────────────────────────────────────────────────────

def load_watchlist() -> pd.DataFrame:
    """Read the Watchlist sheet from watchlist.xlsx."""
    df = pd.read_excel(WATCHLIST_PATH, sheet_name="Watchlist", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Normalize column names to snake_case keys
    rename = {
        "Artist":           "artist",
        "Venue":            "venue_manual",
        "City":             "city_manual",
        "State":            "state_manual",
        "Show Date":        "show_date_manual",
        "Date Range Start": "date_range_start",
        "Date Range End":   "date_range_end",
        "Plan to Attend":   "plan_to_attend",
        "Attended":         "attended",
        "Budget / Ticket":  "budget",
        "Actual / Ticket":  "actual",
        "Notes":            "notes",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Convert numeric columns
    for col in ("budget", "actual"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill blank attended/plan values with sensible defaults
    if "attended" in df.columns:
        df["attended"] = df["attended"].fillna("No").str.strip()
    if "plan_to_attend" in df.columns:
        df["plan_to_attend"] = df["plan_to_attend"].fillna("Yes").str.strip()

    # Parse dates
    for col in ("date_range_start", "date_range_end", "show_date_manual"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    # Drop blank rows
    df = df.dropna(subset=["artist"])
    df["artist"] = df["artist"].str.strip()
    return df


# ── Ticketmaster cache ─────────────────────────────────────────────────────

def _cache_key(artist: str, start: date, end: date) -> str:
    raw = f"{artist}|{start}|{end}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(hours=CACHE_TTL_HOURS)


def fetch_events_cached(artist: str, start: date, end: date) -> list[dict]:
    key  = _cache_key(artist, start, end)
    path = _cache_path(key)

    if _is_fresh(path):
        with open(path) as f:
            data = json.load(f)
        # Rehydrate date objects
        for ev in data:
            if ev.get("show_date_str"):
                ev["show_date"] = datetime.strptime(ev["show_date_str"], "%Y-%m-%d").date()
        return data

    try:
        events = search_all_regions(artist, start, end)
        # Serialize dates
        serializable = []
        for ev in events:
            e = dict(ev)
            if isinstance(e.get("show_date"), date):
                e["show_date"] = None          # will be rebuilt from show_date_str on reload
            serializable.append(e)
        with open(path, "w") as f:
            json.dump(serializable, f, default=str)
        return events
    except Exception as exc:
        st.warning(f"Ticketmaster fetch failed for '{artist}': {exc}")
        return []


# ── Merge ──────────────────────────────────────────────────────────────────

def build_merged_df(watchlist: pd.DataFrame) -> pd.DataFrame:
    """
    For each row in the watchlist, fetch matching TM events and pick the
    best match (same date if provided, otherwise first result).
    Falls back to manual watchlist data when TM returns nothing.
    """
    rows = []

    for _, wl in watchlist.iterrows():
        artist      = wl["artist"]
        start       = wl.get("date_range_start") or date(2025, 7, 1)
        end         = wl.get("date_range_end")   or date(2025, 12, 31)
        manual_date = wl.get("show_date_manual")

        tm_events = fetch_events_cached(artist, start, end)

        # Pick best matching TM event
        tm = None
        if tm_events:
            if manual_date:
                # Prefer exact date match
                exact = [e for e in tm_events if e.get("show_date") == manual_date]
                tm = exact[0] if exact else tm_events[0]
            else:
                tm = tm_events[0]

        row = {
            "artist":        artist,
            "plan_to_attend": wl.get("plan_to_attend", "Yes"),
            "attended":       wl.get("attended", "No"),
            "budget":         wl.get("budget"),
            "actual":         wl.get("actual"),
            "notes":          wl.get("notes", ""),
        }

        if tm:
            row.update({
                "venue":     tm.get("venue")     or wl.get("venue_manual"),
                "city":      tm.get("city")      or wl.get("city_manual"),
                "state":     tm.get("state")     or wl.get("state_manual"),
                "lat":       tm.get("lat"),
                "lon":       tm.get("lon"),
                "show_date": tm.get("show_date") or manual_date,
                "price_min": tm.get("price_min"),
                "price_max": tm.get("price_max"),
                "tm_url":    tm.get("url"),
                "tm_matched": True,
            })
        else:
            row.update({
                "venue":      wl.get("venue_manual"),
                "city":       wl.get("city_manual"),
                "state":      wl.get("state_manual"),
                "lat":        None,
                "lon":        None,
                "show_date":  manual_date,
                "price_min":  None,
                "price_max":  None,
                "tm_url":     None,
                "tm_matched": False,
            })

        rows.append(row)

    df = pd.DataFrame(rows)

    # Computed columns
    df["dollar_variance"] = df["actual"] - df["budget"]
    df["pct_variance"]    = ((df["actual"] - df["budget"]) / df["budget"]).where(
        df["budget"].notna() & df["actual"].notna()
    )
    df["show_date"] = pd.to_datetime(df["show_date"], errors="coerce")

    return df


# ── Convenience loader (cached by Streamlit) ───────────────────────────────

@st.cache_data(ttl=CACHE_TTL_HOURS * 3600, show_spinner="Loading concert data…")
def get_data() -> pd.DataFrame:
    watchlist = load_watchlist()
    return build_merged_df(watchlist)
