import React from 'react';

interface Trade {
  id: number;
  direction: string;
  net_pnl: number;
}

interface PnlBarsProps {
  trades: Trade[];
}

export function PnlBars({ trades }: PnlBarsProps) {
  if (!trades || trades.length === 0) {
    return (
      <div className="mb-4 p-4 text-sm border border-gray-700 bg-gray-800 rounded text-gray-400">
        No PnL data available
      </div>
    );
  }

  // Get last 10 trades for visualization
  const recentTrades = trades.slice(0, 10);

  // Find max absolute PnL for scaling
  const maxPnL = Math.max(...recentTrades.map(t => Math.abs(t.net_pnl)), 1);

  const renderBar = (pnl: number) => {
    const percentage = (Math.abs(pnl) / maxPnL) * 100;
    const totalBlocks = 20;
    const filledBlocks = Math.round((percentage / 100) * totalBlocks);

    const barChar = pnl >= 0 ? '█' : '█';
    const colorClass = pnl >= 0 ? 'text-green-500' : 'text-red-500';

    return (
      <span className={colorClass}>
        {barChar.repeat(Math.max(0, filledBlocks))}
      </span>
    );
  };

  return (
    <div className="mb-4 p-4 text-sm border border-gray-700 bg-gray-800 font-mono space-y-2 rounded">
      <div className="text-gray-400 mb-3 font-semibold">Recent Trade PnL</div>
      {recentTrades.map((trade) => (
        <div key={trade.id} className="flex justify-between items-center">
          <div className="w-1/4 text-gray-300">
            <span className="text-xs text-gray-500">#{trade.id}</span>
            {' '}
            <span className={trade.direction === 'YES' ? 'text-green-400' : 'text-red-400'}>
              {trade.direction === 'YES' ? '▲' : '▼'}
            </span>
          </div>
          <div className="w-1/2">
            {renderBar(trade.net_pnl)}
          </div>
          <div className={`w-1/4 text-right font-bold ${
            trade.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {trade.net_pnl >= 0 ? '+' : '-'}${Math.abs(trade.net_pnl).toFixed(2)}
          </div>
        </div>
      ))}
    </div>
  );
}
