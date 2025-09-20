#!/usr/bin/env python3

"""
IOB Calculator (CLI)
--------------------

Compute Insulin On Board (IOB) for one or more boluses using an oref-style
exponential (gamma-variate) model.

Input format
============
- Arguments are given as **pairs**: (units, time).
- `units`: insulin units (float).
- `time`: either
    * elapsed minutes (int/float), e.g. 30, 120
    * or a clock time 'HH:MM' in 24h format, e.g. 22:30, 01:10.
      Times later than the current system time are assumed to be *yesterday*,
      but ignored if older than DIA hours.

- Multiple doses can be supplied as repeated pairs:
    1.0 30   2.0 120   0.8 290
    1.0 22:30  2.0 23:00  0.8 01:10

Options
=======
--dia, --DIA  H        Duration of insulin action in hours (default: 5)
--peak, --PEAK M       Peak activity time in minutes (default: 75)
--breakdown    Show per-dose contributions
--no-round     Disable rounding (for debugging)
 --shape-n SHAPE_N    Shape parameter n (gamma-variate). (default: 3)

Examples
========
1) Single bolus, 1U 30 minutes ago:
   $ python iob.py 1.0 30

2) Multiple boluses, elapsed minutes:
   $ python iob.py 1.0 30  2.0 120  0.8 290

3) Boluses around midnight using HH:MM:
   $ python iob.py 1.0 22:30  2.0 23:00  0.8 01:10

4) With breakdown and custom DIA/PEAK:
   $ python iob.py 1.0 30  2.0 120 --dia 4.5 --peak 60 --breakdown

Output
======
By default prints the total IOB (rounded to 2 decimals). With --breakdown,
also prints each dose as:  <units> U, <elapsed> min -> <iob> U
"""

import sys, math, argparse
from datetime import datetime, timedelta

# --- User-adjustable defaults ---
DIA  = 5      # hours
PEAK = 75     # minutes

# ---------- Core gamma-based IOB ----------
def _gamma_cdf_integer_k(k: int, x: float) -> float:
    """Regularized lower incomplete gamma CDF for integer k >= 1."""
    if x <= 0:
        return 0.0
    s = 1.0
    term = 1.0
    for m in range(1, k):
        term *= x / m
        s += term
    return 1.0 - math.exp(-x) * s

def iob_exponential_oref(
    units: float,
    elapsed_min: float,
    DIA_hours: float = DIA,
    PEAK_min: float = PEAK,
    shape_n: int = 3,
    *,
    round_result: bool = True,
) -> float:
    """Single-dose IOB (units) using oref-style exponential (gamma-variate) curve.

    When ``round_result`` is False the raw floating point result is returned so callers can
    accumulate several contributions and round once at the end to avoid double rounding.
    """
    if units <= 0:
        return 0.0
    if DIA_hours <= 0:
        raise ValueError("DIA_hours must be a positive number of hours")
    peak = float(PEAK_min)
    if peak <= 0.0:
        raise ValueError("PEAK_min must be a positive number of minutes")
    end = max(1.0, DIA_hours * 60.0)
    t = max(0.0, float(elapsed_min))
    if t == 0.0:
        value = float(units)
    elif t >= end:
        value = 0.0
    else:
        n = max(1, int(shape_n))
        k = n + 1
        lam = n / peak

        Ft = _gamma_cdf_integer_k(k, lam * t)
        FD = _gamma_cdf_integer_k(k, lam * end)
        if FD <= 0.0:
            value = 0.0
        else:
            remaining_frac = max(0.0, 1.0 - (Ft / FD))
            value = float(units) * remaining_frac

    return round(value, 2) if round_result else value

def iob_total_from_elapsed(doses, DIA_hours: float = DIA, PEAK_min: float = PEAK,
                           shape_n: int = 3, return_breakdown: bool = False):
    """
    doses: iterable of (units, elapsed_min). Ignores entries with elapsed >= DIA.
    Returns total IOB (rounded 2), and optionally a breakdown list of (units, elapsed_min(0f), iob(2f)).
    """
    if DIA_hours <= 0:
        raise ValueError("DIA_hours must be a positive number of hours")
    end = DIA_hours * 60.0
    total = 0.0
    breakdown = []
    for units, elapsed in doses:
        if units > 0 and 0.0 <= elapsed < end:
            raw_iob = iob_exponential_oref(
                units,
                elapsed,
                DIA_hours,
                PEAK_min,
                shape_n,
                round_result=False,
            )
            total += raw_iob
            if return_breakdown:
                breakdown.append(
                    (float(units), round(float(elapsed), 0), round(raw_iob, 2))
                )
        elif return_breakdown:
            breakdown.append((float(units), round(float(elapsed), 0), 0.0))
    total = round(total, 2)
    return (total, breakdown) if return_breakdown else total

