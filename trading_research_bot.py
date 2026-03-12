import ccxt
import pandas as pd
import numpy as np
import time
import re
from datetime import datetime

############################
# CONFIG
############################

INITIAL_CAPITAL = 1000
EMA_PERIOD = 20
DEV_THRESHOLD = 0.003
LOOKBACK = 500
REPORT_FILE = "quant_research_report.txt"

UNIVERSE = "TOP3"  
# options:
# TOP3
# TOP10
# TOP20
# TOP30
# TOP40
# TOP50

LOOP_INTERVAL = 60


############################
# LOAD STRATEGIES
############################

def load_strategies(report_file):

    rows = []

    pattern = r'^([A-Z0-9/.-]+)\s+([1-3]m)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)'

    with open(report_file) as f:
        for line in f:
            m = re.match(pattern, line.strip())
            if m:
                symbol, tf, accum, tp, sl, trades, winrate, pf, expectancy, sharpe, dd, cap, edge = m.groups()

                rows.append({
                    "symbol": symbol,
                    "timeframe": tf,
                    "accum": int(accum),
                    "tp": float(tp),
                    "sl": float(sl),
                    "trades": int(trades),
                    "pf": float(pf),
                    "edge": float(edge)
                })

    df = pd.DataFrame(rows)

    df = df[(df.trades > 30) & (df.pf > 1.1)]

    df = df.sort_values("edge", ascending=False)

    return df.head(20).to_dict("records")


############################
# MARKET UNIVERSE
############################

def market_universe():

    top = {
        "TOP3": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        "TOP10": [],
        "TOP20": [],
        "TOP30": [],
        "TOP40": [],
        "TOP50": []
    }

    return top[UNIVERSE]


############################
# SCANNER
############################

class Scanner:

    def __init__(self):

        self.exchange = ccxt.kucoin({'enableRateLimit': True})
        self.cache = {}

    def fetch(self, symbol):

        data = self.exchange.fetch_ohlcv(symbol, "1m", limit=LOOKBACK)

        df = pd.DataFrame(data, columns=["ts","o","h","l","c","v"])

        df["ts"] = pd.to_datetime(df["ts"], unit="ms")

        return df

    def aggregate(self, df, tf):

        if tf == "1m":
            return df

        n = int(tf.replace("m",""))

        df["grp"] = np.arange(len(df)) // n

        agg = df.groupby("grp").agg({
            "ts":"first",
            "o":"first",
            "h":"max",
            "l":"min",
            "c":"last",
            "v":"sum"
        }).reset_index(drop=True)

        return agg

    def compute(self, df):

        df["ema"] = df["c"].ewm(span=EMA_PERIOD).mean()

        dev = (df["c"] - df["ema"]) / df["ema"]

        signal = []

        for d in dev:

            if d < -DEV_THRESHOLD:
                signal.append(1)

            elif d > DEV_THRESHOLD:
                signal.append(-1)

            else:
                signal.append(0)

        df["signal"] = signal

        return df


############################
# PORTFOLIO
############################

class Portfolio:

    def __init__(self, strategies):

        self.capital = INITIAL_CAPITAL
        self.positions = {}
        self.strategies = strategies
        self.trade_log = []

    def size(self):

        return self.capital / len(self.strategies)

    def open(self, symbol, side, price, tp, sl):

        if symbol in self.positions:
            return

        size = self.size()

        self.positions[symbol] = {
            "side": side,
            "entry": price,
            "size": size,
            "tp": price * (1 + tp) if side==1 else price * (1 - tp),
            "sl": price * (1 - sl) if side==1 else price * (1 + sl),
            "open": datetime.utcnow(),
            "mae":0,
            "mfe":0
        }

    def update(self, symbol, price):

        if symbol not in self.positions:
            return

        p = self.positions[symbol]

        entry = p["entry"]

        move = (price-entry)/entry

        if p["side"] == -1:
            move *= -1

        p["mfe"] = max(p["mfe"], move)
        p["mae"] = min(p["mae"], move)

        if price >= p["tp"] or price <= p["sl"]:

            pnl = move * p["size"]

            self.capital += pnl

            trade = {
                "symbol":symbol,
                "entry":entry,
                "exit":price,
                "pnl":pnl,
                "mae":p["mae"],
                "mfe":p["mfe"],
                "open":p["open"],
                "close":datetime.utcnow()
            }

            self.trade_log.append(trade)

            del self.positions[symbol]


############################
# LOGGING
############################

def save_logs(portfolio):

    df = pd.DataFrame(portfolio.trade_log)

    df.to_csv("run_log.csv", index=False)

    if len(df) == 0:
        return

    report = {}

    report["trades"] = len(df)
    report["winrate"] = (df.pnl>0).mean()
    report["avg_mae"] = df.mae.mean()
    report["avg_mfe"] = df.mfe.mean()

    hours = df.close.dt.hour.value_counts()

    with open("metrics_report.txt","w") as f:

        for k,v in report.items():
            f.write(f"{k}: {v}\n")

        f.write("\nTrades by hour\n")

        f.write(hours.to_string())


############################
# MAIN LOOP
############################

def main():

    strategies = load_strategies(REPORT_FILE)

    scanner = Scanner()

    portfolio = Portfolio(strategies)

    print("Starting research bot")

    while True:

        for s in strategies:

            symbol = s["symbol"]

            df = scanner.fetch(symbol)

            df = scanner.aggregate(df, s["timeframe"])

            df = scanner.compute(df)

            last = df.iloc[-1]

            portfolio.update(symbol, last.c)

            signals = df.signal.values

            accum = s["accum"]

            if len(signals) >= accum:

                seq = signals[-accum:]

                if all(seq==1):
                    portfolio.open(symbol,1,last.c,s["tp"],s["sl"])

                if all(seq==-1):
                    portfolio.open(symbol,-1,last.c,s["tp"],s["sl"])

        print("capital", portfolio.capital)

        save_logs(portfolio)

        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    main()
