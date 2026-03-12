import re
import pandas as pd

def load_strategies(report_file):

    pattern = r'^([A-Z0-9/.-]+)\s+([1-3]m)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)'

    rows = []

    with open(report_file) as f:

        for line in f:

            m = re.match(pattern,line.strip())

            if m:

                symbol, tf, accum, tp, sl, trades = m.groups()

                rows.append({
                    "symbol":symbol,
                    "timeframe":tf,
                    "accum":int(accum),
                    "tp":float(tp),
                    "sl":float(sl),
                    "trades":int(trades)
                })

    df = pd.DataFrame(rows)

    df = df[df.trades > 30]

    return df.head(20).to_dict("records")