# ---------- Helpers ----------
def _parse_hhmm_to_elapsed_today_or_yesterday(hhmm: str, now: datetime, dia_minutes: float) -> float:
    """Convert 'HH:MM' to elapsed minutes, using today; if in the future, interpret as yesterday.
       If resulting elapsed > DIA, return None to indicate 'ignore'."""
    parts = hhmm.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid HH:MM time '{hhmm}'")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid HH:MM time '{hhmm}'") from None
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid HH:MM time '{hhmm}' (hour must be 0-23)")
    if not (0 <= minute <= 59):
        raise ValueError(f"Invalid HH:MM time '{hhmm}' (minute must be 0-59)")
    today = now.date()
    when_today = datetime(today.year, today.month, today.day, hour, minute, tzinfo=now.tzinfo)
    if when_today <= now:
        elapsed = (now - when_today).total_seconds() / 60.0
    else:
        when_yest = when_today - timedelta(days=1)
        elapsed = (now - when_yest).total_seconds() / 60.0
    return elapsed if 0.0 <= elapsed <= dia_minutes else None

def _token_is_hhmm(tok: str) -> bool:
    return (':' in tok) and all(part.isdigit() for part in tok.split(':', 1))  # loose check

def parse_pairs(tokens, now: datetime, dia_hours: float):
    """
    Parse a flat list like: U elapsed  U "HH:MM"  U 30  U 23:10 ...
    Returns a list of (units, elapsed_min).
    """
    out = []
    i = 0
    if dia_hours <= 0:
        raise ValueError("dia_hours must be a positive number of hours")
    dia_minutes = dia_hours * 60.0
    n = len(tokens)
    while i < n:
        if i+1 >= n:
            raise ValueError("Odd number of positional arguments; doses must be (units, time) pairs.")
        # units
        try:
            units = float(tokens[i])
        except ValueError:
            raise ValueError(f"Expected units (float) at arg {i+1}, got '{tokens[i]}'")
        # time (minutes or HH:MM)
        tkn = tokens[i+1]
        if _token_is_hhmm(tkn):
            elapsed = _parse_hhmm_to_elapsed_today_or_yesterday(tkn, now, dia_minutes)
            if elapsed is None:
                # outside DIA: silently skip
                pass
            else:
                out.append((units, elapsed))
        else:
            try:
                elapsed = float(tkn)
            except ValueError:
                raise ValueError(f"Expected elapsed minutes or 'HH:MM' at arg {i+2}, got '{tkn}'")
            if 0.0 <= elapsed <= dia_minutes:
                out.append((units, elapsed))
            # else: silently skip (older than DIA)
        i += 2
    return out

# ---------- CLI ----------
def build_arg_parser():
    p = argparse.ArgumentParser(
        description="Compute Insulin On Board (IOB) from one or more (units, time) pairs.\n"
                    "Time can be elapsed minutes or 'HH:MM' (24h).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument('args', nargs='+',
                   help="Pairs: U ELAPSED  or  U HH:MM  (repeatable). "
                        "Example: 1.0 30  2.0 120  0.8 01:10")
    p.add_argument('--dia', '--DIA', type=float, default=DIA, dest='dia',
                   help="Duration of insulin activity (hours).")
    p.add_argument('--peak', '--PEAK', type=float, default=PEAK, dest='peak',
               help="Time to peak activity (minutes).")
    p.add_argument('--shape-n', type=int, default=3,
                   help="Shape parameter n (gamma-variate).")
    p.add_argument('--breakdown', action='store_true',
                   help="Show per-dose breakdown.")
    p.add_argument('--no-round', action='store_true',
                   help="Disable rounding (mainly for debugging).")
    return p

def main(argv=None):
    ap = build_arg_parser()
    if argv is None and len(sys.argv) == 1:
        ap.print_help(sys.stderr)
        print("\nError: you must provide one or more (units, time) pairs.", file=sys.stderr)
        return 2
    ns = ap.parse_args(argv)

    if ns.dia <= 0:
        print("Error: --dia must be a positive number of hours.", file=sys.stderr)
        return 2
    # use local 'now' (naive) for HH:MM; consistency is fine for CLI
    now = datetime.now()
    try:
        doses = parse_pairs(ns.args, now, ns.dia)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if ns.peak <= 0:
        print("Error: --peak must be a positive number of minutes.", file=sys.stderr)
        return 2

    if not doses:
        print("Total IOB: 0.00 U (no doses within DIA)", file=sys.stderr)
        return 0

    try:
        total, breakdown = iob_total_from_elapsed(
            doses, DIA_hours=ns.dia, PEAK_min=ns.peak, shape_n=ns.shape_n, return_breakdown=True
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if ns.no_round:
        # recompute without rounding for visibility
        # (uses the inner single-dose function before rounding)
        end = ns.dia * 60.0
        total_raw = 0.0
        raw_rows = []
        for units, elapsed in doses:
            if units > 0 and 0 <= elapsed < end:
                val = iob_exponential_oref(
                    units,
                    elapsed,
                    DIA_hours=ns.dia,
                    PEAK_min=ns.peak,
                    shape_n=ns.shape_n,
                    round_result=False,
                )
                total_raw += val
                raw_rows.append((units, elapsed, val))
        print(f"Total IOB (raw): {total_raw}")
        if ns.breakdown:
            for u,e,v in raw_rows:
                print(f"{u} U, {e:.0f} min -> {v} U")
        return 0

    # default: rounded
    print(f"Total IOB: {total:.2f} U")
    if ns.breakdown:
        for u, e, i in breakdown:
            print(f"{u:g} U, {e:.0f} min -> {i:.2f} U")
    return 0

if __name__ == '__main__':
    sys.exit(main())
