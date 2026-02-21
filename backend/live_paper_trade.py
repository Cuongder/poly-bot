import time
import pandas as pd
import requests
from core.polymarket_client import PolymarketClient
from core.signal_generator import SignalGenerator
from core.risk_manager import RiskManager
from core.fee_optimizer import FeeOptimizer

class PaperTrader:
    def __init__(self):
        self.poly_client = PolymarketClient()
        self.sg = SignalGenerator()
        self.rm = RiskManager()
        self.fo = FeeOptimizer()
        
        self.balance = 100.0
        self.wins = 0
        self.losses = 0
        self.trades = []
        
        # Example PolyMarket Condition ID for a BTC market
        # Real ID would be fetched via Polymarket API
        self.market_token_id = "0x_dummy_btc_up_token_id"

    def fetch_live_btc_data(self) -> pd.DataFrame:
        """Fetch pseudo-live BTC OHLCV from Binance API for indicator generation"""
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=100"
        try:
            res = requests.get(url).json()
            df = pd.DataFrame(res, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        except Exception as e:
            print(f"Failed to fetch Binance data: {e}")
            return pd.DataFrame()

    def run_cycle(self):
        print(f"\n--- Paper Trading Cycle Start ---")
        print(f"Current Balance: ${self.balance:.2f} | Wins: {self.losses} | Losses: {self.losses}")
        
        # 1. Fetch Underlying Asset Data (BTC)
        df = self.fetch_live_btc_data()
        if df.empty:
            print("No data fetched, skipping cycle.")
            return
            
        latest_price = df['close'].iloc[-1]
        print(f"Live BTC Price: ${latest_price:,.2f}")
        
        # 2. Generate Signals
        signal = self.sg.generate_signal(df)
        print(f"Generated Signal: {signal['direction']} (Strength: {signal['strength']:.2f})")
        
        if signal['direction'] != 'NEUTRAL':
            # 3. Risk Management
            win_rate = (self.wins / (self.wins + self.losses)) if (self.wins + self.losses) > 0 else 0.5
            size = self.rm.calculate_position_size(self.balance, win_rate, 5.0, 2.5, signal['strength'])
            
            # Poly price (probability 0-1)
            poly_price = self.poly_client.get_market_price(self.market_token_id)
            print(f"Polymarket Ask Price: {poly_price}")
            
            if size > 0:
                print(f"Placing PAPER order -> Dir: {signal['direction']} | Size: ${size:.2f} | Price: {poly_price}")
                
                # Mock outcome for paper trading execution
                import random
                is_win = random.random() > 0.5 
                
                # If we bought shares at `poly_price`, payout on win is 1.0 per share
                shares = size / poly_price
                if is_win:
                    pnl = shares * 1.0 - size  # Profit
                    self.wins += 1
                    status = "WIN"
                else:
                    pnl = -size  # Loss
                    self.losses += 1
                    status = "LOSS"
                    
                fee = size * 0.02 # mock 2% fee / slippage
                net_pnl = pnl - fee
                
                self.balance += net_pnl
                self.poly_client.paper_balance = self.balance # Sync to client
                
                print(f"Trade Result: {status} | Net PnL: ${net_pnl:.2f} | New Bal: ${self.balance:.2f}")
                self.trades.append({"dir": signal['direction'], "net_pnl": net_pnl, "balance": self.balance})
        else:
            print("No trade entry met.")
            
        print("--- Cycle End ---\n")

if __name__ == "__main__":
    print("Initiating Poly-Bot Paper Trading Engine...\n")
    trader = PaperTrader()
    
    try:
        for _ in range(5):
            trader.run_cycle()
            time.sleep(5) # wait 5s between cycles for demo
    except KeyboardInterrupt:
        print("Paper Trading Stopped.")
    
    print("\nFinal Paper Trading Results:")
    print(f"Balance: ${trader.balance:.2f} | Total Trades: {len(trader.trades)}")
