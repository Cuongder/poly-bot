import math

class RiskManager:
    def __init__(self, config=None):
        self.max_position_pct = 0.05
        self.max_leverage = 3
        self.max_drawdown_pct = -0.10
        self.daily_loss_limit_pct = -0.05
        self.kelly_fraction = 0.5
        self.min_edge = 0.015
        self.atr_multiplier = 1.5
        
        if config:
            self._apply_config(config)

    def _apply_config(self, config: dict):
        self.max_position_pct = config.get("max_position_pct", self.max_position_pct)
        self.max_leverage = config.get("max_leverage", self.max_leverage)
        self.max_drawdown_pct = config.get("max_drawdown_pct", self.max_drawdown_pct)
        self.daily_loss_limit_pct = config.get("daily_loss_limit", self.daily_loss_limit_pct)
        
        kelly = config.get("kelly_criterion", {})
        self.kelly_fraction = kelly.get("fraction", self.kelly_fraction)
        self.min_edge = kelly.get("min_edge", self.min_edge)
        
        sl = config.get("stop_loss", {})
        self.atr_multiplier = sl.get("atr_multiplier", self.atr_multiplier)

    def calculate_position_size(self, account_balance: float, win_rate: float, avg_win: float, avg_loss: float, confidence_score: float = 1.0) -> float:
        """Calculate position size using Half Kelly Criterion, capped at max_position_pct (5%).
        Only executes if edge > min_edge"""
        
        # Avoid division by zero
        if avg_loss <= 0 or win_rate <= 0:
            return 0.0
            
        reward_risk_ratio = avg_win / avg_loss
        expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        edge = expected_value / avg_loss  # Edge as a percentage of risk
        
        if edge < self.min_edge:
            return 0.0
            
        kelly_pct = win_rate - ((1 - win_rate) / reward_risk_ratio)
        
        if kelly_pct <= 0:
            return 0.0
            
        # Apply fraction and confidence score
        allocated_pct = kelly_pct * self.kelly_fraction * confidence_score
        
        # Cap at max_position_pct
        final_pct = min(allocated_pct, self.max_position_pct)
        
        return account_balance * final_pct

    def calculate_stop_loss(self, entry_price: float, direction: str, atr_1h: float) -> float:
        """Calculates stop loss based on 1.5x ATR trailing return distance."""
        stop_distance = atr_1h * self.atr_multiplier
        
        if direction.upper() == 'UP':
            return entry_price - stop_distance
        elif direction.upper() == 'DOWN':
            return entry_price + stop_distance
        else:
            raise ValueError("Direction must be UP or DOWN")

    def check_circuit_breakers(self, daily_pnl_pct: float, total_drawdown_pct: float, consecutive_losses: int) -> dict:
        """Checks circuit breakers and returns an action dictionary."""
        response = {
            "should_stop_trading": False,
            "reduce_size": False,
            "pause_bot": False,
            "reason": ""
        }
        
        if total_drawdown_pct <= self.max_drawdown_pct:
            response["should_stop_trading"] = True
            response["reason"] = f"Max drawdown hit: {total_drawdown_pct * 100}%"
            
        elif daily_pnl_pct <= self.daily_loss_limit_pct:
            response["should_stop_trading"] = True
            response["reason"] = f"Daily loss limit hit: {daily_pnl_pct * 100}%"
            
        elif consecutive_losses >= 5:
            response["reduce_size"] = True
            response["reason"] = f"Consecutive losses: {consecutive_losses}. Suggest reducing size by 50%."
            
        return response

    def calculate_leverage(self, atr_1h: float, atr_avg: float) -> int:
        """Dynamic leverage based on volatility. High vol = Low leverage."""
        volatility_ratio = atr_1h / atr_avg if atr_avg > 0 else 1
        
        if volatility_ratio > 2.0:
            return 1  # Volatility spike
        elif volatility_ratio > 1.2:
            return min(2, self.max_leverage)
        else:
            return self.max_leverage
