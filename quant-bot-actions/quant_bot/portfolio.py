from datetime import datetime

class Portfolio:

    def __init__(self, capital, strategies):
        self.capital = capital
        self.strategies = strategies
        self.positions = {}
        self.trade_log = []

    def position_size(self):
        """
        Capital allocation per strategy
        """
        if len(self.strategies) == 0:
            return 0
        return self.capital / len(self.strategies)

    def open(self, symbol, side, price, tp, sl):

        if symbol in self.positions:
            return

        size = self.position_size()

        position = {
            "side": side,
            "entry": price,
            "size": size,
            "tp": price * (1 + tp) if side == 1 else price * (1 - tp),
            "sl": price * (1 - sl) if side == 1 else price * (1 + sl),
            "mae": 0,
            "mfe": 0,
            "open": datetime.utcnow().isoformat()
        }

        self.positions[symbol] = position

    def update(self, symbol, price):

        if symbol not in self.positions:
            return

        p = self.positions[symbol]

        entry = p["entry"]

        move = (price - entry) / entry

        if p["side"] == -1:
            move *= -1

        p["mfe"] = max(p["mfe"], move)
        p["mae"] = min(p["mae"], move)

        tp_hit = price >= p["tp"] if p["side"] == 1 else price <= p["tp"]
        sl_hit = price <= p["sl"] if p["side"] == 1 else price >= p["sl"]

        if tp_hit or sl_hit:

            pnl = move * p["size"]

            self.capital += pnl

            trade = {
                "symbol": symbol,
                "entry": entry,
                "exit": price,
                "pnl": pnl,
                "mae": p["mae"],
                "mfe": p["mfe"],
                "open": p["open"],
                "close": datetime.utcnow().isoformat()
            }

            self.trade_log.append(trade)

            del self.positions[symbol]
