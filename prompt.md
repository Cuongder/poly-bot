# PROMPT FOR ANTIGRAVITY - POLYMARKET BOT WITH WEB DASHBOARD

## 🎯 BỐI CẢNH

Tôi đang chạy 1 bot giao dịch UP/DOWN BTC trên Polymarket (prediction market trên Polygon Mainnet). Bot hiện tại có win rate 60% nhưng risk management chưa tốt, leverage quá cao (3x-7x), drawdown lớn (-13.7%).

**YÊU CẦU QUAN TRỌNG:** Tôi cần **bot + web dashboard** giống style ảnh đính kèm (dark theme, terminal-style, real-time metrics).

---

## 🚀 YÊU CẦU TỔNG QUAN

### 1. Backend (Python FastAPI)
- Kelly Criterion Position Sizing (Half Kelly, max 5%)
- Multi-Timeframe Correlation Filter (5m vs 15m)
- ATR-based Trailing Stop (1.5x ATR 1H, max leverage 3x)
- Fee Optimizer (batch orders, min edge 1.5%)
- Circuit Breakers (stop at -10% drawdown)
- REST API + WebSocket

### 2. Frontend (React + TailwindCSS)
**UI GIỐNG ẢNH MẪU:**
- Dark theme (đen + xanh lá + xanh dương)
- Header: Logo, status LIVE/OFFLINE, clock
- System Info Panel: Wallet, Network, Markets, Strategy, Risk
- Performance Cards: NET PNL, GROSS PNL, WIN RATE, TRADES, FEES, AVG NET/TX
- Trade Stats: Best/Worst trade, streaks, drawdown
- Category Table: Breakdown theo market và direction
- PNL Bars: Progress bars hiển thị PNL by category
- Controls: Start/Stop/Pause buttons, config panel

---

## 📁 CẤU TRÚC FILE

```
polymarket_bot/
├── backend/
│   ├── api/main.py            # FastAPI + WebSocket
│   ├── core/
│   │   ├── risk_manager.py    # ⭐ QUAN TRỌNG NHẤT
│   │   ├── signal_generator.py
│   │   ├── correlation_analyzer.py
│   │   ├── fee_optimizer.py
│   │   ├── session_filter.py
│   │   └── polymarket_client.py
│   └── config/settings.yaml
├── frontend/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── SystemInfo.tsx
│   │   ├── PerformanceCards.tsx
│   │   ├── TradeStats.tsx
│   │   ├── CategoryTable.tsx
│   │   ├── PnlBars.tsx
│   │   └── Controls.tsx
│   └── pages/index.tsx
└── docker-compose.yml
```

---

## 🎨 UI SPECIFICATIONS (COPY ẢNH MẪU)

### Color Scheme
- Background: #0d1117 (dark github)
- Card background: #161b22
- Border: #30363d
- Text primary: #c9d1d9
- Text secondary: #8b949e
- Green (profit): #3fb950
- Red (loss): #f85149
- Blue (accent): #58a6ff
- Yellow (warning): #d29922

### Typography
- Font: JetBrains Mono hoặc Fira Code (monospace)
- Header: 16-18px bold
- Cards: 24-32px for numbers, 12px for labels
- Table: 13-14px

