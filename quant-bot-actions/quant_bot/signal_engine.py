from quant_bot.config import EMA_PERIOD, DEV_THRESHOLD

class SignalEngine:

    def compute(self,df):

        df["ema"] = df["c"].ewm(span=EMA_PERIOD).mean()

        dev = (df["c"]-df["ema"])/df["ema"]

        signals = []

        for d in dev:

            if d < -DEV_THRESHOLD:
                signals.append(1)

            elif d > DEV_THRESHOLD:
                signals.append(-1)

            else:
                signals.append(0)

        df["signal"] = signals

        return df

    def check(self,signals,accum):

        if len(signals) < accum:
            return 0

        seq = signals[-accum:]

        if all(s==1 for s in seq):
            return 1

        if all(s==-1 for s in seq):
            return -1

        return 0
