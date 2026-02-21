from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import datetime
from .websocket import manager
from core.polymarket_client import PolymarketClient
from live_paper_trade import PaperTrader
from pydantic import BaseModel

class StartCmd(BaseModel):
    mode: str = "demo"

app = FastAPI(title="Poly-bot API")
poly_client = PolymarketClient()
paper_trader = PaperTrader()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()

# Mocked state for the bot
current_status = {
    "status": "LIVE",
    "boot_time": "2026-02-19 14:52:07 UTC+7",
    "wallet": "0x3fA9...c82E",
    "network": "Polygon Mainnet",
    "chain_id": 137,
    "strategy": "K-ATR | VolFilter | RSI",
    "markets": "BTC/USD UP-DOWN 5min, BTC/USD UP-DOWN 15min",
    "mode": "DEMO"
}

performance_stats = {
    "netPnl": 0.0,
    "grossPnl": 0.0,
    "winRate": 0.0,
    "trades": 0,
    "fees": 0.0,
    "avgNet": 0.0
}

@app.get("/")
def read_root():
    return {"message": "Poly-bot API is running"}

@app.get("/api/status")
def get_status():
    wallet_addr = poly_client.wallet_address
    short_wallet = f"{wallet_addr[:6]}...{wallet_addr[-4:]}" if len(wallet_addr) > 20 else wallet_addr
    
    current_status["wallet"] = short_wallet
    current_status["network"] = "Polygon Mainnet" if poly_client.is_connected else "Offline"
    
    # Calculate Uptime
    uptime_sec = int(time.time() - start_time)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    current_status["uptime"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Send both balances
    current_status["demo_balance"] = f"${paper_trader.balance:,.2f}"
    current_status["live_balance"] = f"${poly_client.get_wallet_balance():,.2f}"
    
    # Balance for backwards compat / main display
    if current_status.get("mode") == "DEMO":
        current_status["balance"] = current_status["demo_balance"]
    else:
        current_status["balance"] = current_status["live_balance"]
        
    return current_status

@app.get("/api/performance")
def get_performance():
    return performance_stats

@app.post("/api/bot/start")
def start_bot(cmd: StartCmd = StartCmd()):
    current_status["status"] = "LIVE"
    current_status["mode"] = cmd.mode.upper()
    return {"message": f"Bot started in {cmd.mode.upper()} mode"}

@app.post("/api/bot/stop")
def stop_bot():
    current_status["status"] = "OFFLINE"
    return {"message": "Bot stopped"}

@app.post("/api/bot/pause")
def pause_bot():
    current_status["status"] = "PAUSED"
    return {"message": "Bot paused"}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 1. Wait for a message (or just keep connection open)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to send live updates
async def live_update_broadcaster():
    import traceback
    while True:
        try:
            await asyncio.sleep(5) # Give it 5s per cycle so we don't spam Binance/Polygon API
            print("Broadcaster tick...", flush=True)
            # Update demo logic
            if current_status["status"] == "LIVE" and current_status.get("mode") == "DEMO":
                await asyncio.to_thread(paper_trader.run_cycle)
                print(f"Paper trader cycle finished. Trades: {len(paper_trader.trades)}", flush=True)
                
                # Sync stats
                trades_count = len(paper_trader.trades)
                if trades_count > 0:
                    performance_stats["trades"] = trades_count
                    performance_stats["netPnl"] = sum(t["net_pnl"] for t in paper_trader.trades)
                    performance_stats["winRate"] = round((paper_trader.wins / trades_count) * 100, 1)
                    performance_stats["avgNet"] = round(performance_stats["netPnl"] / trades_count, 2)
                    performance_stats["grossPnl"] = sum(t["net_pnl"] for t in paper_trader.trades if t["net_pnl"] > 0)
                    performance_stats["fees"] = sum(abs(t["net_pnl"] * 0.02) for t in paper_trader.trades) # Simplified fee mockup
            
            # Update current status with real data before broadcast
            updated_status = get_status()
            
            # Broadcast live updates
            await manager.broadcast({
                "type": "tick",
                "timestamp": datetime.datetime.now().isoformat(),
                "performance": performance_stats,
                "status": updated_status
            })
            print("Broadcasted tick to clients.", flush=True)
        except Exception as e:
            print("=== BROADCASTER CRASHED ===", flush=True)
            traceback.print_exc()
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(live_update_broadcaster())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
