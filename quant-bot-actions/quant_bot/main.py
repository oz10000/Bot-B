import time
import os
import pandas as pd
from datetime import datetime, timedelta

from quant_bot.config import INITIAL_CAPITAL, LOOP_INTERVAL, REPORT_FILE, DATA_DIR, CYCLES, TRADES_FILE, METRICS_FILE
from quant_bot.strategy_loader import load_strategies
from quant_bot.market_data import MarketData
from quant_bot.signal_engine import SignalEngine
from quant_bot.portfolio import Portfolio
from quant_bot.metrics import save_logs
from quant_bot.report_builder import build_reports

def main():
    # 🔹 Crear carpetas necesarias
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # 🔹 Crear trades_log.csv vacío si no existe
    if not os.path.exists(TRADES_FILE):
        pd.DataFrame(columns=["timestamp", "symbol", "side", "entry", "exit", "pnl"]).to_csv(TRADES_FILE, index=False)

    # 🔹 Crear metrics_report.txt vacío si no existe
    if not os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "w") as f:
            f.write("")

    # 🔹 Cargar estrategias y setup inicial
    strategies = load_strategies(REPORT_FILE)
    data = MarketData(strategies)
    engine = SignalEngine()
    portfolio = Portfolio(INITIAL_CAPITAL, strategies)

    # 🔹 Inicializar temporizador de reportes
    last_report_time = datetime.utcnow()

    for _ in range(CYCLES):
        data.fetch_all()

        for s in strategies:
            symbol = s["symbol"]
            df = data.cache.get(symbol)
            if df is None:
                continue

            df = data.aggregate(df, s["timeframe"])
            df = engine.compute(df)
            last_price = df.iloc[-1].c

            portfolio.update(symbol, last_price)
            side = engine.check(df.signal.values, s["accum"])
            if side != 0:
                portfolio.open(symbol, side, last_price, s["tp"], s["sl"])

        # 🔹 Guardar trades log actualizado
        save_logs(portfolio)

        # 🔹 Guardar reportes cada 5 minutos
        now = datetime.utcnow()
        if now - last_report_time >= timedelta(minutes=5):
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            report_file_ts = f"reports/report_{timestamp}.txt"
            build_reports(output_file=report_file_ts)
            last_report_time = now

        # 🔹 Esperar LOOP_INTERVAL
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
