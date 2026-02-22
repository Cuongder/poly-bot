import React from 'react';

interface Position {
  id: number;
  market: string;
  direction: string;
  size: number;
  entry_price: number;
  entry_time: string;
  stop_loss: number;
  take_profit: number;
}

interface PositionPanelProps {
  position: Position | null;
}

export const PositionPanel: React.FC<PositionPanelProps> = ({ position }) => {
  if (!position) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4">
        <h3 className="text-lg font-semibold text-gray-300 mb-2">Open Position</h3>
        <p className="text-gray-500 text-sm">No open position</p>
      </div>
    );
  }

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleString();
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-semibold text-gray-300">Open Position</h3>
        <span className={`px-2 py-1 rounded text-sm font-medium ${
          position.direction === 'YES' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
        }`}>
          {position.direction}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-gray-500">Entry Price</p>
          <p className="text-lg font-mono text-gray-200">{position.entry_price.toFixed(4)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Size</p>
          <p className="text-lg font-mono text-gray-200">${position.size.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Stop Loss</p>
          <p className="text-lg font-mono text-red-400">{position.stop_loss.toFixed(4)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Take Profit</p>
          <p className="text-lg font-mono text-green-400">{position.take_profit.toFixed(4)}</p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700">
        <p className="text-xs text-gray-500">
          Entry Time: {formatTime(position.entry_time)}
        </p>
      </div>
    </div>
  );
};
