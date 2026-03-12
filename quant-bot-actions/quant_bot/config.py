INITIAL_CAPITAL = 100

EMA_PERIOD = 20
DEV_THRESHOLD = 0.003
LOOKBACK = 500

MAX_STRATEGIES = 20

REPORT_FILE = "data/quant_research_report.txt"

DATA_DIR = "runtime"

STATE_FILE = f"{DATA_DIR}/portfolio_state.json"
TRADES_FILE = f"{DATA_DIR}/trades_log.csv"
METRICS_FILE = f"{DATA_DIR}/metrics_report.txt"
EQUITY_FILE = f"{DATA_DIR}/equity_curve.csv"

SUMMARY_TXT = f"{DATA_DIR}/summary_report.txt"
TRADES_TXT = f"{DATA_DIR}/trades_report.txt"
STATS_TXT = f"{DATA_DIR}/statistics_report.txt"

EXCHANGE = "kucoin"

FETCH_DELAY = 0.4
LOOP_INTERVAL = 60

CYCLES = 3
