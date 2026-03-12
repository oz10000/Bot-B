import pandas as pd
from quant_bot.config import TRADES_FILE, METRICS_FILE, SUMMARY_TXT, TRADES_TXT, STATS_TXT

def build_reports(output_file=None):
    """
    Construye reportes a partir de trades_log.csv y metrics.txt
    Si output_file se pasa, guarda el reporte completo ahí.
    """
    trades = pd.read_csv(TRADES_FILE)

    # Reporte detallado de trades
    report_txt = "TRADE REPORT\n\n"
    for _, t in trades.iterrows():
        report_txt += f"{t['symbol']} | entry {t['entry']} | exit {t['exit']} | pnl {t['pnl']}\n"

    # Métricas del bot
    with open(METRICS_FILE, "r") as m:
        metrics = m.read()

    stats_txt = "STATISTICS\n\n" + metrics

    summary_txt = "QUANT BOT SUMMARY\n\n"
    summary_txt += f"Total trades: {len(trades)}\n"
    summary_txt += f"Total pnl: {trades.pnl.sum()}\n"

    # Guardar reportes individuales
    trades_report_file = TRADES_TXT if output_file is None else output_file.replace(".txt", "_trades.txt")
    stats_report_file = STATS_TXT if output_file is None else output_file.replace(".txt", "_stats.txt")
    summary_report_file = SUMMARY_TXT if output_file is None else output_file.replace(".txt", "_summary.txt")

    with open(trades_report_file, "w") as f:
        f.write(report_txt)
    with open(stats_report_file, "w") as f:
        f.write(stats_txt)
    with open(summary_report_file, "w") as f:
        f.write(summary_txt)
