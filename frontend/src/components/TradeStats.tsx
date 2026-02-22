import React from 'react';

interface Trade {
  id: number;
  net_pnl: number;
  entry_price: number;
  exit_price: number | null;
}

interface TradeStatsProps {
  trades: Trade[];
  bestTx: Trade | null;
  worstTx: Trade | null;
}

export function TradeStats({ trades, bestTx, worstTx }: TradeStatsProps) {
  // Calculate max drawdown from trades
  const calculateMaxDrawdown = () => {
    if (trades.length === 0) return 0;

    let peak = 0;
    let maxDrawdown = 0;
    let runningPnl = 0;

    for (const trade of trades) {
      runningPnl += trade.net_pnl;
      if (runningPnl > peak) {
        peak = runningPnl;
      }
      const drawdown = peak - runningPnl;
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown;
      }
    }

    return maxDrawdown;
  };

  const maxDrawdown = calculateMaxDrawdown();

  return (
    <div className="grid grid-cols-3 divide-x divide-gray-700 border border-gray-700 bg-gray-800 text-sm mb-4 rounded">
      <div className="p-3 text-center">
        <span className="text-gray-400 block text-xs mb-1">Best Trade</span>
        <span className="text-green-400 font-mono">
          {bestTx ? `$${bestTx.net_pnl.toFixed(2)}` : '-'}
        </span>
      </div>
      <div className="p-3 text-center">
        <span className="text-gray-400 block text-xs mb-1">Worst Trade</span>
        <span className="text-red-400 font-mono">
          {worstTx ? `$${worstTx.net_pnl.toFixed(2)}` : '-'}
        </span>
      </div>
      <div className="p-3 text-center">
        <span className="text-gray-400 block text-xs mb-1">Max Drawdown</span>
        <span className="text-red-400 font-mono">
          ${maxDrawdown.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