### Layout (giống ảnh)
```
┌─────────────────────────────────────────────────────────────┐
│ ■ ● ▲  OpenClaw ─── polymarket-bot ─── zsh      [LIVE]    │
├─────────────────────────────────────────────────────────────┤
│ ┌─ OpenClaw booted at 2026-02-19 14:52:07 UTC+7            │
│ ├─ Wallet 0x3fA9...c82E • Polymarket account verified ✓    │
│ ├─ Network Polygon Mainnet • chain_id=137 • gas ok         │
│ ├─ Markets BTC/USD UP-DOWN 5min, BTC/USD UP-DOWN 15min     │
│ ├─ Strategy momentum_v3 + vol_filter + rsi_14              │
│ └─ Session up 00:00:29                                     │
├─────────────────────────────────────────────────────────────┤
│  [+$612.40]  [+$738.90]  [60.2%]  [500]  [-$126.50]        │
│   NET PNL   GROSS PNL   WIN RATE  TRADES    FEES           │
├─────────────────────────────────────────────────────────────┤
│  Best tx +$18.40  │  Worst tx -$12.60  │  Max DD -$84.20   │
├─────────────────────────────────────────────────────────────┤
│  CATEGORY TABLE (giống ảnh)                                 │
├─────────────────────────────────────────────────────────────┤
│  PNL BARS (progress bars)                                   │
├─────────────────────────────────────────────────────────────┤
│  [Start] [Stop] [Pause]  │  Config Panel                   │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ THAM SỐ CỐ ĐỊNH

```yaml
max_leverage: 3
max_position_pct: 0.05
max_drawdown_pct: 0.10
daily_loss_limit_pct: 0.05
min_edge_pct: 0.015
partial_close_ratio: 0.5

markets:
  - BTC/USD UP-DOWN 5min
  - BTC/USD UP-DOWN 15min

strategy:
  - momentum_v3
  - vol_filter
  - rsi_14
```

---

## 🔥 ƯU TIÊN CODE

### Phase 1: Backend Core
```python
# risk_manager.py
class RiskManager:
    def calculate_position_size(self, account_balance, win_rate, avg_win, avg_loss, confidence_score):
        """Half Kelly Criterion, cap at 5%"""
        pass
    
    def calculate_stop_loss(self, entry_price, direction, atr_1h):
        """1.5x ATR trailing stop"""
        pass
    
    def check_circuit_breakers(self, daily_pnl_pct, total_drawdown_pct, consecutive_losses):
        """Return should_stop_trading: bool"""
        pass

# FastAPI endpoints
@app.get("/api/status")
@app.get("/api/performance")
@app.get("/api/trades")
@app.websocket("/ws/live")
```

### Phase 2: Frontend Dashboard
```tsx
// components/PerformanceCards.tsx
const PerformanceCards = ({ data }) => (
  <div className="grid grid-cols-6 gap-4">
    <Card label="NET PNL" value={data.netPnl} color="green" />
    <Card label="GROSS PNL" value={data.grossPnl} color="green" />
    <Card label="WIN RATE" value={data.winRate} color="blue" suffix="%" />
    <Card label="TRADES" value={data.trades} />
    <Card label="FEES PAID" value={data.fees} color="red" />
    <Card label="AVG NET/TX" value={data.avgNet} color="green" />
  </div>
);

// Real-time WebSocket
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/live');
  ws.onmessage = (event) => setData(JSON.parse(event.data));
}, []);
```

---

## 🧪 TEST YÊU CẦU

- Unit test cho RiskManager
- API integration tests
- WebSocket connection test
- UI component tests (React Testing Library)

---

## 📝 LƯU Ý QUAN TRỌNG

1. **UI PHẢI GIỐNG ẢNH MẪU** - Dark theme, monospace font, card layout
2. **ĐỪNG thay đổi strategy gốc** (momentum_v3 + vol_filter + rsi_14)
3. **Real-time updates** via WebSocket, delay < 1s
4. **Responsive** - phải xem được trên mobile
5. **Type hints** cho Python, TypeScript cho React
6. **Error handling** robust

---

## 🔐 BẢO MẬT

- Private key đọc từ `.env`
- WebSocket auth (JWT)
- Rate limiting

---

## ✅ ĐỊNH NGHĨA "DONE"

- [ ] `docker-compose up` chạy được ngay
- [ ] Dashboard hiển thị giống ảnh mẫu 90%+
- [ ] Real-time updates hoạt động
- [ ] Controls (start/stop/pause) hoạt động
- [ ] Backend bot chạy được không lỗi
- [ ] README.md đầy đủ

---

## 📎 FILE ĐÍNH KÈM

- `plan.md` - Chi tiết đầy đủ specs
- Ảnh mẫu UI - Tham khảo visual design

---

**Code ngay giúp tôi, tôi cần deploy trong tuần này! UI phải đẹp như ảnh mẫu!**
