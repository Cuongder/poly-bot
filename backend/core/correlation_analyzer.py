class CorrelationAnalyzer:
    def __init__(self):
        """
        Calculates correlation score between 5m and 15m timeframes
        Score 0-1, higher = more confident
        """
        pass

    def calculate_correlation_score(self, tf_5m_signal, tf_15m_signal) -> float:
        """
        Compares signals from 5m and 15m timeframes.
        Returns a confidence score from 0.0 to 1.0.
        """
        if not tf_5m_signal or not tf_15m_signal:
            return 0.0
            
        direction_5m = tf_5m_signal.get("direction")
        direction_15m = tf_15m_signal.get("direction")
        
        strength_5m = tf_5m_signal.get("strength", 0.0)
        strength_15m = tf_15m_signal.get("strength", 0.0)

        if direction_5m == direction_15m:
            strength_diff = abs(strength_5m - strength_15m)
            if strength_diff < 0.2:  # Similar strength
                return 0.9
            else:
                return 0.7
        else:
            return 0.3  # Conflicting, reduce size or skip
