# Concert Tracker 🎵

A Streamlit dashboard that pulls your upcoming concerts from the Ticketmaster API,
plots them on a calendar and map, and tracks your ticket budget vs actual spend.

---

## Setup (first time, ~5 minutes)

### 1. Get a free Ticketmaster API key

1. Go to https://developer.ticketmaster.com
2. Sign up and create an app under **My Apps**
3. Copy your **Consumer Key**

### 2. Clone / download this folder

```
concert-tracker/
├── app.py
├── ticketmaster.py
├── data_layer.py
├── watchlist.xlsx       ← your show list
├── requirements.txt
├── .env.example
└── README.md
```

### 3. Install Python dependencies

Requires Python 3.11+.

```bash
cd concert-tracker
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
# Now open .env and replace  your_consumer_key_here  with your actual key
```

### 5. Edit your watchlist

Open `watchlist.xlsx` and fill in your shows:

| Column | What to enter |
|---|---|
| Artist | Artist name exactly as on Ticketmaster |
| Venue | Optional — used as fallback if API doesn't find it |
| City / State | Fallback location |
| Show Date | Exact date if you know it (YYYY-MM-DD) |
| Date Range Start/End | The window to search in Ticketmaster |
| Plan to Attend | Yes / Maybe / No |
| Attended | Yes / No (update after the show) |
| Budget / Ticket | What you plan to spend |
| Actual / Ticket | What you actually paid (fill in after) |

### 6. Run the app

```bash
streamlit run app.py
```

Opens at http://localhost:8501

---

## How it works

```
watchlist.xlsx  +  Ticketmaster API
        ↓
    data_layer.py  (merge + cache)
        ↓
    app.py  (Streamlit dashboard)
        ├── 📅 Calendar — month grid Jul–Dec, color-coded by status
        ├── 🗺️ Map      — Plotly mapbox, NorCal + Las Vegas pins
        └── 📊 Tracker  — editable budget table + bar chart
```

API results are cached locally in `.cache/` for 12 hours so you don't burn through
your rate limit on every reload.

---

## Adding more artists

Just add a new row to `watchlist.xlsx`. The app will fetch from Ticketmaster
automatically on next load (or hit **Refresh data** in the sidebar).

---

## Troubleshooting

**"TICKETMASTER_API_KEY not set"** → Make sure `.env` exists (not just `.env.example`)
and has your real key.

**Artist not found** → Try the exact spelling from Ticketmaster's website. You can
test in `ticketmaster.py` directly:
```bash
python ticketmaster.py
```

**Map shows no pins** → Ticketmaster coordinates load with the API. Without a valid
key, the map uses approximate city-center coordinates as a fallback.

**Dates wrong** → Check `Date Range Start` and `Date Range End` in your watchlist
cover the actual show date.
