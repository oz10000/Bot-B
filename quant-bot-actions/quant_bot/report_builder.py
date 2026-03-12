import pandas as pd
from quant_bot.config import TRADES_FILE, METRICS_FILE, SUMMARY_TXT, TRADES_TXT, STATS_TXT

def build_reports():

    trades = pd.read_csv(TRADES_FILE)

    with open(TRADES_TXT,"w") as f:

        f.write("TRADE REPORT\n\n")

        for _,t in trades.iterrows():

            f.write(
                f"{t['symbol']} | entry {t['entry']} | exit {t['exit']} | pnl {t['pnl']}\n"
            )

    with open(METRICS_FILE) as m:

        metrics = m.read()

    with open(STATS_TXT,"w") as f:

        f.write("STATISTICS\n\n")
        f.write(metrics)

    with open(SUMMARY_TXT,"w") as f:

        f.write("QUANT BOT SUMMARY\n\n")

        f.write(f"Total trades: {len(trades)}\n")
        f.write(f"Total pnl: {trades.pnl.sum()}\n")
