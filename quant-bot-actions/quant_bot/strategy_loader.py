import re
import os
import pandas as pd

DEFAULT_STRATEGIES = [
    "BTC/USDT 1m 3 0.006 0.016 100",
    "ETH/USDT 1m 3 0.006 0.016 90",
    "SOL/USDT 1m 3 0.006 0.016 80",
    "XRP/USDT 1m 3 0.006 0.016 75",
    "DOGE/USDT 1m 3 0.006 0.016 120"
]


def ensure_report_exists(report_file):
    """
    Creates the strategy report automatically if missing.
    """
    if not os.path.exists(report_file):

        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, "w") as f:
            for line in DEFAULT_STRATEGIES:
                f.write(line + "\n")


def load_strategies(report_file):

    ensure_report_exists(report_file)

    pattern = r'^([A-Z0-9/.-]+)\s+([1-3]m)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)'

    rows = []

    with open(report_file) as f:

        for line in f:

            m = re.match(pattern, line.strip())

            if m:

                symbol, tf, accum, tp, sl, trades = m.groups()

                rows.append({
                    "symbol": symbol,
                    "timeframe": tf,
                    "accum": int(accum),
                    "tp": float(tp),
                    "sl": float(sl),
                    "trades": int(trades)
                })

    if len(rows) == 0:
        return []

    df = pd.DataFrame(rows)

    df = df[df.trades > 30]

    return df.head(20).to_dict("records")
