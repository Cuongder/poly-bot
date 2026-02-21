import React from 'react';

interface TradeStatsProps {
    bestTx: string;
    worstTx: string;
    maxDd: string;
}

export function TradeStats({ bestTx, worstTx, maxDd }: TradeStatsProps) {
    return (
        <div className="grid grid-cols-3 divide-x divide-borderC border border-borderC bg-bgMain text-sm mb-4">
            <div className="p-2 text-center">
                <span className="text-textSecondary">Best tx</span> <span className="text-success">{bestTx}</span>
            </div>
            <div className="p-2 text-center">
                <span className="text-textSecondary">Worst tx</span> <span className="text-danger">{worstTx}</span>
            </div>
            <div className="p-2 text-center">
                <span className="text-textSecondary">Max DD</span> <span className="text-danger">{maxDd}</span>
            </div>
        </div>
    );
}
