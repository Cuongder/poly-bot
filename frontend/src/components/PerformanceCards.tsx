import React from 'react';

interface CardProps {
    label: string;
    value: string | number;
    color?: 'green' | 'red' | 'blue' | 'default';
    prefix?: string;
    suffix?: string;
}

const Card = ({ label, value, color = 'default', prefix = '', suffix = '' }: CardProps) => {
    let colorClass = 'text-textPrimary';
    if (color === 'green') colorClass = 'text-success';
    if (color === 'red') colorClass = 'text-danger';
    if (color === 'blue') colorClass = 'text-accent';

    return (
        <div className="flex flex-col items-center justify-center border border-borderC bg-bgCard p-4">
            <div className={`text-2xl font-bold ${colorClass}`}>
                [{prefix}{value}{suffix}]
            </div>
            <div className="text-xs text-textSecondary uppercase tracking-widest mt-2">
                {label}
            </div>
        </div>
    );
};

interface PerformanceCardsProps {
    data: any;
}

export function PerformanceCards({ data }: PerformanceCardsProps) {
    if (!data) return null;

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 mb-4 gap-[1px] bg-borderC border border-borderC">
            <Card label="NET PNL" value={data.netPnl} color={data.netPnl >= 0 ? "green" : "red"} prefix={data.netPnl > 0 ? "+$" : "-$"} />
            <Card label="GROSS PNL" value={data.grossPnl} color={data.grossPnl >= 0 ? "green" : "red"} prefix={data.grossPnl > 0 ? "+$" : "-$"} />
            <Card label="WIN RATE" value={data.winRate} color="blue" suffix="%" />
            <Card label="TRADES" value={data.trades} />
            <Card label="FEES PAID" value={Math.abs(data.fees)} color="red" prefix="-$" />
            <Card label="AVG NET/TX" value={data.avgNet} color={data.avgNet >= 0 ? "green" : "red"} prefix={data.avgNet > 0 ? "+$" : "-$"} />
        </div>
    );
}
