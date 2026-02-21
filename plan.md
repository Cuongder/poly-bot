# Polymarket BTC UP/DOWN Bot - Optimization Project with Web Dashboard

## 📋 TỔNG QUAN DỰ ÁN

Bot giao dịch UP/DOWN BTC trên Polymarket (Polygon Mainnet) với chiến lược hedge 2 đầu (mua cả UP và DOWN) trên 2 khung thờ gian 5m và 15m.

**Mục tiêu:** Tối ưu risk management, giảm drawdown, tăng risk-adjusted returns, **và có web dashboard trực quan giống ảnh mẫu**.

---

## 🖥️ WEB DASHBOARD (FEATURE MỚI)

### UI/UX Requirements
- **Dark theme** giống ảnh mẫu (đen/xanh lá/xanh dương)
- **Real-time updates** via WebSocket
- **Responsive design** (desktop + mobile)
- **Tech stack:** React/Next.js hoặc Python Flask + TailwindCSS

### Dashboard Sections (theo ảnh mẫu)

#### 1. Header Bar
```
[Logo] OpenClaw ─── polymarket-bot ─── zsh ─── 120x45         [LIVE] 17:31:36
```
- Status indicator (LIVE/OFFLINE/Paused)
- Current time
- Terminal-style header

#### 2. System Info Panel
```
┌─ OpenClaw booted at 2026-02-19 14:52:07 UTC+7
├─ Wallet 0x3fA9...c82E • Polymarket account verified ✓
├─ Network Polygon Mainnet • chain_id=137 • gas ok
├─ Markets BTC/USD UP-DOWN 5min, BTC/USD UP-DOWN 15min
├─ Strategy momentum_v3 + vol_filter + rsi_14
├─ Risk/trade max $20.00 • stop-loss on • auto-compound on
└─ Session up 00:00:29
```
- Wallet connection status
- Network status with gas indicator
- Active markets (5m, 15m)
- Strategy đang chạy
- Risk parameters
- Session uptime counter

#### 3. Performance Summary Cards
| Card | Display |
|------|---------|
| NET PNL | +$612.40 (green, after fees) |
| GROSS PNL | +$738.90 (green, before fees) |
| WIN RATE | 60.2% (blue, 301W/199L) |
| TRADES | 500 confirmed txs |
| FEES PAID | -$126.50 (red, $0.253 avg/tx) |
| AVG NET/TX | +$1.22 (green, gross $1.48) |

#### 4. Trade Statistics
```
Best tx  +$18.40 BTC 5min ▲ UP [tx #447]
Worst tx -$12.60 BTC 15min ▼ DN [tx #312]
Best streak 13W (tx #388-400)  Worst streak: 7L (tx #305-311)
Max drawdown -$84.20 at tx #312 • recovered at tx #341
```

#### 5. Category Breakdown Table
| MARKET | DIR | TRADES | W/L | WIN% | GROSS PNL | FEES | NET PNL |
|--------|-----|--------|-----|------|-----------|------|---------|
| BTC 5min ★ | ▲ UP | 148 | 98W/50L | 66.2% | +$268.40 | -$37.00 | +$231.40 |
| BTC 5min ★ | ▼ DN | 112 | 74W/38L | 66.1% | +$210.20 | -$28.00 | +$182.20 |
| BTC 15min | ▲ UP | 129 | 70W/59L | 54.3% | +$156.80 | -$32.25 | +$124.55 |
| BTC 15min | ▼ DN | 111 | 59W/52L | 53.2% | +$103.50 | -$29.25 | +$74.25 |
| TOTAL | - | 500 | 301W/199L | 60.2% | +$738.90 | -$126.50 | +$612.40 |

#### 6. Net PNL by Category (Progress Bars)
```
BTC 5min ▲ UP  [████████████░░░░░░░░] +$231.40
BTC 5min ▼ DN  [████████░░░░░░░░░░░░] +$182.20
BTC 15min ▲ UP [██████░░░░░░░░░░░░░░] +$124.55
BTC 15min ▼ DN [████░░░░░░░░░░░░░░░░] +$74.25
```

#### 7. Real-time Charts (Bonus)
- Equity curve (PNL over time)
- Win rate rolling 30-day
- Drawdown chart
- Volume by market

#### 8. Controls Panel
- [Start Bot] [Stop Bot] [Pause]
- Emergency Stop (circuit breaker)
- Adjust risk parameters (sliders)
- Toggle auto-compound
- Export data (CSV/JSON)

