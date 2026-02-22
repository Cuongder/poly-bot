import time
import logging
import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import pandas as pd
import requests
from core.polymarket_client import PolymarketClient
from core.signal_generator import SignalGenerator
from core.risk_manager import RiskManager
from core.fee_optimizer import FeeOptimizer
from core.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position"""
    id: int
    market: str
    direction: str  # 'YES' or 'NO'
    size: float
    entry_price: float
    entry_time: datetime.datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class TradeResult:
    """Result of a closed trade"""
    trade_id: int
    direction: str
    entry_price: float
    exit_price: float
    size: float
    gross_pnl: float
    fee_paid: float
    net_pnl: float
    open_time: datetime.datetime
    close_time: datetime.datetime
    close_reason: str  # 'SIGNAL', 'STOP_LOSS', 'TAKE_PROFIT'


class PaperTrader:
    """
    Paper trading engine with proper position management.
    - Opens positions based on signals
    - Tracks open positions with entry prices
    - Closes positions on reverse signals or stop loss/take profit
    - Calculates PnL based on actual price movements
    """

    def __init__(self, initial_balance: float = 100.0, db: Optional[Database] = None):
        self.poly_client = PolymarketClient()
        self.sg = SignalGenerator()
        self.rm = RiskManager()
        self.fo = FeeOptimizer()
        self.db = db or Database()

        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.wins = 0
        self.losses = 0
        self.total_fees = 0.0

        # Position tracking
        self.open_position: Optional[Position] = None
        self.trade_history: List[TradeResult] = []

        # Configuration
        self.market_token_id = "0x_dummy_btc_up_token_id"
        self.stop_loss_pct = 0.10  # 10% stop loss
        self.take_profit_pct = 0.20  # 20% take profit
        self.fee_rate = 0.02  # 2% fee/slippage

        logger.info(f"PaperTrader initialized with balance: ${initial_balance:.2f}")

    def fetch_live_btc_data(self) -> pd.DataFrame:
        """Fetch pseudo-live BTC OHLCV from Binance API for indicator generation"""
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=100"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)

            logger.debug(f"Fetched {len(df)} candles from Binance")
            return df
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Binance data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {e}")
            return pd.DataFrame()

    def calculate_pnl(self, position: Position, exit_price: float) -> float:
        """
        Calculate PnL for a position based on price movement.
        For binary options: payout is $1 per share if correct, $0 if wrong.
        """
        shares = position.size / position.entry_price

        if position.direction == 'YES':
            # Bought YES shares at entry_price, sell at exit_price
            # PnL = (exit - entry) * shares
            pnl = (exit_price - position.entry_price) * shares
        else:  # 'NO'
            # Bought NO shares at entry_price, sell at exit_price
            # For NO shares, price moves inversely to probability
            pnl = (exit_price - position.entry_price) * shares

        return pnl

    def open_position(self, direction: str, size: float, entry_price: float) -> Position:
        """Open a new position and save to database"""
        # Validate inputs
        if direction not in ['YES', 'NO']:
            raise ValueError(f"Invalid direction: {direction}. Must be 'YES' or 'NO'")
        if size <= 0:
            raise ValueError(f"Invalid size: {size}. Must be positive")
        if entry_price <= 0 or entry_price > 1:
            raise ValueError(f"Invalid entry_price: {entry_price}. Must be between 0 and 1")

        # Check if we already have an open position
        if self.open_position is not None:
            logger.warning("Already have an open position. Close it first.")
            return self.open_position

        # Check balance
        if size > self.balance:
            logger.warning(f"Insufficient balance. Required: ${size:.2f}, Available: ${self.balance:.2f}")
            size = self.balance * 0.95  # Use 95% of balance

        # Calculate stop loss and take profit levels
        if direction == 'YES':
            stop_loss = max(0.01, entry_price * (1 - self.stop_loss_pct))
            take_profit = min(0.99, entry_price * (1 + self.take_profit_pct))
        else:  # NO
            stop_loss = min(0.99, entry_price * (1 + self.stop_loss_pct))
            take_profit = max(0.01, entry_price * (1 - self.take_profit_pct))

        # Log to database first to get trade ID
        trade_data = {
            'market': self.market_token_id,
            'direction': direction,
            'size': size,
            'entry_price': entry_price
        }
        trade_id = self.db.log_trade(trade_data)

        position = Position(
            id=trade_id,
            market=self.market_token_id,
            direction=direction,
            size=size,
            entry_price=entry_price,
            entry_time=datetime.datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.open_position = position
        self.balance -= size  # Deduct position size from balance

        logger.info(f"Opened {direction} position | Size: ${size:.2f} | Entry: {entry_price:.4f} | "
                   f"SL: {stop_loss:.4f} | TP: {take_profit:.4f}")

        return position

    def close_position(self, exit_price: float, reason: str = 'SIGNAL') -> Optional[TradeResult]:
        """Close the current position and calculate PnL"""
        if self.open_position is None:
            logger.warning("No open position to close")
            return None

        position = self.open_position

        # Calculate PnL
        gross_pnl = self.calculate_pnl(position, exit_price)

        # Calculate fees
        entry_fee = position.size * self.fee_rate
        exit_value = position.size + gross_pnl
        exit_fee = max(0, exit_value) * self.fee_rate
        total_fee = entry_fee + exit_fee

        net_pnl = gross_pnl - total_fee

        # Update balance
        self.balance += position.size + gross_pnl - exit_fee

        # Update win/loss counters
        if net_pnl > 0:
            self.wins += 1
        else:
            self.losses += 1

        self.total_fees += total_fee

        # Create trade result
        result = TradeResult(
            trade_id=position.id,
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            gross_pnl=gross_pnl,
            fee_paid=total_fee,
            net_pnl=net_pnl,
            open_time=position.entry_time,
            close_time=datetime.datetime.now(),
            close_reason=reason
        )

        self.trade_history.append(result)

        # Update database
        close_data = {
            'exit_price': exit_price,
            'fee_paid': total_fee,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl
        }
        self.db.close_trade(position.id, close_data)

        logger.info(f"Closed position | Reason: {reason} | Entry: {position.entry_price:.4f} | "
                   f"Exit: {exit_price:.4f} | Gross PnL: ${gross_pnl:.2f} | "
                   f"Fees: ${total_fee:.2f} | Net PnL: ${net_pnl:.2f} | "
                   f"Balance: ${self.balance:.2f}")

        self.open_position = None
        return result

    def check_exit_conditions(self, current_price: float) -> Optional[str]:
        """Check if position should be closed based on stop loss or take profit"""
        if self.open_position is None:
            return None

        position = self.open_position

        if position.direction == 'YES':
            if current_price <= position.stop_loss:
                return 'STOP_LOSS'
            if current_price >= position.take_profit:
                return 'TAKE_PROFIT'
        else:  # NO
            if current_price >= position.stop_loss:
                return 'STOP_LOSS'
            if current_price <= position.take_profit:
                return 'TAKE_PROFIT'

        return None

    def signal_to_direction(self, signal: Dict) -> Optional[str]:
        """Convert signal to position direction"""
        if signal['direction'] == 'BUY':
            return 'YES'
        elif signal['direction'] == 'SELL':
            return 'NO'
        return None

    def run_cycle(self):
        """Execute one trading cycle"""
        logger.info("--- Paper Trading Cycle Start ---")
        logger.info(f"Balance: ${self.balance:.2f} | Wins: {self.wins} | Losses: {self.losses} | "
                   f"Open Position: {self.open_position is not None}")

        try:
            # 1. Fetch market data
            df = self.fetch_live_btc_data()
            if df.empty:
                logger.warning("No data fetched, skipping cycle")
                return

            latest_price = df['close'].iloc[-1]
            logger.info(f"Live BTC Price: ${latest_price:,.2f}")

            # 2. Get Polymarket price
            poly_price = self.poly_client.get_market_price(self.market_token_id)
            logger.info(f"Polymarket Price: {poly_price:.4f}")

            # 3. Check exit conditions if we have an open position
            if self.open_position is not None:
                exit_reason = self.check_exit_conditions(poly_price)
                if exit_reason:
                    self.close_position(poly_price, exit_reason)
                    return

            # 4. Generate trading signal
            signal = self.sg.generate_signal(df)
            logger.info(f"Signal: {signal['direction']} (Strength: {signal['strength']:.2f})")

            signal_direction = self.signal_to_direction(signal)

            # 5. Handle position based on signal
            if signal_direction is None:
                logger.info("No trade signal - NEUTRAL")
            elif self.open_position is None:
                # No position - open if signal is strong enough
                if signal['strength'] >= 0.5:
                    win_rate = (self.wins / (self.wins + self.losses)) if (self.wins + self.losses) > 0 else 0.5
                    size = self.rm.calculate_position_size(
                        self.balance, win_rate, 5.0, 2.5, signal['strength']
                    )

                    if size > 0 and size <= self.balance:
                        self.open_position(signal_direction, size, poly_price)
                    else:
                        logger.warning(f"Calculated position size {size:.2f} is invalid or exceeds balance")
                else:
                    logger.info(f"Signal strength {signal['strength']:.2f} below threshold, not entering")
            else:
                # Have position - check for reversal
                if signal_direction != self.open_position.direction:
                    logger.info(f"Signal reversal detected: {self.open_position.direction} -> {signal_direction}")
                    self.close_position(poly_price, 'SIGNAL')

                    # Open new position if signal is strong
                    if signal['strength'] >= 0.5:
                        win_rate = (self.wins / (self.wins + self.losses)) if (self.wins + self.losses) > 0 else 0.5
                        size = self.rm.calculate_position_size(
                            self.balance, win_rate, 5.0, 2.5, signal['strength']
                        )
                        if size > 0 and size <= self.balance:
                            self.open_position(signal_direction, size, poly_price)
                else:
                    logger.info(f"Signal aligns with current position ({self.open_position.direction}), holding")

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)

        logger.info("--- Paper Trading Cycle End ---\n")

    def get_stats(self) -> Dict:
        """Get current trading statistics"""
        total_trades = self.wins + self.losses
        win_rate = (self.wins / total_trades * 100) if total_trades > 0 else 0

        total_net_pnl = sum(t.net_pnl for t in self.trade_history)
        total_gross_pnl = sum(t.gross_pnl for t in self.trade_history if t.gross_pnl > 0)

        return {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'total_pnl': self.balance - self.initial_balance,
            'wins': self.wins,
            'losses': self.losses,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_fees': self.total_fees,
            'gross_pnl': total_gross_pnl,
            'net_pnl': total_net_pnl,
            'has_open_position': self.open_position is not None
        }

    def get_open_position_info(self) -> Optional[Dict]:
        """Get information about current open position"""
        if self.open_position is None:
            return None

        position = self.open_position
        return {
            'id': position.id,
            'market': position.market,
            'direction': position.direction,
            'size': position.size,
            'entry_price': position.entry_price,
            'entry_time': position.entry_time.isoformat(),
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit
        }


if __name__ == "__main__":
    logger.info("Initiating Poly-Bot Paper Trading Engine...")
    trader = PaperTrader()

    try:
        for _ in range(5):
            trader.run_cycle()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Paper Trading Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

    # Final summary
    stats = trader.get_stats()
    logger.info("\n=== Final Paper Trading Results ===")
    logger.info(f"Final Balance: ${stats['balance']:.2f}")
    logger.info(f"Total PnL: ${stats['total_pnl']:.2f}")
    logger.info(f"Total Trades: {stats['total_trades']}")
    logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
    logger.info(f"Total Fees: ${stats['total_fees']:.2f}")
