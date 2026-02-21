import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { SystemInfo } from './components/SystemInfo';
import { PerformanceCards } from './components/PerformanceCards';
import { TradeStats } from './components/TradeStats';
import { CategoryTable } from './components/CategoryTable';
import { PnlBars } from './components/PnlBars';
import { Controls } from './components/Controls';
import { Charts } from './components/Charts';

// Initial empty data for real Live mode
const defaultCategories: any[] = [];

const defaultPnlBars: any[] = [];

function App() {
  const [statusData, setStatusData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);

  useEffect(() => {
    // Initial fetch, use cache bust
    const timestamp = Date.now();
    fetch(`http://localhost:8000/api/status?t=${timestamp}`).then(res => res.json()).then(setStatusData).catch(() => { });
    fetch(`http://localhost:8000/api/performance?t=${timestamp}`).then(res => res.json()).then(setPerfData).catch(() => { });


    // WebSocket connection
    const ws = new WebSocket('ws://localhost:8000/ws/live');

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'tick') {
          if (data.status) setStatusData(data.status);
          if (data.performance) setPerfData(data.performance);
        }
      } catch (e) {
        console.error("WS Parse error", e);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen p-2 md:p-4 lg:p-8 max-w-[1200px] mx-auto">
      <div className="flex flex-col mb-4">
        <Header status={statusData?.status || 'OFFLINE'} />
        <SystemInfo data={statusData} />
      </div>

      <PerformanceCards data={perfData} />

      <TradeStats
        bestTx="Waiting for trades..."
        worstTx="Waiting for trades..."
        maxDd="0.00%"
      />

      <Charts data={[]} />

      <CategoryTable data={defaultCategories} />
      <PnlBars data={defaultPnlBars} />
      <Controls />
    </div>
  );
}

export default App;
