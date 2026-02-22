import os
import asyncio
import time
import datetime
import logging
import hashlib
import secrets
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import jwt
from jwt.exceptions import InvalidTokenError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import core modules
try:
    from .websocket import manager
    from core.polymarket_client import PolymarketClient
    from live_paper_trade import PaperTrader
    from core.database import Database
except ImportError as e:
    logger.warning(f"First import attempt failed: {e}")
    from websocket import manager
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.polymarket_client import PolymarketClient
    from live_paper_trade import PaperTrader
    from core.database import Database
    logger.info("Second import attempt succeeded")

logger.info(f"Module loaded successfully. Database: {Database}, PaperTrader: {PaperTrader}")

# ============================================================================
# Configuration
# ============================================================================

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# API Key Configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize components
db = Database()
poly_client = PolymarketClient()
paper_trader = PaperTrader(db=db)

start_time = time.time()

# Mocked state for the bot
current_status = {
    "status": "LIVE",
    "boot_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+7"),
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

# ============================================================================
# Pydantic Models
# ============================================================================

class StartCmd(BaseModel):
    """Model for start bot command"""
    mode: str = Field(default="demo", pattern="^(demo|live)$")

    @validator('mode')
    def mode_must_be_valid(cls, v):
        if v.lower() not in ['demo', 'live']:
            raise ValueError('mode must be either "demo" or "live"')
        return v.lower()


class LoginRequest(BaseModel):
    """Model for login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Model for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TradeHistoryParams(BaseModel):
    """Model for trade history query parameters"""
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    status: Optional[str] = Field(default=None, pattern="^(OPEN|CLOSED)$")


class DateRangeParams(BaseModel):
    """Model for date range query"""
    start_date: datetime.datetime
    end_date: datetime.datetime

    @validator('end_date')
    def end_date_must_be_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class TradeResponse(BaseModel):
    """Model for trade response"""
    id: int
    market: str
    direction: str
    size: float
    entry_price: float
    exit_price: Optional[float]
    fee_paid: float
    gross_pnl: float
    net_pnl: float
    status: str
    close_reason: Optional[str]
    open_time: str
    close_time: Optional[str]


class StatsResponse(BaseModel):
    """Model for trading statistics"""
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    gross_profit: float
    total_fees: float
    avg_pnl: float
    max_pnl: float
    min_pnl: float


class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


# ============================================================================
# Authentication
# ============================================================================

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Verify JWT token and return payload"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> dict:
    """Verify API key and return permissions"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Hash the API key for comparison
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_data = db.validate_api_key(key_hash)

    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    return key_data


def require_write_permission(api_key_data: dict = Depends(verify_api_key)) -> dict:
    """Require write permission for API key"""
    if api_key_data.get('permissions') not in ['write', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required",
        )
    return api_key_data


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    route_count = len([r for r in app.routes if hasattr(r, 'path')])
    logger.info(f"Starting up Poly-bot API with {route_count} routes...")
    route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
    for path in sorted(route_paths):
        logger.info(f"  Server route: {path}")
    asyncio.create_task(live_update_broadcaster())
    yield
    # Shutdown
    logger.info("Shutting down Poly-bot API...")


app = FastAPI(
    title="Poly-bot API",
    description="API for Poly-bot automated trading system",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )


# ============================================================================
# Public Endpoints
# ============================================================================

@app.get("/_debug/routes", tags=["Debug"])
def debug_routes():
    """Debug endpoint to see all registered routes"""
    return {
        "total_routes": len(app.routes),
        "routes": [r.path for r in app.routes if hasattr(r, 'path')]
    }

