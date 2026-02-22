import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { SystemInfo } from './components/SystemInfo';
import { PerformanceCards } from './components/PerformanceCards';
import { TradeStats } from './components/TradeStats';
import { CategoryTable } from './components/CategoryTable';
import { PnlBars } from './components/PnlBars';
import { Controls } from './components/Controls';
import { Charts } from './components/Charts';
import { PositionPanel } from './components/PositionPanel';
import { AuthPanel } from './components/AuthPanel';

const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/live';

interface Trade {
  id: number;
  market: string;
  direction: string;
  size: number;
  entry_price: number;
  exit_price: number | null;
  fee_paid: number;
  gross_pnl: number;
  net_pnl: number;
  status: string;
  close_reason: string | null;
  open_time: string;
  close_time: string | null;
}

interface Position {
  id: number;
  market: string;
  direction: string;
  size: number;
  entry_price: number;
  entry_time: string;
  stop_loss: number;
  take_profit: number;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [apiKey, setApiKey] = useState<string>('');
  const [statusData, setStatusData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [openPosition, setOpenPosition] = useState<Position | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load API key from localStorage on mount
  useEffect(() => {
    const savedApiKey = localStorage.getItem('polybot_api_key');
    if (savedApiKey) {
      setApiKey(savedApiKey);
      setIsAuthenticated(true);
    }
  }, []);

  // Fetch data with API key
  const fetchWithAuth = useCallback(async (endpoint: string) => {
    if (!apiKey) return null;
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'X-API-Key': apiKey,
        },
      });
      if (response.status === 401) {
        setIsAuthenticated(false);
        setApiKey('');
        localStorage.removeItem('polybot_api_key');
        throw new Error('Invalid API key');
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error(`Error fetching ${endpoint}:`, err);
      return null;
    }
  }, [apiKey]);

  // Initial data fetch
  useEffect(() => {
    if (!isAuthenticated || !apiKey) return;

    const fetchData = async () => {
      const [status, performance, tradesData] = await Promise.all([
        fetchWithAuth('/api/status'),
        fetchWithAuth('/api/performance'),
        fetchWithAuth('/api/trades?limit=50'),
      ]);

      if (status) setStatusData(status);
      if (performance) setPerfData(performance);
      if (tradesData) setTrades(tradesData);
      if (status?.open_position) setOpenPosition(status.open_position);
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [isAuthenticated, apiKey, fetchWithAuth]);

  // WebSocket connection with auto-reconnect
  const connectWebSocket = useCallback(() => {
    if (!isAuthenticated || wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'tick') {
          if (data.status) {
            setStatusData(data.status);
            if (data.status.open_position) {
              setOpenPosition(data.status.open_position);
            } else {
              setOpenPosition(null);
            }
          }
          if (data.performance) setPerfData(data.performance);
        }
      } catch (e) {
        console.error('WS Parse error:', e);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
      wsRef.current = null;

      // Auto-reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting to reconnect...');
        connectWebSocket();
      }, 5000);
    };

    wsRef.current = ws;
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      connectWebSocket();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isAuthenticated, connectWebSocket]);

  const handleAuth = (key: string) => {
    setApiKey(key);
    setIsAuthenticated(true);
    localStorage.setItem('polybot_api_key', key);
  };

  const handleLogout = () => {
    setApiKey('');
    setIsAuthenticated(false);
    localStorage.removeItem('polybot_api_key');
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <AuthPanel onAuth={handleAuth} apiBaseUrl={API_BASE_URL} />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-2 md:p-4 lg:p-8 max-w-[1200px] mx-auto bg-gray-900 text-gray-100">
      {/* Connection Status */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">WS:</span>
          <span className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-400">
            {connectionStatus === 'connected' ? 'Connected' :
             connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-red-400 hover:text-red-300 px-3 py-1 border border-red-400 rounded"
        >
          Logout
        </button>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded mb-4">
          {error}
        </div>
      )}

      <div className="flex flex-col mb-4">
        <Header status={statusData?.status || 'OFFLINE'} />
        <SystemInfo data={statusData} />
      </div>

      {/* Open Position Panel */}
      <PositionPanel position={openPosition} />

      <PerformanceCards data={perfData} />

      <TradeStats
        trades={trades}
        bestTx={trades.length > 0
          ? trades.reduce((max, t) => t.net_pnl > max.net_pnl ? t : max, trades[0])
          : null}
        worstTx={trades.length > 0
          ? trades.reduce((min, t) => t.net_pnl < min.net_pnl ? t : min, trades[0])
          : null}
      />

      <Charts trades={trades} />

      <CategoryTable trades={trades} />
      <PnlBars trades={trades} />
      <Controls apiKey={apiKey} apiBaseUrl={API_BASE_URL} />
    </div>
  );
}

export default App;
