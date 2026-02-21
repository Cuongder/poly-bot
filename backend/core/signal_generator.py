import pandas as pd
import numpy as np

class SignalGenerator:
    def __init__(self):
        """
        Generates trading signals based on momentum_v3, vol_filter, and rsi_14.
        """
        pass

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds EMA, SMA, and RSI to the dataframe using pure pandas"""
        if len(df) < 50:
            return df
            
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['SMA_20_VOL'] = df['volume'].rolling(window=20).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid division by zero
        rs = gain / loss
        # Where loss == 0, RSI is 100
        rs = rs.replace(np.inf, np.nan)
        rsi = 100 - (100 / (1 + rs))
        # Fill strictly where loss was exactly 0
        rsi = rsi.fillna(100)
        
        df['RSI_14'] = rsi
        
        return df

    def generate_signal(self, df: pd.DataFrame) -> dict:
        """
        Evaluates the latest row for trading signals.
        Requirements:
        1. Trend Filter: EMA(20) > EMA(50) for UP (vice versa for DOWN)
        2. Volume Confirmation: Volume > SMA(20)_VOL * 1.2
        3. RSI Filter: Exclude RSI in 30-70 range
        """
        df = self.compute_indicators(df)
        if df.empty or len(df) < 50:
            print(f"DEBUG: df is empty ({df.empty}) or too small ({len(df)})")
            return {"direction": "NEUTRAL", "strength": 0.0}
            
        latest = df.iloc[-1]
        
        # Check volume confirmation
        if latest['volume'] <= latest['SMA_20_VOL'] * 1.2:
            return {"direction": "NEUTRAL", "strength": 0.0}
            
        # Check RSI filter
        rsi = latest['RSI_14']
        if pd.isna(rsi) or (30 <= rsi <= 70):
            return {"direction": "NEUTRAL", "strength": 0.0}
            
        # Check trend
        ema_20 = latest['EMA_20']
        ema_50 = latest['EMA_50']
        
        if pd.isna(ema_20) or pd.isna(ema_50):
            print(f"DEBUG: EMA20 ({ema_20}) or EMA50 ({ema_50}) is NA")
            return {"direction": "NEUTRAL", "strength": 0.0}
            
        if ema_20 > ema_50 and rsi > 70:
            return {"direction": "UP", "strength": (rsi - 70) / 30.0}  # Normalize strength
            
        if ema_20 < ema_50 and rsi < 30:
            return {"direction": "DOWN", "strength": (30 - rsi) / 30.0}  # Normalize strength
            
        return {"direction": "NEUTRAL", "strength": 0.0}
