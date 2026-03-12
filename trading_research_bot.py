import ccxt
import pandas as pd
import numpy as np
import time
import re
import json
import os
from datetime import datetime

############################
# CONFIG
############################

INITIAL_CAPITAL = 1000
EMA_PERIOD = 20
DEV_THRESHOLD = 0.003
LOOKBACK = 500

REPORT_FILE = "quant_research_report.txt"

STATE_FILE = "portfolio_state.json"
TRADES_FILE = "trades_log.csv"
METRICS_FILE = "metrics_report.txt"

UNIVERSE = "TOP3"

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
# SCANNER
############################

class Scanner:

    def __init__(self):

        self.exchange = ccxt.kucoin({'enableRateLimit': True})

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

        return self.capital / max(len(self.strategies),1)

    def open(self, symbol, side, price, tp, sl):

        if symbol in self.positions:
            return

        size = self.size()

        self.positions[symbol] = {
            "side": side,
            "entry": price,
            "size": size,
            "tp": price*(1+tp) if side==1 else price*(1-tp),
            "sl": price*(1-sl) if side==1 else price*(1+sl),
            "open": datetime.utcnow().isoformat(),
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
                "close":datetime.utcnow().isoformat()
            }

            self.trade_log.append(trade)

            del self.positions[symbol]

############################
# STATE PERSISTENCE
############################

def save_state(portfolio):

    state = {
        "capital": portfolio.capital,
        "positions": portfolio.positions
    }

    with open(STATE_FILE,"w") as f:
        json.dump(state,f)

def load_state(portfolio):

    if not os.path.exists(STATE_FILE):
        return

    with open(STATE_FILE) as f:

        state = json.load(f)

        portfolio.capital = state["capital"]
        portfolio.positions = state["positions"]

############################
# LOGGING
############################

def save_logs(portfolio):

    if len(portfolio.trade_log) == 0:
        return

    df = pd.DataFrame(portfolio.trade_log)

    df.to_csv(
        TRADES_FILE,
        mode="a",
        header=not os.path.exists(TRADES_FILE),
        index=False
    )

    portfolio.trade_log = []

    full = pd.read_csv(TRADES_FILE)

    report = {}

    report["trades"] = len(full)
    report["winrate"] = (full.pnl>0).mean()
    report["avg_mae"] = full.mae.mean()
    report["avg_mfe"] = full.mfe.mean()
    report["pnl_total"] = full.pnl.sum()

    with open(METRICS_FILE,"w") as f:

        for k,v in report.items():
            f.write(f"{k}: {v}\n")

############################
# MAIN LOOP
############################

def main():

    strategies = load_strategies(REPORT_FILE)

    scanner = Scanner()

    portfolio = Portfolio(strategies)

    load_state(portfolio)

    print("starting bot")

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

        print("capital",portfolio.capital)

        save_logs(portfolio)

        save_state(portfolio)

        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