@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint - API health check"""
    return {
        "message": "Poly-bot API is running",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.get("/api/status", tags=["Status"])
def get_status(api_key: dict = Depends(verify_api_key)):
    """Get current bot status - requires API key"""
    try:
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

        # Add open position info if available
        open_pos = paper_trader.get_open_position_info()
        if open_pos:
            current_status["open_position"] = open_pos

        return current_status
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve status"
        )


@app.get("/api/performance", tags=["Performance"])
def get_performance(api_key: dict = Depends(verify_api_key)):
    """Get performance statistics - requires API key"""
    try:
        # Get stats from paper trader
        trader_stats = paper_trader.get_stats()

        # Get stats from database
        db_stats = db.get_trade_stats()

        # Merge stats
        performance_stats.update({
            "netPnl": db_stats['total_pnl'],
            "grossPnl": db_stats['gross_profit'],
            "winRate": db_stats['win_rate'],
            "trades": db_stats['total_trades'],
            "fees": db_stats['total_fees'],
            "avgNet": db_stats['avg_pnl'],
            "wins": db_stats['wins'],
            "losses": db_stats['losses']
        })

        return performance_stats
    except Exception as e:
        logger.error(f"Error getting performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance data"
        )


# ============================================================================
# Authentication Endpoints
# ============================================================================

logger.info(f"About to register auth routes. Current routes: {len(app.routes)}")

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(credentials: LoginRequest):
    """
    Login to get JWT access token.

    **Note**: In production, use proper user authentication (e.g., database lookup)
    """
    # TODO: Replace with proper user authentication
    # For demo purposes, accept any username/password combination
    # In production, verify against database

    if credentials.username and credentials.password:
        access_token_expires = datetime.timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": credentials.username, "role": "user"},
            expires_delta=access_token_expires
        )

        logger.info(f"User '{credentials.username}' logged in successfully")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@app.post("/api/auth/apikey", tags=["Authentication"])
def create_api_key(
    name: str,
    permissions: str = "read",
    token_payload: dict = Depends(verify_token)
):
    """
    Create a new API key - requires JWT authentication.

    - **name**: Name for the API key
    - **permissions**: "read" or "write"
    """
    if permissions not in ['read', 'write']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="permissions must be 'read' or 'write'"
        )

    # Generate a new API key
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Store in database
    key_id = db.add_api_key(key_hash, name, permissions)

    logger.info(f"Created new API key '{name}' with {permissions} permissions")

    return {
        "api_key": api_key,
        "name": name,
        "permissions": permissions,
        "id": key_id,
        "warning": "Store this API key securely - it will not be shown again"
    }

logger.info("Auth routes registered successfully")

# ============================================================================
# Protected Bot Control Endpoints (JWT Required)
# ============================================================================

@app.post("/api/bot/start", tags=["Bot Control"])
def start_bot(
    cmd: StartCmd,
    token_payload: dict = Depends(verify_token)
):
    """Start the trading bot - requires JWT authentication"""
    try:
        current_status["status"] = "LIVE"
        current_status["mode"] = cmd.mode.upper()

        logger.info(f"Bot started in {cmd.mode.upper()} mode by user '{token_payload.get('sub')}'")

        return {
            "message": f"Bot started in {cmd.mode.upper()} mode",
            "status": current_status["status"],
            "mode": current_status["mode"]
        }
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bot"
        )


@app.post("/api/bot/stop", tags=["Bot Control"])
def stop_bot(token_payload: dict = Depends(verify_token)):
    """Stop the trading bot - requires JWT authentication"""
    try:
        current_status["status"] = "OFFLINE"

        logger.info(f"Bot stopped by user '{token_payload.get('sub')}'")

        return {
            "message": "Bot stopped",
            "status": current_status["status"]
        }
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop bot"
        )


@app.post("/api/bot/pause", tags=["Bot Control"])
def pause_bot(token_payload: dict = Depends(verify_token)):
    """Pause the trading bot - requires JWT authentication"""
    try:
        current_status["status"] = "PAUSED"

        logger.info(f"Bot paused by user '{token_payload.get('sub')}'")

        return {
            "message": "Bot paused",
            "status": current_status["status"]
        }
    except Exception as e:
        logger.error(f"Error pausing bot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause bot"
        )


# ============================================================================
# Trade History Endpoints (API Key Required)
# ============================================================================

@app.get("/api/trades", response_model=List[TradeResponse], tags=["Trades"])
def get_trades(
    params: TradeHistoryParams = Depends(),
    api_key: dict = Depends(verify_api_key)
):
    """Get trade history with pagination - requires API key"""
    try:
        if params.status == "OPEN":
            trades = db.get_open_trades()
        elif params.status == "CLOSED":
            trades = db.get_closed_trades(limit=params.limit, offset=params.offset)
        else:
            trades = db.get_all_trades(limit=params.limit, offset=params.offset)

        return trades
    except Exception as e:
        logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trades"
        )


@app.get("/api/trades/{trade_id}", response_model=TradeResponse, tags=["Trades"])
def get_trade_by_id(
    trade_id: int,
    api_key: dict = Depends(verify_api_key)
):
    """Get a specific trade by ID - requires API key"""
    try:
        trade = db.get_trade_by_id(trade_id)
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trade with ID {trade_id} not found"
            )
        return trade
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade {trade_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trade"
        )


@app.get("/api/trades/stats", response_model=StatsResponse, tags=["Trades"])
def get_trade_stats(api_key: dict = Depends(verify_api_key)):
    """Get trading statistics - requires API key"""
    try:
        stats = db.get_trade_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting trade stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trade statistics"
        )


@app.post("/api/trades/range", response_model=List[TradeResponse], tags=["Trades"])
def get_trades_by_date_range(
    params: DateRangeParams,
    api_key: dict = Depends(verify_api_key)
):
    """Get trades within a date range - requires API key"""
    try:
        trades = db.get_trades_by_date_range(params.start_date, params.end_date)
        return trades
    except Exception as e:
        logger.error(f"Error getting trades by date range: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trades"
        )


@app.get("/api/position", tags=["Position"])
def get_open_position(api_key: dict = Depends(verify_api_key)):
    """Get current open position - requires API key"""
    try:
        position = paper_trader.get_open_position_info()

        if not position:
            return {
                "has_open_position": False,
                "message": "No open position"
            }

        # Get current market price for unrealized PnL calculation
        current_price = poly_client.get_market_price(paper_trader.market_token_id)

        # Calculate unrealized PnL
        shares = position['size'] / position['entry_price']
        unrealized_pnl = (current_price - position['entry_price']) * shares

        return {
            "has_open_position": True,
            "position": position,
            "current_price": current_price,
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round((unrealized_pnl / position['size']) * 100, 2) if position['size'] > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting open position: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve open position"
        )


@app.get("/api/stats", response_model=StatsResponse, tags=["Stats"])
def get_stats(api_key: dict = Depends(verify_api_key)):
    """Get trading statistics (alias for /api/trades/stats) - requires API key"""
    try:
        stats = db.get_trade_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live updates"""
    await manager.connect(websocket)
    logger.info(f"WebSocket client connected: {websocket.client}")
    try:
        while True:
            # Wait for a message (or just keep connection open)
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


