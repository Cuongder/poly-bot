import React, { useState } from 'react';

interface AuthPanelProps {
  onAuth: (apiKey: string) => void;
  apiBaseUrl: string;
}

export const AuthPanel: React.FC<AuthPanelProps> = ({ onAuth, apiBaseUrl }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [mode, setMode] = useState<'login' | 'apikey'>('apikey');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Create API key using JWT token
      const keyResponse = await fetch(`${apiBaseUrl}/api/auth/apikey?name=frontend&permissions=write`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });

      if (!keyResponse.ok) {
        throw new Error('Failed to create API key');
      }

      const keyData = await keyResponse.json();
      onAuth(keyData.api_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKeyInput.trim()) {
      onAuth(apiKeyInput.trim());
    }
  };

  return (
    <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full border border-gray-700">
      <h1 className="text-2xl font-bold text-green-400 mb-2 text-center">Poly-bot</h1>
      <p className="text-gray-400 text-center mb-6">Trading Dashboard</p>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode('apikey')}
          className={`flex-1 py-2 rounded ${mode === 'apikey' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300'}`}
        >
          API Key
        </button>
        <button
          onClick={() => setMode('login')}
          className={`flex-1 py-2 rounded ${mode === 'login' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300'}`}
        >
          Login
        </button>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {mode === 'apikey' ? (
        <form onSubmit={handleApiKeySubmit} className="space-y-4">
          <div>
            <label className="block text-gray-400 text-sm mb-1">API Key</label>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="Enter your API key"
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-green-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-green-600 hover:bg-green-500 text-white py-2 rounded transition-colors"
          >
            Connect
          </button>
        </form>
      ) : (
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-gray-400 text-sm mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-green-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-green-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white py-2 rounded transition-colors"
          >
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>
      )}

      <p className="text-xs text-gray-500 mt-4 text-center">
        Default: admin / admin
      </p>
    </div>
  );
};
