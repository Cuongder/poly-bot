import unittest
from core.risk_manager import RiskManager

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()
        
    def test_calculate_position_size(self):
        account_balance = 10000
        win_rate = 0.60
        avg_win = 200
        avg_loss = 100
        
        # Kelly = W - ((1-W) / (W/L_ratio))
        # Kelly = 0.6 - (0.4 / 2) = 0.4
        # Half Kelly = 0.2 (20%)
        # Cap is 5% natively in RiskManager
        
        size = self.rm.calculate_position_size(account_balance, win_rate, avg_win, avg_loss)
        
        # Should be capped at 5% of 10000 => 500
        self.assertAlmostEqual(size, 500.0)
        
    def test_circuit_breakers_drawdown(self):
        res = self.rm.check_circuit_breakers(daily_pnl_pct=-0.02, total_drawdown_pct=-0.12, consecutive_losses=2)
        self.assertTrue(res['should_stop_trading'])
        self.assertIn("Max drawdown hit", res['reason'])

    def test_circuit_breakers_consecutive_losses(self):
        res = self.rm.check_circuit_breakers(daily_pnl_pct=-0.01, total_drawdown_pct=-0.02, consecutive_losses=6)
        self.assertFalse(res['should_stop_trading'])
        self.assertTrue(res['reduce_size'])

if __name__ == '__main__':
    unittest.main()
