import React from 'react';

interface Trade {
  id: number;
  market: string;
  direction: string;
  entry_price: number;
  exit_price: number | null;
  fee_paid: number;
  gross_pnl: number;
  net_pnl: number;
  status: string;
  open_time: string;
}

interface CategoryTableProps {
  trades: Trade[];
}

export function CategoryTable({ trades }: CategoryTableProps) {
  if (!trades || trades.length === 0) {
    return (
      <div className="mb-4 text-sm border border-gray-700 bg-gray-800 rounded p-4 text-gray-400">
        No trade history available
      </div>
    );
  }

  // Show recent trades (last 10)
  const recentTrades = trades.slice(0, 10);

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleString();
  };

  return (
    <div className="mb-4 text-sm border border-gray-700 bg-gray-800 overflow-x-auto rounded">
      <div className="p-3 bg-gray-700/50 border-b border-gray-700 font-semibold text-gray-300">
        Recent Trades
      </div>
      <table className="w-full text-left border-collapse">
        <thead className="bg-gray-700/30 border-b border-gray-700 text-gray-400 text-xs">
          <tr>
            <th className="p-2 font-normal">ID</th>
            <th className="p-2 font-normal">TIME</th>
            <th className="p-2 font-normal">DIR</th>
            <th className="p-2 font-normal">ENTRY</th>
            <th className="p-2 font-normal">EXIT</th>
            <th className="p-2 font-normal">STATUS</th>
            <th className="p-2 font-normal text-right">FEE</th>
            <th className="p-2 font-normal text-right">PNL</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700 text-gray-200">
          {recentTrades.map((trade) => (
            <tr key={trade.id} className="hover:bg-gray-700/30">
              <td className="p-2 font-mono text-xs">#{trade.id}</td>
              <td className="p-2 text-xs">{formatTime(trade.open_time)}</td>
              <td className="p-2">
                <span className={trade.direction === 'YES' ? 'text-green-400' : 'text-red-400'}>
                  {trade.direction === 'YES' ? '▲ YES' : '▼ NO'}
                </span>
              </td>
              <td className="p-2 font-mono">{trade.entry_price.toFixed(4)}</td>
              <td className="p-2 font-mono">
                {trade.exit_price ? trade.exit_price.toFixed(4) : '-'}
              </td>
              <td className="p-2">
                <span className={`px-2 py-0.5 rounded text-xs ${
                  trade.status === 'CLOSED'
                    ? 'bg-gray-700 text-gray-300'
                    : 'bg-yellow-900/50 text-yellow-400'
                }`}>
                  {trade.status}
                </span>
              </td>
              <td className="p-2 text-right text-red-400 font-mono">
                ${trade.fee_paid.toFixed(2)}
              </td>
              <td className={`p-2 text-right font-bold font-mono ${
                trade.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {trade.net_pnl >= 0 ? '+' : '-'}${Math.abs(trade.net_pnl).toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
