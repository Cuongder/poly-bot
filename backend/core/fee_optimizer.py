class FeeOptimizer:
    def __init__(self, avg_fee_per_trade=0.25):
        self.avg_fee_per_trade = avg_fee_per_trade
        self.min_edge = 0.015  # 1.5%
        
    def should_enter(self, expected_gross_pnl_pct: float) -> bool:
        """Only enter if edge > fees + min_profit"""
        # We assume expected_gross_pnl_pct is the expected ROI in percentage
        # Since avg_fee_per_trade is in USD, we need the account size or position size to get percentage.
        # But based on the prompt signature:
        # expected_pnl_pct > (self.avg_fee_per_trade * 2 + self.min_edge)
        return expected_gross_pnl_pct > (self.avg_fee_per_trade * 2 + self.min_edge)
    
    def batch_orders(self, pending_orders: list) -> list:
        """Combine small DCA orders into larger ones to save fees."""
        if not pending_orders:
            return []
            
        batched = {}
        for order in pending_orders:
            market = order.get('market')
            direction = order.get('direction')
            size = order.get('size', 0)
            
            key = (market, direction)
            if key not in batched:
                batched[key] = {'market': market, 'direction': direction, 'size': 0}
            
            batched[key]['size'] += size
            
        return list(batched.values())
