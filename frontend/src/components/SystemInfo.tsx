import React from 'react';

interface SystemInfoProps {
    data: any;
}

export function SystemInfo({ data }: SystemInfoProps) {
    if (!data) return <div className="p-4 border border-borderC border-t-0 text-textSecondary">Loading System Info...</div>;

    return (
        <div className="border border-borderC border-t-0 bg-bgMain p-4 text-sm leading-relaxed text-textPrimary">
            <div><span className="text-textSecondary">┌─ </span>OpenClaw booted at {data.boot_time || 'N/A'}</div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Wallet <span className="text-secondary">{data.wallet || 'N/A'}</span> •
                Live Balance: <span className="text-success">{data.live_balance || '...'}</span> •
                Demo Balance: <span className="text-warning">{data.demo_balance || '...'}</span>
            </div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Network {data.network || 'N/A'} • chain_id={data.chain_id || 'N/A'} • <span className="text-success">gas ok</span>
            </div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Markets <span className="text-accent">{data.markets || 'N/A'}</span>
            </div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Mode <span className={`${data.mode === 'DEMO' ? 'text-warning' : 'text-danger'} font-bold uppercase`}>[{data.mode || 'LIVE'}]</span>
            </div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Strategy {data.strategy || 'N/A'}
            </div>
            <div>
                <span className="text-textSecondary">├─ </span>
                Risk/trade max 5% • stop-loss <span className="text-success">on</span> • auto-compound <span className="text-success">on</span>
            </div>
            <div>
                <span className="text-textSecondary">└─ </span>
                Session up <span className="text-success">{data.uptime || '00:00:00'}</span>
            </div>
        </div >
    );
}
