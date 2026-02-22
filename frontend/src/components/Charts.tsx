import React from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface Trade {
  id: number;
  net_pnl: number;
  open_time: string;
}

interface ChartsProps {
  trades: Trade[];
}

export function Charts({ trades }: ChartsProps) {
  // Calculate equity curve from trades
  const calculateEquityCurve = () => {
    if (!trades || trades.length === 0) {
      return [{ time: 'Start', equity: 100, drawdown: 0 }];
    }

    // Sort trades by time
    const sortedTrades = [...trades].sort((a, b) =>
      new Date(a.open_time).getTime() - new Date(b.open_time).getTime()
    );

    let equity = 100; // Starting balance
    let peak = equity;
    const data = [];

    for (const trade of sortedTrades) {
      equity += trade.net_pnl;
      if (equity > peak) peak = equity;
      const drawdown = ((peak - equity) / peak) * 100;

      data.push({
        time: new Date(trade.open_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        equity: parseFloat(equity.toFixed(2)),
        drawdown: parseFloat(drawdown.toFixed(2))
      });
    }

    return data;
  };

  const chartData = calculateEquityCurve();

  return (
    <div className="mb-4 border border-gray-700 bg-gray-800 p-4 rounded">
      <div className="text-sm text-gray-400 mb-4 font-semibold">EQUITY CURVE</div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              stroke="#9ca3af"
              tick={{ fontSize: 12, fill: '#9ca3af' }}
            />
            <YAxis
              yAxisId="left"
              stroke="#22c55e"
              tick={{ fontSize: 12, fill: '#22c55e' }}
              domain={['auto', 'auto']}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                borderColor: '#374151',
                color: '#f3f4f6'
              }}
              itemStyle={{ color: '#22c55e' }}
              formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Equity']}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="equity"
              stroke="#22c55e"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorEquity)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {chartData.length > 1 && (
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <span className="text-xs text-gray-500 block">Start Balance</span>
            <span className="text-gray-300 font-mono">${chartData[0].equity.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-xs text-gray-500 block">Current Balance</span>
            <span className="text-gray-300 font-mono">${chartData[chartData.length - 1].equity.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-xs text-gray-500 block">Total Return</span>
            <span className={`font-mono ${
              chartData[chartData.length - 1].equity >= chartData[0].equity
                ? 'text-green-400'
                : 'text-red-400'
            }`}>
              {((chartData[chartData.length - 1].equity / chartData[0].equity - 1) * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
