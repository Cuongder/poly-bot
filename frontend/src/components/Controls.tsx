import React, { useState } from 'react';

export function Controls() {
    const [isDemo, setIsDemo] = useState(true);

    const handleAction = async (action: string, modeOverride?: string) => {
        try {
            const currentMode = modeOverride || (isDemo ? 'demo' : 'live');
            await fetch(`http://localhost:8000/api/bot/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: currentMode })
            });
        } catch (e) {
            console.error(e);
        }
    };

    const toggleDemo = () => {
        const newDemoState = !isDemo;
        setIsDemo(newDemoState);
        // Only update mode if we are assumed to act on Start config directly
        handleAction('start', newDemoState ? 'demo' : 'live');
    };

    return (
        <div className="flex justify-between items-center border border-borderC bg-bgCard p-4">
            <div className="flex space-x-4 items-center">
                <button
                    onClick={() => handleAction('start')}
                    className="px-6 py-2 bg-bgMain border border-borderC text-success hover:bg-borderC transition-colors"
                >
                    [Start]
                </button>
                <button
                    onClick={() => handleAction('stop')}
                    className="px-6 py-2 bg-bgMain border border-borderC text-danger hover:bg-borderC transition-colors"
                >
                    [Stop]
                </button>
                <button
                    onClick={() => handleAction('pause')}
                    className="px-6 py-2 bg-bgMain border border-borderC text-warning hover:bg-borderC transition-colors"
                >
                    [Pause]
                </button>

                {/* Demo Toggle */}
                <div className="flex items-center ml-8 space-x-2">
                    <span className="text-sm text-textSecondary uppercase tracking-wider">Demo Mode</span>
                    <button
                        onClick={toggleDemo}
                        className={`w-12 h-6 rounded-full p-1 flex data-on:bg-accent bg-borderC transition-colors cursor-pointer border border-borderC `}
                        style={{ backgroundColor: isDemo ? '#58a6ff' : '#30363d' }}
                    >
                        <div className={`bg-bgMain w-4 h-4 rounded-full shadow-md transform transition-transform ${isDemo ? 'translate-x-6' : ''}`}></div>
                    </button>
                </div>

            </div>
            <div className="text-textSecondary text-sm">
                Config Panel (Click to expand)
            </div>
        </div>
    );
}
