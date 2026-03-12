import time
import os

from quant_bot.config import INITIAL_CAPITAL, LOOP_INTERVAL, REPORT_FILE, DATA_DIR, CYCLES

from quant_bot.strategy_loader import load_strategies
from quant_bot.market_data import MarketData
from quant_bot.signal_engine import SignalEngine
from quant_bot.portfolio import Portfolio
from quant_bot.metrics import save_logs
from quant_bot.report_builder import build_reports

def main():

    os.makedirs(DATA_DIR,exist_ok=True)

    strategies = load_strategies(REPORT_FILE)

    data = MarketData(strategies)

    engine = SignalEngine()

    portfolio = Portfolio(INITIAL_CAPITAL,strategies)

    for _ in range(CYCLES):

        data.fetch_all()

        for s in strategies:

            symbol = s["symbol"]

            df = data.cache.get(symbol)

            if df is None:
                continue

            df = data.aggregate(df,s["timeframe"])

            df = engine.compute(df)

            last_price = df.iloc[-1].c

            portfolio.update(symbol,last_price)

            side = engine.check(df.signal.values,s["accum"])

            if side != 0:

                portfolio.open(symbol,side,last_price,s["tp"],s["sl"])

        save_logs(portfolio)

        time.sleep(LOOP_INTERVAL)

    build_reports()

if __name__ == "__main__":
    main()