---

## 🎯 YÊU CẦU CHỨC NĂNG BACKEND

### 1. Risk Management Module
- **Position Sizing:** Kelly Criterion động (Half Kelly, max 5% account/trade)
- **Leverage Control:** Auto-adjust leverage 1x-3x dựa trên volatility (ATR)
- **Max Drawdown Protection:** Circuit breaker dừng bot khi hit -10% account

### 2. Multi-Timeframe Correlation Filter
- Check đồng thuận giữa 5m và 15m
- Tăng position size khi cả 2 khung confirm (score > 0.7)
- Giảm size hoặc skip khi contradict (score < 0.3)

### 3. Fee Optimizer
- Batch multiple DCA orders into 1-2 orders
- Minimum edge threshold: 1.5% (after fees)
- Consolidate small positions before closing

### 4. Session Filter
- Skip trading khi funding rate > 0.01%
- Avoid 00:00 UTC (daily close) ± 15 minutes
- Skip khi volatility quá cao (ATR > 2x average)

### 5. Dynamic Stop Loss / Take Profit
- Trailing stop: 1.5x ATR(14) của khung 1H
- Take profit: 2:1 R:R minimum
- Partial close at 1:1 R:R (50% position)

---

## 🔧 KỸ THUẬT YÊU CẦU

### Tech Stack
- **Backend:** Python 3.10+ (FastAPI)
- **Frontend:** React/Next.js hoặc Flask + TailwindCSS
- **Real-time:** WebSocket hoặc Server-Sent Events
- **Database:** SQLite/PostgreSQL cho trade history
- **Blockchain:** Polygon Mainnet (chain_id=137)
- **API:** Polymarket API, Covalent/Alchemy cho on-chain data
- **Indicators:** ta-lib hoặc pandas-ta

### Cấu trúc thư mục
```
polymarket_bot/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI entry
│   │   ├── websocket.py       # Real-time updates
│   │   └── routes.py          # REST endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── risk_manager.py
│   │   ├── signal_generator.py
│   │   ├── correlation_analyzer.py
│   │   ├── fee_optimizer.py
│   │   ├── session_filter.py
│   │   ├── polymarket_client.py
│   │   └── database.py
│   ├── models/
│   │   ├── trade.py
│   │   └── performance.py
│   ├── config/
│   │   └── settings.yaml
│   └── requirements.txt
├── frontend/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── SystemInfo.tsx
│   │   ├── PerformanceCards.tsx
│   │   ├── TradeStats.tsx
│   │   ├── CategoryTable.tsx
│   │   ├── PnlBars.tsx
│   │   ├── Charts.tsx
│   │   └── Controls.tsx
│   ├── pages/
│   │   └── index.tsx
│   ├── styles/
│   │   └── globals.css
│   └── package.json
├── tests/
└── README.md
```

### API Endpoints
```python
# REST API
GET  /api/status              # Bot status, wallet, network
GET  /api/performance         # Performance summary
GET  /api/trades              # Trade history (paginated)
GET  /api/stats               # Detailed statistics
POST /api/bot/start           # Start bot
POST /api/bot/stop            # Stop bot
POST /api/bot/pause           # Pause bot
POST /api/config              # Update config

# WebSocket
WS   /ws/live                 # Real-time updates
```

---

## 📊 THÔNG SỐ RISK MANAGEMENT

```yaml
risk_management:
  max_position_size: 0.05      # 5% of account per trade
  max_leverage: 3              # Max 3x (not 7x)
  max_drawdown: 0.10           # Stop bot at -10%
  daily_loss_limit: 0.05       # Stop after -5% daily
  
  kelly_criterion:
    enabled: true
    fraction: 0.5              # Half Kelly
    min_edge: 0.015            # 1.5% minimum edge
    
  stop_loss:
    method: atr_trailing
    atr_period: 14
    atr_multiplier: 1.5
    timeframe: 1h              # Use 1H ATR
    
  take_profit:
    r_r_ratio: 2.0             # 2:1 minimum
    partial_close: true
    partial_at: 1.0            # Close 50% at 1:1
```

---

## 🧠 CHIẾN LƯỢC TÍN HIỆU (GIỮ NGUYÊN + TỐI ƯU)

### Current Strategy
- momentum_v3 (động lượng giá)
- vol_filter (lọc volume)
- rsi_14 (RSI 14 periods)

