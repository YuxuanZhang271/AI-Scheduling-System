# data_preprocessing.py
# Robust preprocessing:
# - Reads stats_check.csv and schedule.csv from current directory.
# - For each task row (user, date), linearly interpolates Energy/Pressure
#   at the task's start/end time using that user's stats on the same date.
# - Task Energy/Pressure = value_at_end - value_at_start.
# - Handles all edge cases (beginning/end of day, single-point day, no data).
# - No chained assignment; no out-of-bounds indices.

import pandas as pd
import numpy as np
from datetime import datetime, date, time

STATS_PATH = "stats_check.csv"
TASKS_PATH = "schedule.csv"
OUT_PATH   = "new_tasks_df.csv"

# ---------- Helpers ----------

def _to_time(x) -> time | None:
    """Parse a time-of-day from arbitrary string; return None on failure."""
    if pd.isna(x):
        return None
    try:
        # pandas handles formats like '5:00:00 PM', '09:10', etc.
        return pd.to_datetime(x, errors="raise").time()
    except Exception:
        return None

def _combine(d: date, t: time) -> np.datetime64:
    """Combine date and time to numpy datetime64[ns]."""
    return np.datetime64(datetime.combine(d, t))

def _bracket_pair(ts: np.ndarray, query_t: np.datetime64) -> tuple[int, int] | None:
    """
    Given a strictly non-decreasing ts[0..n-1] (datetime64[ns]) and a query time,
    return a valid adjacent pair (i0, i1) such that i0 in [0, n-2], i1 = i0+1.
    If n == 0 -> None; if n == 1 -> (0,0) (degenerate).
    Otherwise, clamp to first/last segment.
    """
    n = len(ts)
    if n == 0:
        return None
    if n == 1:
        return (0, 0)
    pos = np.searchsorted(ts, query_t, side="left")
    i0 = max(0, min(pos - 1, n - 2))
    return (i0, i0 + 1)

def _interp_at(ts: np.ndarray, vs: np.ndarray, query_t: np.datetime64) -> float | None:
    """
    Linear interpolation of vs at query_t over time grid ts (datetime64[ns]).
    Returns vs[0] if n==1; None if n==0.
    """
    n = len(ts)
    if n == 0:
        return None
    if n == 1:
        return float(vs[0])

    i0, i1 = _bracket_pair(ts, query_t)
    t0, t1 = ts[i0], ts[i1]
    v0, v1 = float(vs[i0]), float(vs[i1])

    # Guard degenerate segment
    denom = (t1 - t0) / np.timedelta64(1, "ns")
    if denom == 0:
        return v0
    numer = (query_t - t0) / np.timedelta64(1, "ns")
    alpha = float(numer / denom)
    return v0 + alpha * (v1 - v0)

# ---------- Load data ----------

stats_df = pd.read_csv(STATS_PATH)
tasks_df = pd.read_csv(TASKS_PATH)

# Basic checks (optional but helpful)
required_stats_cols = {"Timestamp", "Name", "Energy", "Pressure"}
required_tasks_cols = {"Timestamp", "User name", "Task type", "Start time", "End time", "Difficulty"}
missing_s = required_stats_cols - set(stats_df.columns)
missing_t = required_tasks_cols - set(tasks_df.columns)
if missing_s:
    raise ValueError(f"stats_check.csv missing columns: {sorted(missing_s)}")
if missing_t:
    raise ValueError(f"schedule.csv missing columns: {sorted(missing_t)}")

# Parse timestamps
stats_df["timestamp"] = pd.to_datetime(stats_df["Timestamp"], errors="coerce")
tasks_df["row_timestamp"] = pd.to_datetime(tasks_df["Timestamp"], errors="coerce")

# Derive per-row date for grouping/lookup
stats_df["date"] = stats_df["timestamp"].dt.date
tasks_df["date"] = tasks_df["row_timestamp"].dt.date

# Keep only rows with valid timestamps
stats_df = stats_df.dropna(subset=["timestamp"]).copy()
tasks_df = tasks_df.dropna(subset=["row_timestamp"]).copy()

# Pre-group stats by (Name, date) with sorted time arrays for fast interpolation
# Store as dict[(name, date)] -> dict of arrays
grouped = {}
for (nm, d), g in stats_df.groupby(["Name", "date"], as_index=False):
    g = g.sort_values("timestamp").reset_index(drop=True)
    grouped[(nm, d)] = {
        "ts": g["timestamp"].to_numpy(dtype="datetime64[ns]"),
        "energy": g["Energy"].to_numpy(dtype=float),
        "pressure": g["Pressure"].to_numpy(dtype=float),
    }

# ---------- Compute per-task deltas ----------

out_rows = []
for idx, row in tasks_df.iterrows():
    user = row["User name"]
    d: date = row["date"]

    st = _to_time(row["Start time"])
    et = _to_time(row["End time"])

    # Prepare output row (start as a copy of task row)
    new_row = row.to_dict()

    # Defaults if we can't compute
    new_row["Energy"] = np.nan
    new_row["Pressure"] = np.nan

    # Validate presence of user/day and times
    g = grouped.get((user, d))
    if g is None or st is None or et is None:
        out_rows.append(new_row)
        continue

    # Build absolute query times
    t_start = _combine(d, st)
    t_end   = _combine(d, et)

    # If end < start (cross-midnight or input mistake), swap to be safe
    if t_end < t_start:
        t_start, t_end = t_end, t_start

    ts = g["ts"]
    en = g["energy"]
    pr = g["pressure"]

    # Handle empty stats (should be covered by g is None)
    if ts.size == 0:
        out_rows.append(new_row)
        continue

    e_start = _interp_at(ts, en, t_start)
    e_end   = _interp_at(ts, en, t_end)
    p_start = _interp_at(ts, pr, t_start)
    p_end   = _interp_at(ts, pr, t_end)

    # If any interpolation fails (shouldn't), leave NaN
    if None in (e_start, e_end, p_start, p_end):
        out_rows.append(new_row)
        continue

    new_row["Energy"]   = float(e_end - e_start)
    new_row["Pressure"] = float(p_end - p_start)
    out_rows.append(new_row)

# Assemble output DataFrame with the original task columns + computed fields
orig_cols = ["Timestamp", "User name", "Task type", "Start time", "End time", "Difficulty"]
extra_cols = ["Energy", "Pressure"]
new_tasks_df = pd.DataFrame(out_rows, columns=orig_cols + extra_cols)

# Save
new_tasks_df.to_csv(OUT_PATH, index=False)

print(f"Saved: {OUT_PATH}")
