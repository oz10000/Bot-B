import pandas as pd
import os
from quant_bot.config import TRADES_FILE, METRICS_FILE, EQUITY_FILE

def save_logs(portfolio):

    if len(portfolio.trade_log)==0:
        return

    df = pd.DataFrame(portfolio.trade_log)

    df.to_csv(
        TRADES_FILE,
        mode="a",
        header=not os.path.exists(TRADES_FILE),
        index=False
    )

    portfolio.trade_log=[]

    full = pd.read_csv(TRADES_FILE)

    report = {
        "trades":len(full),
        "winrate":(full.pnl>0).mean(),
        "avg_mae":full.mae.mean(),
        "avg_mfe":full.mfe.mean(),
        "pnl_total":full.pnl.sum()
    }

    with open(METRICS_FILE,"w") as f:

        for k,v in report.items():
            f.write(f"{k}:{v}\n")

    eq = pd.DataFrame([{"capital":portfolio.capital}])

    eq.to_csv(
        EQUITY_FILE,
        mode="a",
        header=not os.path.exists(EQUITY_FILE),
        index=False
    )