### Tối ưu thêm
1. **Trend Filter:** Chỉ trade khi EMA(20) > EMA(50) cho UP, ngược lại cho DOWN
2. **Volume Confirmation:** Volume phải > Volume SMA(20) * 1.2
3. **RSI Filter:** Không trade khi RSI 30-70 (neutral zone)

---

## ⏰ SESSION FILTER RULES

```python
SKIP_TRADING_WHEN:
  - funding_rate > 0.0001        # 0.01%
  - time_of_day == 00:00 ± 15min # Daily close
  - volatility_spike == True     # ATR > 2x avg
  - weekend_low_volume == True   # Saturday low liquidity
```

---

## 📈 CORRELATION SCORING

```python
def calculate_correlation_score(tf_5m_signal, tf_15m_signal):
    """
    Score 0-1, higher = more confident
    """
    if tf_5m_signal.direction == tf_15m_signal.direction:
        strength_diff = abs(tf_5m_signal.strength - tf_15m_signal.strength)
        if strength_diff < 0.2:  # Similar strength
            return 0.9
        else:
            return 0.7
    else:
        return 0.3  # Conflicting, reduce size or skip
```

---

## 💰 FEE OPTIMIZATION

```python
class FeeOptimizer:
    def __init__(self, avg_fee_per_trade=0.25):
        self.min_edge = 0.015  # 1.5%
        
    def should_enter(self, expected_pnl_pct):
        """Only enter if edge > fees + min_profit"""
        return expected_pnl_pct > (self.avg_fee_per_trade * 2 + self.min_edge)
    
    def batch_orders(self, pending_orders):
        """Combine small DCA orders into larger ones"""
        # Implementation here
        pass
```

---

## 🚨 CIRCUIT BREAKERS

```python
CIRCUIT_BREAKERS:
  daily_loss:
    threshold: -0.05           # -5%
    action: stop_trading
    
  max_drawdown:
    threshold: -0.10           # -10%
    action: stop_bot
    
  consecutive_losses:
    threshold: 5
    action: reduce_size_50%
    
  volatility_spike:
    condition: atr_current > atr_avg * 2
    action: pause_30min
```

---

## 📋 DELIVERABLES

### Phase 1: Backend Core (Week 1)
- [x] Risk Manager with Kelly Criterion
- [x] Signal Generator
- [x] Polymarket API integration
- [x] Database schema + trade logging
- [x] Circuit breakers
- [x] REST API endpoints

### Phase 2: Frontend Dashboard (Week 2)
- [x] React app setup with dark theme
- [x] Header + System Info panel
- [x] Performance Cards component
- [x] Trade Stats + Category Table
- [x] PNL Progress Bars
- [ ] Real-time WebSocket connection

### Phase 3: Polish & Testing (Week 3)
- [x] Charts (equity curve, drawdown)
- [x] Controls panel (start/stop/config)
- [x] Unit tests (80%+ coverage)
- [x] Backtest script
- [x] README.md hướng dẫn
- [x] Docker compose setup

---

## 🔐 BẢO MẬT

- Private key lưu trong file `.env`, không commit
- Sử dụng wallet mới (không dùng ví có nhiều tiền)
- Rate limiting API calls
- Log rotation để tránh fill disk
- WebSocket auth (JWT token)

---

## 📞 THÔNG TIN LIÊN HỆ

- Tác giả yêu cầu: Nhím
- Bot gốc: Polymarket UP/DOWN BTC 5m/15m
- Target platform: Polymarket trên Polygon
- Budget: Optimization + Web Dashboard
- UI Reference: Ảnh mẫu terminal-style dark theme

---

## ✅ ACCEPTANCE CRITERIA

### Backend
- [ ] Bot chạy ổn định 24h không crash
- [ ] Drawdown < 10% trong backtest 3 tháng
- [ ] Win rate >= 55% (chấp nhận giảm từ 60% nếu risk-adjusted returns tốt hơn)
- [ ] Sharpe ratio > 1.5
- [ ] Fee impact < 15% gross profit

### Frontend
- [ ] Dashboard hiển thị đúng giống ảnh mẫu
- [ ] Real-time updates < 1s delay
- [ ] Responsive trên mobile
- [ ] Controls hoạt động (start/stop/pause)
- [ ] Charts render không lag

### Integration
- [ ] Backend + Frontend kết nối seamless
- [ ] WebSocket không disconnect
- [ ] Docker compose up chạy được ngay
