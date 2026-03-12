import ccxt
import pandas as pd
import numpy as np
import time
from quant_bot.config import LOOKBACK, EXCHANGE, FETCH_DELAY

class MarketData:

    def __init__(self,strategies):

        self.exchange = getattr(ccxt,EXCHANGE)({"enableRateLimit":True})

        self.symbols = list(set([s["symbol"] for s in strategies]))

        self.cache = {}

    def fetch_all(self):

        self.cache = {}

        for sym in self.symbols:

            try:

                data = self.exchange.fetch_ohlcv(sym,"1m",limit=LOOKBACK)

                df = pd.DataFrame(data,columns=["ts","o","h","l","c","v"])

                df["ts"] = pd.to_datetime(df["ts"],unit="ms")

                self.cache[sym] = df

            except Exception as e:

                print("fetch error",sym,e)

            time.sleep(FETCH_DELAY)

    def aggregate(self,df,tf):

        if tf == "1m":
            return df

        n = int(tf.replace("m",""))

        df = df.copy()

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
