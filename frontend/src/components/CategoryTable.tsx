import React from 'react';

interface CategoryData {
    market: string;
    isStar?: boolean;
    dir: 'UP' | 'DN';
    trades: number;
    w: number;
    l: number;
    winPct: number;
    grossPnl: number;
    fees: number;
    netPnl: number;
}

interface CategoryTableProps {
    data: CategoryData[];
}

export function CategoryTable({ data }: CategoryTableProps) {
    if (!data || data.length === 0) return null;

    return (
        <div className="mb-4 text-sm border border-borderC bg-bgMain overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead className="bg-bgCard border-b border-borderC text-textSecondary">
                    <tr>
                        <th className="p-2 font-normal">MARKET</th>
                        <th className="p-2 font-normal">DIR</th>
                        <th className="p-2 font-normal">TRADES</th>
                        <th className="p-2 font-normal">W/L</th>
                        <th className="p-2 font-normal">WIN%</th>
                        <th className="p-2 font-normal text-right">GROSS PNL</th>
                        <th className="p-2 font-normal text-right">FEES</th>
                        <th className="p-2 font-normal text-right">NET PNL</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-borderC text-textPrimary">
                    {data.map((row, i) => (
                        <tr key={i} className="hover:bg-bgCard">
                            <td className="p-2">{row.market} {row.isStar && '★'}</td>
                            <td className="p-2">
                                <span className={row.dir === 'UP' ? 'text-success' : 'text-danger'}>
                                    {row.dir === 'UP' ? '▲ UP' : '▼ DN'}
                                </span>
                            </td>
                            <td className="p-2">{row.trades}</td>
                            <td className="p-2">{row.w}W/{row.l}L</td>
                            <td className="p-2">{row.winPct.toFixed(1)}%</td>
                            <td className={`p-2 text-right ${row.grossPnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                {row.grossPnl >= 0 ? '+' : '-'}${Math.abs(row.grossPnl).toFixed(2)}
                            </td>
                            <td className="p-2 text-right text-danger">-${Math.abs(row.fees).toFixed(2)}</td>
                            <td className={`p-2 text-right font-bold ${row.netPnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                {row.netPnl >= 0 ? '+' : '-'}${Math.abs(row.netPnl).toFixed(2)}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
