import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartsProps {
    data: any[];
}

// Mocking chart data based on requirements
const mockChartData = [
    { time: '00:00', equity: 10000, dd: 0 },
    { time: '04:00', equity: 10100, dd: -10 },
    { time: '08:00', equity: 10050, dd: -50 },
    { time: '12:00', equity: 10200, dd: -20 },
    { time: '16:00', equity: 10400, dd: 0 },
    { time: '20:00', equity: 10350, dd: -50 },
    { time: '24:00', equity: 10600, dd: 0 },
];

export function Charts({ data = mockChartData }: ChartsProps) {
    return (
        <div className="mb-4 border border-borderC bg-bgCard p-4">
            <div className="text-sm text-textSecondary mb-4">EQUITY CURVE (Past 24h)</div>
            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                        <XAxis dataKey="time" stroke="#8b949e" tick={{ fontSize: 12, fill: '#8b949e' }} />
                        <YAxis
                            yAxisId="left"
                            stroke="#3fb950"
                            tick={{ fontSize: 12, fill: '#3fb950' }}
                            domain={['auto', 'auto']}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#161b22', borderColor: '#30363d', color: '#c9d1d9' }}
                            itemStyle={{ color: '#3fb950' }}
                        />
                        <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="equity"
                            stroke="#3fb950"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
