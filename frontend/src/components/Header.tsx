import React, { useState, useEffect } from 'react';

interface HeaderProps {
    status: string;
}

export function Header({ status }: HeaderProps) {
    const [time, setTime] = useState(new Date().toLocaleTimeString());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    const getStatusColor = (s: string) => {
        switch (s) {
            case 'LIVE': return 'text-success';
            case 'PAUSED': return 'text-warning';
            default: return 'text-danger';
        }
    };

    return (
        <div className="flex justify-between items-center border border-borderC bg-bgCard p-2 text-sm text-textPrimary">
            <div className="flex items-center space-x-2">
                <span className="text-xl">■ ● ▲</span>
                <span>OpenClaw ─── polymarket-bot ─── zsh ─── 120x45</span>
            </div>
            <div className="flex items-center space-x-4">
                <span className={`font-bold ${getStatusColor(status)}`}>[{status}]</span>
                <span>{time}</span>
            </div>
        </div>
    );
}
