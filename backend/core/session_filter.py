import datetime
import pytz

class SessionFilter:
    def __init__(self):
        """
        Filters trading sessions based on funding rate, daily close, volatility, and weekend logic.
        """
        pass

    def should_skip_trading(self, funding_rate: float, atr_current: float, atr_avg: float, current_time_utc: datetime.datetime = None) -> dict:
        """
        SKIP_TRADING_WHEN:
          - funding_rate > 0.0001        # 0.01%
          - time_of_day == 00:00 ± 15min # Daily close
          - volatility_spike == True     # ATR > 2x avg
          - weekend_low_volume == True   # Saturday low liquidity
        Returns dict with "skip" boolean and "reason" string.
        """
        if current_time_utc is None:
            current_time_utc = datetime.datetime.now(pytz.utc)
            
        # 1. Funding rate check
        if funding_rate > 0.0001:
            return {"skip": True, "reason": f"Funding rate too high: {funding_rate}"}
            
        # 2. Daily close check (00:00 ± 15min UTC)
        hour = current_time_utc.hour
        minute = current_time_utc.minute
        
        # 23:45 - 23:59 or 00:00 - 00:15
        if (hour == 23 and minute >= 45) or (hour == 0 and minute <= 15):
            return {"skip": True, "reason": "Avoid trading around daily close (00:00 UTC)"}
            
        # 3. Volatility spike
        if atr_avg > 0 and atr_current > (atr_avg * 2):
            return {"skip": True, "reason": "Volatility spike detected (ATR > 2x avg)"}
            
        # 4. Weekend low volume (Saturday)
        if current_time_utc.weekday() == 5: # Saturday = 5 in Python (0=Monday)
            return {"skip": True, "reason": "Weekend low liquidity (Saturday)"}
            
        return {"skip": False, "reason": ""}
