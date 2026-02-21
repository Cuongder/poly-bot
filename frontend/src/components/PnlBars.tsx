import React from 'react';

interface PnlBarData {
    label: string;
    dir: 'UP' | 'DN';
    pnl: number;
    percentage: number; // 0 to 100
}

interface PnlBarsProps {
    data: PnlBarData[];
}

export function PnlBars({ data }: PnlBarsProps) {
    if (!data || data.length === 0) return null;

    const renderBar = (pct: number) => {
        // Console style block characters
        const totalBlocks = 20;
        const filledBlocks = Math.round((pct / 100) * totalBlocks);
        const emptyBlocks = totalBlocks - filledBlocks;

        return '█'.repeat(Math.max(0, filledBlocks)) + '░'.repeat(Math.max(0, emptyBlocks));
    };

    return (
        <div className="mb-4 p-4 text-sm border border-borderC bg-bgMain font-mono space-y-2">
            {data.map((item, i) => (
                <div key={i} className="flex justify-between items-center group">
                    <div className="w-1/3 text-textPrimary">
                        {item.label} <span className={item.dir === 'UP' ? 'text-success' : 'text-danger'}>
                            {item.dir === 'UP' ? '▲ UP' : '▼ DN'}
                        </span>
                    </div>
                    <div className="w-1/3 text-center tracking-widest text-[#58a6ff]">
                        [{renderBar(item.percentage)}]
                    </div>
                    <div className={`w-1/3 text-right ${item.pnl >= 0 ? 'text-success' : 'text-danger'} font-bold`}>
                        {item.pnl >= 0 ? '+' : '-'}${Math.abs(item.pnl).toFixed(2)}
                    </div>
                </div>
            ))}
        </div>
    );
}
