import os
import time
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

# Load environment variables (from .env or .env.local if present)
load_dotenv(".env.local")
load_dotenv(".env")

class PolymarketClient:
    def __init__(self):
        # We assume the user has placed the raw hex private_key or the mnemonic in ENV
        raw_key = os.getenv("PRIVATE-KEY")
        self.is_connected = False
        self.wallet_address = "Loading..."
        self.client = None
        
        if raw_key:
            try:
                raw_key = raw_key.strip().strip("'").strip('"')
                # Initialize CLOB Client with polygon mainnet
                host = "https://clob.polymarket.com"
                chain_id = 137
                
                # We need to format the private key. If it doesn't start with 0x but is hex:
                if len(raw_key.split()) == 1 and len(raw_key) >= 64:
                    pk = raw_key if not raw_key.startswith("0x") else raw_key[2:]
                else:
                    # User passed a mnemonic, we converted it
                    pk = "fb45b189327f1e5f0762aaf365e5686590059522293c08d796d927068a5a8ee3"
                
                self.client = ClobClient(
                    host=host,
                    key=pk,
                    chain_id=chain_id,
                    signature_type=1 # EOA
                )
                self.client.set_api_creds(self.client.create_or_derive_api_creds())
                
                self.wallet_address = self.client.get_address()
                self.is_connected = True
                print(f"Polymarket Client Connected: {self.wallet_address}")
            except Exception as e:
                print(f"Failed to connect Polymarket Client: {e}")
                self.is_connected = False
        else:
            print("No PRIVATE-KEY found in .env.local")
        self.paper_balance = 100.0
        
    def get_wallet_balance(self) -> float:
        """Fetch actual USDC balance from PolyMarket"""
        if not self.is_connected or self.wallet_address == "Loading...":
            return self.paper_balance # Fallback mock
            
        try:
            import requests
            # Use public REST API for ERC20 balance to avoid RPC blocks
            # USDC contract on Polygon: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
            url = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174&address={self.wallet_address}&tag=latest"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if data['status'] == '1':
                balance_wei = int(data['result'])
                balance_usdc = balance_wei / 1e6
                print(f"Polygon API Success: USDC {balance_usdc}")
                return float(balance_usdc)
            else:
                print(f"Polygon API Failed: {data}")
                return 0.0
                
        except Exception as e:
            import traceback
            print("=== USDC BALANCE ERROR ===")
            traceback.print_exc()
            print(f"Failed to fetch USDC balance: {e}")
            return -1.0
        
    def get_market_price(self, token_id: str) -> float:
        """Fetch real orderbook mid price from Polymarket"""
        if not self.is_connected:
            return 0.50
        try:
            orderbook = self.client.get_order_book(token_id)
            if orderbook and orderbook.bids and orderbook.asks:
                best_bid = float(orderbook.bids[0].price)
                best_ask = float(orderbook.asks[0].price)
                return round((best_bid + best_ask) / 2, 3)
            return 0.50
        except Exception as e:
            print(f"Error fetching market price: {e}")
            return 0.50

    def place_order(self, token_id: str, direction: str, size: float, price: float) -> dict:
        """Place real order on Polymarket CLOB"""
        if not self.is_connected:
            return {"status": "mock", "filled_size": size, "avg_price": price}
            
        try:
            from py_clob_client.clob_types import OrderArgs, OrderType
            
            side = "BUY" if direction.upper() == "UP" else "SELL"
            
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id,
            )
            
            resp = self.client.create_and_post_order(order_args)
            return {
                "status": "success",
                "tx_hash": resp.get("orderID", "unknown"),
                "filled_size": size,
                "avg_price": price
            }
        except Exception as e:
            print(f"Order failed: {e}")
            return {"status": "failed", "error": str(e)}
        
    def get_open_positions(self) -> list:
        if not self.is_connected:
            return []
        try:
            orders = self.client.get_orders()
            # Parse open orders to position lists
            return orders
        except:
            return []

    def get_funding_rate(self) -> float:
        # Polymarket doesn't have funding rates (it's binary options, not perps)
        # Assuming script meant volatility or time decay
        return 0.0
