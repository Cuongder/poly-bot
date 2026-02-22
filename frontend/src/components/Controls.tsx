import React, { useState } from 'react';

interface ControlsProps {
  apiKey: string;
  apiBaseUrl: string;
}

export function Controls({ apiKey, apiBaseUrl }: ControlsProps) {
  const [isDemo, setIsDemo] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleAction = async (action: string, modeOverride?: string) => {
    setLoading(true);
    setMessage('');

    try {
      const currentMode = modeOverride || (isDemo ? 'demo' : 'live');
      const response = await fetch(`${apiBaseUrl}/api/bot/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ mode: currentMode })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setMessage(data.message || `${action} successful`);
    } catch (e) {
      console.error(e);
      setMessage(`Error: ${e instanceof Error ? e.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleDemo = () => {
    const newDemoState = !isDemo;
    setIsDemo(newDemoState);
  };

  return (
    <div className="border border-gray-700 bg-gray-800 p-4 rounded">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex space-x-4 items-center">
          <button
            onClick={() => handleAction('start')}
            disabled={loading}
            className="px-6 py-2 bg-gray-900 border border-gray-600 text-green-400 hover:bg-gray-700 transition-colors disabled:opacity-50 rounded"
          >
            {loading ? '...' : '[Start]'}
          </button>
          <button
            onClick={() => handleAction('stop')}
            disabled={loading}
            className="px-6 py-2 bg-gray-900 border border-gray-600 text-red-400 hover:bg-gray-700 transition-colors disabled:opacity-50 rounded"
          >
            {loading ? '...' : '[Stop]'}
          </button>
          <button
            onClick={() => handleAction('pause')}
            disabled={loading}
            className="px-6 py-2 bg-gray-900 border border-gray-600 text-yellow-400 hover:bg-gray-700 transition-colors disabled:opacity-50 rounded"
          >
            {loading ? '...' : '[Pause]'}
          </button>

          {/* Demo Toggle */}
          <div className="flex items-center ml-8 space-x-2">
            <span className="text-sm text-gray-400 uppercase tracking-wider">Demo Mode</span>
            <button
              onClick={toggleDemo}
              className={`w-12 h-6 rounded-full p-1 flex transition-colors cursor-pointer border border-gray-600`}
              style={{ backgroundColor: isDemo ? '#22c55e' : '#4b5563' }}
            >
              <div className={`bg-gray-900 w-4 h-4 rounded-full shadow-md transform transition-transform ${isDemo ? 'translate-x-6' : ''}`}></div>
            </button>
          </div>
        </div>

        <div className="text-gray-400 text-sm">
          {message ? (
            <span className={message.includes('Error') ? 'text-red-400' : 'text-green-400'}>
              {message}
            </span>
          ) : (
            'Bot Controls'
          )}
        </div>
      </div>
    </div>
  );
}