# Background task to send live updates
async def live_update_broadcaster():
    """Background task to broadcast live updates via WebSocket"""
    while True:
        try:
            await asyncio.sleep(5)  # Give it 5s per cycle
            logger.debug("Broadcaster tick...")

            # Update demo logic
            if current_status["status"] == "LIVE" and current_status.get("mode") == "DEMO":
                await asyncio.to_thread(paper_trader.run_cycle)
                logger.debug(f"Paper trader cycle finished. Trades: {len(paper_trader.trade_history)}")

                # Sync stats
                trader_stats = paper_trader.get_stats()
                performance_stats["trades"] = trader_stats['total_trades']
                performance_stats["netPnl"] = trader_stats['net_pnl']
                performance_stats["winRate"] = round(trader_stats['win_rate'], 1)
                performance_stats["avgNet"] = round(trader_stats['net_pnl'] / max(trader_stats['total_trades'], 1), 2)
                performance_stats["grossPnl"] = trader_stats['gross_pnl']
                performance_stats["fees"] = trader_stats['total_fees']

            # Update current status with real data before broadcast
            try:
                wallet_addr = poly_client.wallet_address
                short_wallet = f"{wallet_addr[:6]}...{wallet_addr[-4:]}" if len(wallet_addr) > 20 else wallet_addr
                current_status["wallet"] = short_wallet
                current_status["demo_balance"] = f"${paper_trader.balance:,.2f}"
                current_status["live_balance"] = f"${poly_client.get_wallet_balance():,.2f}"

                uptime_sec = int(time.time() - start_time)
                hours, remainder = divmod(uptime_sec, 3600)
                minutes, seconds = divmod(remainder, 60)
                current_status["uptime"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                if current_status.get("mode") == "DEMO":
                    current_status["balance"] = current_status["demo_balance"]
                else:
                    current_status["balance"] = current_status["live_balance"]

                # Add open position info
                open_pos = paper_trader.get_open_position_info()
                if open_pos:
                    current_status["open_position"] = open_pos
            except Exception as e:
                logger.error(f"Error updating status for broadcast: {e}")

            # Broadcast live updates
            await manager.broadcast({
                "type": "tick",
                "timestamp": datetime.datetime.now().isoformat(),
                "performance": performance_stats,
                "status": current_status
            })
            logger.debug("Broadcasted tick to clients.")
        except Exception as e:
            logger.error("=== BROADCASTER CRASHED ===", exc_info=True)
            await asyncio.sleep(5)


# Log all registered routes at module load time
route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
logger.info(f"MODULE LOAD COMPLETE - Total routes registered: {len(route_paths)}")
for path in sorted(route_paths):
    logger.info(f"  Route: {path}")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Poly-bot API server...")
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
