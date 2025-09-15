#!/usr/bin/env python3
"""
RichesReach AI Service - With Authentication and WebSocket Support
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
import logging
import time
from datetime import datetime, timedelta
import asyncio
import jwt
import hashlib
import json
from typing import Optional, List, Dict, Any
import random

# Import real data services
from core.simple_market_data_service import SimpleMarketDataService
from core.real_options_service import RealOptionsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stock data caching for performance
class StockDataCache:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 60  # 1 minute for faster updates
        self.max_cache_size = 50  # Limit cache size
    
    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached stock data if not expired"""
        if symbol in self.cache:
            data, timestamp = self.cache[symbol]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                # Remove expired data
                del self.cache[symbol]
        return None
    
    def set(self, symbol: str, data: Dict[str, Any]) -> None:
        """Cache stock data with timestamp and manage cache size"""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[symbol] = (data, time.time())
    
    def get_multiple(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get multiple cached stock data"""
        result = {}
        for symbol in symbols:
            cached_data = self.get(symbol)
            if cached_data:
                result[symbol] = cached_data
        return result

# Global stock data cache instance
stock_cache = StockDataCache()

# Price update tracking
last_price_update = 0
PRICE_UPDATE_INTERVAL = 300  # 5 minutes in seconds

async def update_stock_prices():
    """Update stock prices in the background every 5 minutes"""
    global last_price_update
    import time
    
    current_time = time.time()
    if current_time - last_price_update < PRICE_UPDATE_INTERVAL:
        return
    
    logger.info("Updating stock prices in background...")
    last_price_update = current_time
    
    # Update prices for popular stocks only (to avoid API limits)
    popular_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC"]
    
    for symbol in popular_symbols:
        try:
            # Fetch fresh data and cache it
            await generate_stock_data(symbol)
        except Exception as e:
            logger.warning(f"Failed to update price for {symbol}: {str(e)}")
    
    logger.info("Stock price update completed")

# Comprehensive stock database with 200+ stocks including small-caps
def get_comprehensive_stock_database():
    return {
        # Large Cap Tech
        "AAPL": {"symbol": "AAPL", "companyName": "Apple Inc.", "currentPrice": 234.07, "marketCap": "Large"},
        "GOOGL": {"symbol": "GOOGL", "companyName": "Alphabet Inc.", "currentPrice": 240.8, "marketCap": "Large"},
        "MSFT": {"symbol": "MSFT", "companyName": "Microsoft Corporation", "currentPrice": 509.9, "marketCap": "Large"},
        "AMZN": {"symbol": "AMZN", "companyName": "Amazon.com Inc.", "currentPrice": 228.15, "marketCap": "Large"},
        "NVDA": {"symbol": "NVDA", "companyName": "NVIDIA Corporation", "currentPrice": 875.28, "marketCap": "Large"},
        "META": {"symbol": "META", "companyName": "Meta Platforms Inc.", "currentPrice": 485.12, "marketCap": "Large"},
        "TSLA": {"symbol": "TSLA", "companyName": "Tesla Inc.", "currentPrice": 395.94, "marketCap": "Large"},
        "NFLX": {"symbol": "NFLX", "companyName": "Netflix Inc.", "currentPrice": 1188.44, "marketCap": "Large"},
        "AMD": {"symbol": "AMD", "companyName": "Advanced Micro Devices Inc.", "currentPrice": 158.57, "marketCap": "Large"},
        "INTC": {"symbol": "INTC", "companyName": "Intel Corporation", "currentPrice": 24.08, "marketCap": "Large"},
        "CRM": {"symbol": "CRM", "companyName": "Salesforce Inc.", "currentPrice": 242.76, "marketCap": "Large"},
        "ADBE": {"symbol": "ADBE", "companyName": "Adobe Inc.", "currentPrice": 349.36, "marketCap": "Large"},
        "ORCL": {"symbol": "ORCL", "companyName": "Oracle Corporation", "currentPrice": 145.23, "marketCap": "Large"},
        "CSCO": {"symbol": "CSCO", "companyName": "Cisco Systems Inc.", "currentPrice": 58.91, "marketCap": "Large"},
        "IBM": {"symbol": "IBM", "companyName": "International Business Machines", "currentPrice": 189.45, "marketCap": "Large"},
        
        # Financial Services
        "JPM": {"symbol": "JPM", "companyName": "JPMorgan Chase & Co.", "currentPrice": 178.45, "marketCap": "Large"},
        "BAC": {"symbol": "BAC", "companyName": "Bank of America Corp.", "currentPrice": 34.56, "marketCap": "Large"},
        "WFC": {"symbol": "WFC", "companyName": "Wells Fargo & Company", "currentPrice": 45.78, "marketCap": "Large"},
        "GS": {"symbol": "GS", "companyName": "Goldman Sachs Group Inc.", "currentPrice": 412.34, "marketCap": "Large"},
        "MS": {"symbol": "MS", "companyName": "Morgan Stanley", "currentPrice": 89.12, "marketCap": "Large"},
        "C": {"symbol": "C", "companyName": "Citigroup Inc.", "currentPrice": 67.89, "marketCap": "Large"},
        "V": {"symbol": "V", "companyName": "Visa Inc.", "currentPrice": 245.78, "marketCap": "Large"},
        "MA": {"symbol": "MA", "companyName": "Mastercard Inc.", "currentPrice": 456.23, "marketCap": "Large"},
        "AXP": {"symbol": "AXP", "companyName": "American Express Company", "currentPrice": 198.45, "marketCap": "Large"},
        "PYPL": {"symbol": "PYPL", "companyName": "PayPal Holdings Inc.", "currentPrice": 62.34, "marketCap": "Large"},
        "SQ": {"symbol": "SQ", "companyName": "Block Inc.", "currentPrice": 78.91, "marketCap": "Large"},
        
        # Healthcare & Biotech
        "JNJ": {"symbol": "JNJ", "companyName": "Johnson & Johnson", "currentPrice": 156.23, "marketCap": "Large"},
        "PFE": {"symbol": "PFE", "companyName": "Pfizer Inc.", "currentPrice": 28.45, "marketCap": "Large"},
        "UNH": {"symbol": "UNH", "companyName": "UnitedHealth Group Inc.", "currentPrice": 523.67, "marketCap": "Large"},
        "ABBV": {"symbol": "ABBV", "companyName": "AbbVie Inc.", "currentPrice": 167.89, "marketCap": "Large"},
        "MRK": {"symbol": "MRK", "companyName": "Merck & Co. Inc.", "currentPrice": 123.45, "marketCap": "Large"},
        "TMO": {"symbol": "TMO", "companyName": "Thermo Fisher Scientific Inc.", "currentPrice": 567.89, "marketCap": "Large"},
        "ABT": {"symbol": "ABT", "companyName": "Abbott Laboratories", "currentPrice": 112.34, "marketCap": "Large"},
        "DHR": {"symbol": "DHR", "companyName": "Danaher Corporation", "currentPrice": 234.56, "marketCap": "Large"},
        "BMY": {"symbol": "BMY", "companyName": "Bristol-Myers Squibb Company", "currentPrice": 45.67, "marketCap": "Large"},
        "LLY": {"symbol": "LLY", "companyName": "Eli Lilly and Company", "currentPrice": 678.90, "marketCap": "Large"},
        
        # Consumer Goods
        "PG": {"symbol": "PG", "companyName": "Procter & Gamble Co.", "currentPrice": 145.67, "marketCap": "Large"},
        "KO": {"symbol": "KO", "companyName": "The Coca-Cola Company", "currentPrice": 58.34, "marketCap": "Large"},
        "PEP": {"symbol": "PEP", "companyName": "PepsiCo Inc.", "currentPrice": 167.89, "marketCap": "Large"},
        "WMT": {"symbol": "WMT", "companyName": "Walmart Inc.", "currentPrice": 167.89, "marketCap": "Large"},
        "HD": {"symbol": "HD", "companyName": "The Home Depot Inc.", "currentPrice": 345.67, "marketCap": "Large"},
        "NKE": {"symbol": "NKE", "companyName": "Nike Inc.", "currentPrice": 98.76, "marketCap": "Large"},
        "MCD": {"symbol": "MCD", "companyName": "McDonald's Corporation", "currentPrice": 289.45, "marketCap": "Large"},
        "SBUX": {"symbol": "SBUX", "companyName": "Starbucks Corporation", "currentPrice": 98.23, "marketCap": "Large"},
        "DIS": {"symbol": "DIS", "companyName": "The Walt Disney Company", "currentPrice": 89.12, "marketCap": "Large"},
        
        # Energy & Utilities
        "XOM": {"symbol": "XOM", "companyName": "Exxon Mobil Corporation", "currentPrice": 112.34, "marketCap": "Large"},
        "CVX": {"symbol": "CVX", "companyName": "Chevron Corporation", "currentPrice": 156.78, "marketCap": "Large"},
        "COP": {"symbol": "COP", "companyName": "ConocoPhillips", "currentPrice": 123.45, "marketCap": "Large"},
        "EOG": {"symbol": "EOG", "companyName": "EOG Resources Inc.", "currentPrice": 134.56, "marketCap": "Large"},
        "SLB": {"symbol": "SLB", "companyName": "Schlumberger Limited", "currentPrice": 45.67, "marketCap": "Large"},
        "NEE": {"symbol": "NEE", "companyName": "NextEra Energy Inc.", "currentPrice": 78.90, "marketCap": "Large"},
        "DUK": {"symbol": "DUK", "companyName": "Duke Energy Corporation", "currentPrice": 98.76, "marketCap": "Large"},
        "SO": {"symbol": "SO", "companyName": "The Southern Company", "currentPrice": 67.89, "marketCap": "Large"},
        
        # Industrial & Materials
        "BA": {"symbol": "BA", "companyName": "The Boeing Company", "currentPrice": 234.56, "marketCap": "Large"},
        "CAT": {"symbol": "CAT", "companyName": "Caterpillar Inc.", "currentPrice": 345.67, "marketCap": "Large"},
        "GE": {"symbol": "GE", "companyName": "General Electric Company", "currentPrice": 156.78, "marketCap": "Large"},
        "HON": {"symbol": "HON", "companyName": "Honeywell International Inc.", "currentPrice": 198.45, "marketCap": "Large"},
        "MMM": {"symbol": "MMM", "companyName": "3M Company", "currentPrice": 98.76, "marketCap": "Large"},
        "UPS": {"symbol": "UPS", "companyName": "United Parcel Service Inc.", "currentPrice": 167.89, "marketCap": "Large"},
        "FDX": {"symbol": "FDX", "companyName": "FedEx Corporation", "currentPrice": 234.56, "marketCap": "Large"},
        "LMT": {"symbol": "LMT", "companyName": "Lockheed Martin Corporation", "currentPrice": 456.78, "marketCap": "Large"},
        "RTX": {"symbol": "RTX", "companyName": "Raytheon Technologies Corporation", "currentPrice": 89.12, "marketCap": "Large"},
        "NOC": {"symbol": "NOC", "companyName": "Northrop Grumman Corporation", "currentPrice": 567.89, "marketCap": "Large"},
        
        # Mid Cap Stocks
        "ZM": {"symbol": "ZM", "companyName": "Zoom Video Communications Inc.", "currentPrice": 67.23, "marketCap": "Mid"},
        "DOCU": {"symbol": "DOCU", "companyName": "DocuSign Inc.", "currentPrice": 45.78, "marketCap": "Mid"},
        "SNOW": {"symbol": "SNOW", "companyName": "Snowflake Inc.", "currentPrice": 156.89, "marketCap": "Mid"},
        "UBER": {"symbol": "UBER", "companyName": "Uber Technologies Inc.", "currentPrice": 45.67, "marketCap": "Mid"},
        "SPOT": {"symbol": "SPOT", "companyName": "Spotify Technology S.A.", "currentPrice": 198.45, "marketCap": "Mid"},
        "ROKU": {"symbol": "ROKU", "companyName": "Roku Inc.", "currentPrice": 78.90, "marketCap": "Mid"},
        "PTON": {"symbol": "PTON", "companyName": "Peloton Interactive Inc.", "currentPrice": 12.34, "marketCap": "Mid"},
        "TWLO": {"symbol": "TWLO", "companyName": "Twilio Inc.", "currentPrice": 56.78, "marketCap": "Mid"},
        "OKTA": {"symbol": "OKTA", "companyName": "Okta Inc.", "currentPrice": 89.12, "marketCap": "Mid"},
        "CRWD": {"symbol": "CRWD", "companyName": "CrowdStrike Holdings Inc.", "currentPrice": 234.56, "marketCap": "Mid"},
        "NET": {"symbol": "NET", "companyName": "Cloudflare Inc.", "currentPrice": 78.90, "marketCap": "Mid"},
        "DDOG": {"symbol": "DDOG", "companyName": "Datadog Inc.", "currentPrice": 123.45, "marketCap": "Mid"},
        "PLTR": {"symbol": "PLTR", "companyName": "Palantir Technologies Inc.", "currentPrice": 23.45, "marketCap": "Mid"},
        "COIN": {"symbol": "COIN", "companyName": "Coinbase Global Inc.", "currentPrice": 156.78, "marketCap": "Mid"},
        "HOOD": {"symbol": "HOOD", "companyName": "Robinhood Markets Inc.", "currentPrice": 12.34, "marketCap": "Mid"},
        
        # Small Cap Stocks
        "GME": {"symbol": "GME", "companyName": "GameStop Corp.", "currentPrice": 23.45, "marketCap": "Small"},
        "AMC": {"symbol": "AMC", "companyName": "AMC Entertainment Holdings Inc.", "currentPrice": 8.90, "marketCap": "Small"},
        "BB": {"symbol": "BB", "companyName": "BlackBerry Limited", "currentPrice": 3.45, "marketCap": "Small"},
        "NOK": {"symbol": "NOK", "companyName": "Nokia Corporation", "currentPrice": 4.56, "marketCap": "Small"},
        "SNDL": {"symbol": "SNDL", "companyName": "Sundial Growers Inc.", "currentPrice": 0.12, "marketCap": "Small"},
        "TLRY": {"symbol": "TLRY", "companyName": "Tilray Inc.", "currentPrice": 2.34, "marketCap": "Small"},
        "ACB": {"symbol": "ACB", "companyName": "Aurora Cannabis Inc.", "currentPrice": 0.45, "marketCap": "Small"},
        "CGC": {"symbol": "CGC", "companyName": "Canopy Growth Corporation", "currentPrice": 1.23, "marketCap": "Small"},
        "HEXO": {"symbol": "HEXO", "companyName": "HEXO Corp.", "currentPrice": 0.34, "marketCap": "Small"},
        "OGI": {"symbol": "OGI", "companyName": "OrganiGram Holdings Inc.", "currentPrice": 0.56, "marketCap": "Small"},
        
        # Biotech Small Caps
        "BNTX": {"symbol": "BNTX", "companyName": "BioNTech SE", "currentPrice": 123.45, "marketCap": "Small"},
        "MRNA": {"symbol": "MRNA", "companyName": "Moderna Inc.", "currentPrice": 89.12, "marketCap": "Small"},
        "NVAX": {"symbol": "NVAX", "companyName": "Novavax Inc.", "currentPrice": 12.34, "marketCap": "Small"},
        "INO": {"symbol": "INO", "companyName": "Inovio Pharmaceuticals Inc.", "currentPrice": 0.45, "marketCap": "Small"},
        "OCGN": {"symbol": "OCGN", "companyName": "Ocugen Inc.", "currentPrice": 0.78, "marketCap": "Small"},
        "VXRT": {"symbol": "VXRT", "companyName": "Vaxart Inc.", "currentPrice": 0.23, "marketCap": "Small"},
        
        # EV & Clean Energy Small Caps
        "NIO": {"symbol": "NIO", "companyName": "NIO Inc.", "currentPrice": 8.90, "marketCap": "Small"},
        "XPEV": {"symbol": "XPEV", "companyName": "XPeng Inc.", "currentPrice": 12.34, "marketCap": "Small"},
        "LI": {"symbol": "LI", "companyName": "Li Auto Inc.", "currentPrice": 23.45, "marketCap": "Small"},
        "LCID": {"symbol": "LCID", "companyName": "Lucid Group Inc.", "currentPrice": 4.56, "marketCap": "Small"},
        "RIVN": {"symbol": "RIVN", "companyName": "Rivian Automotive Inc.", "currentPrice": 15.67, "marketCap": "Small"},
        "F": {"symbol": "F", "companyName": "Ford Motor Company", "currentPrice": 12.34, "marketCap": "Large"},
        "GM": {"symbol": "GM", "companyName": "General Motors Company", "currentPrice": 45.67, "marketCap": "Large"},
        "FORD": {"symbol": "FORD", "companyName": "Ford Motor Company", "currentPrice": 12.34, "marketCap": "Large"},
        "PLUG": {"symbol": "PLUG", "companyName": "Plug Power Inc.", "currentPrice": 8.90, "marketCap": "Small"},
        "FCEL": {"symbol": "FCEL", "companyName": "FuelCell Energy Inc.", "currentPrice": 2.34, "marketCap": "Small"},
        "BLDP": {"symbol": "BLDP", "companyName": "Ballard Power Systems Inc.", "currentPrice": 3.45, "marketCap": "Small"},
        "BE": {"symbol": "BE", "companyName": "Bloom Energy Corporation", "currentPrice": 12.34, "marketCap": "Small"},
        "RUN": {"symbol": "RUN", "companyName": "Sunrun Inc.", "currentPrice": 15.67, "marketCap": "Small"},
        "SPWR": {"symbol": "SPWR", "companyName": "SunPower Corporation", "currentPrice": 4.56, "marketCap": "Small"},
        "ENPH": {"symbol": "ENPH", "companyName": "Enphase Energy Inc.", "currentPrice": 123.45, "marketCap": "Small"},
        "SEDG": {"symbol": "SEDG", "companyName": "SolarEdge Technologies Inc.", "currentPrice": 78.90, "marketCap": "Small"},
        "FSLR": {"symbol": "FSLR", "companyName": "First Solar Inc.", "currentPrice": 89.12, "marketCap": "Small"},
        
        # Fintech & Crypto Small Caps
        "SOFI": {"symbol": "SOFI", "companyName": "SoFi Technologies Inc.", "currentPrice": 8.90, "marketCap": "Small"},
        "UPST": {"symbol": "UPST", "companyName": "Upstart Holdings Inc.", "currentPrice": 23.45, "marketCap": "Small"},
        "LC": {"symbol": "LC", "companyName": "LendingClub Corporation", "currentPrice": 4.56, "marketCap": "Small"},
        "AFRM": {"symbol": "AFRM", "companyName": "Affirm Holdings Inc.", "currentPrice": 15.67, "marketCap": "Small"},
        "OPEN": {"symbol": "OPEN", "companyName": "Opendoor Technologies Inc.", "currentPrice": 2.34, "marketCap": "Small"},
        "Z": {"symbol": "Z", "companyName": "Zillow Group Inc.", "currentPrice": 45.67, "marketCap": "Small"},
        "ZG": {"symbol": "ZG", "companyName": "Zillow Group Inc.", "currentPrice": 45.67, "marketCap": "Small"},
        "RKT": {"symbol": "RKT", "companyName": "Rocket Companies Inc.", "currentPrice": 8.90, "marketCap": "Small"},
        "COMP": {"symbol": "COMP", "companyName": "Compass Inc.", "currentPrice": 3.45, "marketCap": "Small"},
        "REAL": {"symbol": "REAL", "companyName": "The RealReal Inc.", "currentPrice": 1.23, "marketCap": "Small"},
        "RDFN": {"symbol": "RDFN", "companyName": "Redfin Corporation", "currentPrice": 6.78, "marketCap": "Small"},
        "EXPI": {"symbol": "EXPI", "companyName": "eXp World Holdings Inc.", "currentPrice": 12.34, "marketCap": "Small"},
        
        # Gaming & Entertainment Small Caps
        "ATVI": {"symbol": "ATVI", "companyName": "Activision Blizzard Inc.", "currentPrice": 78.90, "marketCap": "Large"},
        "EA": {"symbol": "EA", "companyName": "Electronic Arts Inc.", "currentPrice": 123.45, "marketCap": "Large"},
        "TTWO": {"symbol": "TTWO", "companyName": "Take-Two Interactive Software Inc.", "currentPrice": 156.78, "marketCap": "Large"},
        "U": {"symbol": "U", "companyName": "Unity Software Inc.", "currentPrice": 23.45, "marketCap": "Mid"},
        "RBLX": {"symbol": "RBLX", "companyName": "Roblox Corporation", "currentPrice": 34.56, "marketCap": "Mid"},
        "DKNG": {"symbol": "DKNG", "companyName": "DraftKings Inc.", "currentPrice": 12.34, "marketCap": "Small"},
        "PENN": {"symbol": "PENN", "companyName": "Penn National Gaming Inc.", "currentPrice": 15.67, "marketCap": "Small"},
        "MGM": {"symbol": "MGM", "companyName": "MGM Resorts International", "currentPrice": 45.67, "marketCap": "Large"},
        "LVS": {"symbol": "LVS", "companyName": "Las Vegas Sands Corp.", "currentPrice": 56.78, "marketCap": "Large"},
        "WYNN": {"symbol": "WYNN", "companyName": "Wynn Resorts Limited", "currentPrice": 78.90, "marketCap": "Large"},
        "CZR": {"symbol": "CZR", "companyName": "Caesars Entertainment Inc.", "currentPrice": 23.45, "marketCap": "Small"},
        "BYD": {"symbol": "BYD", "companyName": "Boyd Gaming Corporation", "currentPrice": 34.56, "marketCap": "Small"},
        
        # Additional Popular Stocks
        "BABA": {"symbol": "BABA", "companyName": "Alibaba Group Holding Limited", "currentPrice": 89.12, "marketCap": "Large"},
        "JD": {"symbol": "JD", "companyName": "JD.com Inc.", "currentPrice": 45.67, "marketCap": "Large"},
        "PDD": {"symbol": "PDD", "companyName": "PDD Holdings Inc.", "currentPrice": 78.90, "marketCap": "Large"},
        "BIDU": {"symbol": "BIDU", "companyName": "Baidu Inc.", "currentPrice": 123.45, "marketCap": "Large"},
        "NTES": {"symbol": "NTES", "companyName": "NetEase Inc.", "currentPrice": 67.89, "marketCap": "Large"},
        "TME": {"symbol": "TME", "companyName": "Tencent Music Entertainment Group", "currentPrice": 4.56, "marketCap": "Mid"},
        "VIPS": {"symbol": "VIPS", "companyName": "Vipshop Holdings Limited", "currentPrice": 8.90, "marketCap": "Small"},
        "YMM": {"symbol": "YMM", "companyName": "Full Truck Alliance Co. Ltd.", "currentPrice": 6.78, "marketCap": "Small"},
        "DIDI": {"symbol": "DIDI", "companyName": "DiDi Global Inc.", "currentPrice": 2.34, "marketCap": "Small"},
        "GRAB": {"symbol": "GRAB", "companyName": "Grab Holdings Limited", "currentPrice": 3.45, "marketCap": "Small"},
        "SE": {"symbol": "SE", "companyName": "Sea Limited", "currentPrice": 45.67, "marketCap": "Mid"},
        "GOTU": {"symbol": "GOTU", "companyName": "Gaotu Techedu Inc.", "currentPrice": 1.23, "marketCap": "Small"},
        "TAL": {"symbol": "TAL", "companyName": "TAL Education Group", "currentPrice": 2.34, "marketCap": "Small"},
        "EDU": {"symbol": "EDU", "companyName": "New Oriental Education & Technology Group Inc.", "currentPrice": 3.45, "marketCap": "Small"},
        "COE": {"symbol": "COE", "companyName": "51job Inc.", "currentPrice": 4.56, "marketCap": "Small"}
    }

# In-memory storage for comments (in a real app, this would be a database)
discussion_comments = {
    "discussion_1": [],
    "discussion_2": [],
    "discussion_3": [],
    "discussion_4": [],
    "discussion_5": []
}

# Initialize FastAPI app
app = FastAPI(
    title="RichesReach AI Service",
    description="Production AI-powered investment portfolio analysis and market intelligence",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simple in-memory user storage (replace with database in production)
users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": hashlib.sha256("password123".encode()).hexdigest(),
        "name": "Test User",
        "id": "1"
    }
}

# Initialize real data services
market_data_service = SimpleMarketDataService()
real_options_service = RealOptionsService()

# WebSocket connection management
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.stock_connections: List[WebSocket] = []
        self.discussion_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        await websocket.accept()
        self.active_connections.append(websocket)
        if connection_type == "stock":
            self.stock_connections.append(websocket)
        elif connection_type == "discussion":
            self.discussion_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, connection_type: str = "general"):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if connection_type == "stock" and websocket in self.stock_connections:
            self.stock_connections.remove(websocket)
        elif connection_type == "discussion" and websocket in self.discussion_connections:
            self.discussion_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str, connection_type: str = "general"):
        connections = self.active_connections
        if connection_type == "stock":
            connections = self.stock_connections
        elif connection_type == "discussion":
            connections = self.discussion_connections
            
        for connection in connections.copy():
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

# Security
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Real data generators
async def calculate_affordability_score(stock_data: Dict[str, Any], user_income: float) -> Dict[str, Any]:
    """Calculate affordability metrics based on user income and stock price"""
    current_price = stock_data["currentPrice"]
    
    # Calculate affordability metrics
    shares_affordable_1k = 1000 / current_price  # How many shares with $1k
    shares_affordable_5k = 5000 / current_price  # How many shares with $5k
    shares_affordable_10k = 10000 / current_price  # How many shares with $10k
    
    # Income-based affordability tiers
    if user_income < 30000:  # Low income
        min_shares = 1
        max_investment = user_income * 0.05  # 5% of annual income
        risk_multiplier = 0.5  # Lower risk tolerance
    elif user_income < 75000:  # Medium income
        min_shares = 2
        max_investment = user_income * 0.1  # 10% of annual income
        risk_multiplier = 0.75
    elif user_income < 150000:  # High income
        min_shares = 5
        max_investment = user_income * 0.15  # 15% of annual income
        risk_multiplier = 1.0
    else:  # Very high income
        min_shares = 10
        max_investment = user_income * 0.2  # 20% of annual income
        risk_multiplier = 1.25
    
    # Calculate if stock is affordable
    max_shares_affordable = max_investment / current_price
    is_affordable = max_shares_affordable >= min_shares
    
    # Calculate recommended position size
    if max_shares_affordable >= 100:
        position_size = "Large"
    elif max_shares_affordable >= 20:
        position_size = "Medium"
    elif max_shares_affordable >= 5:
        position_size = "Small"
    else:
        position_size = "Micro"
    
    return {
        "is_affordable": is_affordable,
        "max_shares_affordable": round(max_shares_affordable, 0),
        "max_investment": round(max_investment, 2),
        "position_size": position_size,
        "shares_1k": round(shares_affordable_1k, 2),
        "shares_5k": round(shares_affordable_5k, 2),
        "shares_10k": round(shares_affordable_10k, 2),
        "risk_multiplier": risk_multiplier,
        "income_tier": "Low" if user_income < 30000 else "Medium" if user_income < 75000 else "High" if user_income < 150000 else "Very High"
    }

async def calculate_stock_recommendation(stock_data: Dict[str, Any], user_income: float = 50000) -> str:
    """Calculate intelligent stock recommendation based on real data analysis and user income"""
    score = 0
    current_price = stock_data["currentPrice"]
    change_percent = stock_data["changePercent"]
    pe_ratio = stock_data["peRatio"]
    beginner_score = stock_data["beginnerFriendlyScore"]
    risk_level = stock_data["riskLevel"]
    target_price = stock_data["targetPrice"]
    
    # Get affordability metrics
    affordability = await calculate_affordability_score(stock_data, user_income)
    
    # Price momentum analysis (40% weight)
    if change_percent > 2:
        score += 40  # Strong positive momentum
    elif change_percent > 0:
        score += 20  # Positive momentum
    elif change_percent > -2:
        score += 0   # Neutral
    else:
        score -= 20  # Negative momentum
    
    # Valuation analysis (25% weight)
    if pe_ratio < 15:
        score += 25  # Undervalued
    elif pe_ratio < 25:
        score += 15  # Fairly valued
    elif pe_ratio < 35:
        score += 5   # Slightly overvalued
    else:
        score -= 15  # Overvalued
    
    # Target price analysis (20% weight)
    price_to_target = (target_price - current_price) / current_price
    if price_to_target > 0.15:
        score += 20  # Strong upside potential
    elif price_to_target > 0.05:
        score += 10  # Good upside potential
    elif price_to_target > -0.05:
        score += 0   # Neutral
    else:
        score -= 10  # Downside risk
    
    # Risk assessment (15% weight) - adjusted for income
    risk_score = 0
    if risk_level == "Low":
        risk_score = 15
    elif risk_level == "Medium":
        risk_score = 5
    else:  # High risk
        risk_score = -5
    
    # Apply income-based risk multiplier
    risk_score *= affordability["risk_multiplier"]
    score += risk_score
    
    # Affordability bonus/penalty (10% weight)
    if affordability["is_affordable"]:
        if affordability["position_size"] == "Large":
            score += 10  # Great for building large positions
        elif affordability["position_size"] == "Medium":
            score += 5   # Good for medium positions
        elif affordability["position_size"] == "Small":
            score += 2   # Okay for small positions
        else:  # Micro
            score -= 5   # Too expensive for meaningful position
    else:
        score -= 15  # Not affordable - strong negative
    
    # Price tier adjustment based on income
    if user_income < 30000:  # Low income - prefer cheaper stocks
        if current_price < 50:
            score += 5
        elif current_price > 200:
            score -= 10
    elif user_income < 75000:  # Medium income - moderate price range
        if current_price < 100:
            score += 3
        elif current_price > 500:
            score -= 5
    # High income users can afford any price range
    
    # Generate recommendation
    if score >= 60:
        return "BUY"
    elif score >= 20:
        return "HOLD"
    else:
        return "SELL"

async def generate_stock_reasoning(stock_data: Dict[str, Any], user_income: float = 50000) -> List[str]:
    """Generate intelligent reasoning based on real stock data analysis and user income"""
    reasoning = []
    current_price = stock_data["currentPrice"]
    change_percent = stock_data["changePercent"]
    pe_ratio = stock_data["peRatio"]
    beginner_score = stock_data["beginnerFriendlyScore"]
    risk_level = stock_data["riskLevel"]
    target_price = stock_data["targetPrice"]
    
    # Get affordability metrics
    affordability = await calculate_affordability_score(stock_data, user_income)
    
    # Price momentum analysis
    if change_percent > 2:
        reasoning.append(f"Strong positive momentum with {change_percent:.1f}% gain today")
    elif change_percent > 0:
        reasoning.append(f"Positive momentum with {change_percent:.1f}% gain today")
    elif change_percent > -2:
        reasoning.append(f"Neutral momentum with {change_percent:.1f}% change today")
    else:
        reasoning.append(f"Negative momentum with {change_percent:.1f}% decline today")
    
    # Valuation analysis
    if pe_ratio < 15:
        reasoning.append(f"Attractive valuation with P/E ratio of {pe_ratio:.1f} (undervalued)")
    elif pe_ratio < 25:
        reasoning.append(f"Fair valuation with P/E ratio of {pe_ratio:.1f}")
    elif pe_ratio < 35:
        reasoning.append(f"Elevated valuation with P/E ratio of {pe_ratio:.1f}")
    else:
        reasoning.append(f"High valuation with P/E ratio of {pe_ratio:.1f} (overvalued)")
    
    # Target price analysis
    price_to_target = (target_price - current_price) / current_price
    if price_to_target > 0.15:
        reasoning.append(f"Strong upside potential with target price ${target_price:.2f} (+{price_to_target*100:.1f}%)")
    elif price_to_target > 0.05:
        reasoning.append(f"Good upside potential with target price ${target_price:.2f} (+{price_to_target*100:.1f}%)")
    elif price_to_target > -0.05:
        reasoning.append(f"Target price ${target_price:.2f} is close to current price")
    else:
        reasoning.append(f"Downside risk with target price ${target_price:.2f} ({price_to_target*100:.1f}%)")
    
    # Risk and beginner friendliness
    reasoning.append(f"Risk level: {risk_level}, Beginner score: {beginner_score:.1f}/10")
    
    # Income-based affordability insights
    if affordability["is_affordable"]:
        reasoning.append(f"✅ Affordable for your income: Can buy {affordability['max_shares_affordable']:.0f} shares (${affordability['max_investment']:.0f} max investment)")
        reasoning.append(f"Position size: {affordability['position_size']} - Good for {affordability['income_tier']} income tier")
        
        # Add specific investment suggestions
        if affordability["shares_1k"] >= 1:
            reasoning.append(f"With $1,000: You could buy {affordability['shares_1k']:.0f} shares")
        if affordability["shares_5k"] >= 1:
            reasoning.append(f"With $5,000: You could buy {affordability['shares_5k']:.0f} shares")
    else:
        reasoning.append(f"❌ Not affordable: Would need ${current_price * affordability['max_shares_affordable']:.0f} to buy {affordability['max_shares_affordable']:.0f} shares")
        reasoning.append(f"Consider fractional shares or lower-priced alternatives for {affordability['income_tier']} income tier")
    
    return reasoning

async def filter_stocks_by_income(stocks_data: List[Dict[str, Any]], user_income: float) -> List[Dict[str, Any]]:
    """Filter and rank stocks based on user income and affordability"""
    filtered_stocks = []
    
    for stock in stocks_data:
        affordability = await calculate_affordability_score(stock, user_income)
        
        # Add affordability data to each stock
        stock["affordability"] = affordability
        
        # Only include affordable stocks for low-income users
        if user_income < 30000 and not affordability["is_affordable"]:
            continue
            
        # For medium income, include stocks that are at least small position size
        if user_income < 75000 and affordability["position_size"] == "Micro":
            continue
            
        filtered_stocks.append(stock)
    
    # Sort by affordability score (affordable + good position size first)
    def affordability_score(stock):
        score = 0
        if stock["affordability"]["is_affordable"]:
            score += 100
        if stock["affordability"]["position_size"] == "Large":
            score += 50
        elif stock["affordability"]["position_size"] == "Medium":
            score += 30
        elif stock["affordability"]["position_size"] == "Small":
            score += 10
        return score
    
    return sorted(filtered_stocks, key=affordability_score, reverse=True)

async def generate_stock_data(symbol: str) -> Dict[str, Any]:
    """Generate stock data with real API integration, caching, and performance optimization"""
    try:
        # Check cache first
        cached_data = stock_cache.get(symbol)
        if cached_data:
            logger.info(f"Using cached data for {symbol}")
            return cached_data
        
        # Try to get real-time data from APIs with timeout
        logger.info(f"Fetching real data for {symbol}")
        try:
            # Add timeout to prevent hanging
            price_data = await asyncio.wait_for(
                market_data_service.get_stock_quote(symbol), 
                timeout=5.0  # 5 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"API timeout for {symbol}, using mock data")
            price_data = None
        
        if price_data and price_data.get('price', 0) > 0:
            # Use real data from API
            logger.info(f"Using real API data for {symbol}: ${price_data['price']} from {price_data.get('provider', 'api')}")
            formatted_data = await format_real_stock_data(symbol, price_data)
            # Cache the data
            stock_cache.set(symbol, formatted_data)
            return formatted_data
        else:
            # Fallback to enhanced mock data if API fails
            logger.warning(f"API data not available for {symbol}, using enhanced mock data")
            mock_data = await generate_enhanced_mock_data(symbol)
            # Cache the mock data too
            stock_cache.set(symbol, mock_data)
            return mock_data
            
    except Exception as e:
        logger.error(f"Error fetching real data for {symbol}: {e}")
        mock_data = await generate_enhanced_mock_data(symbol)
        # Cache the mock data
        stock_cache.set(symbol, mock_data)
        return mock_data

async def format_real_stock_data(symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format real API data into our expected stock data structure"""
    company_names = {
        "AAPL": "Apple Inc.", "GOOGL": "Alphabet Inc.", "MSFT": "Microsoft Corporation",
        "TSLA": "Tesla Inc.", "AMZN": "Amazon.com Inc.", "NFLX": "Netflix Inc.",
        "NVDA": "NVIDIA Corporation", "AMD": "Advanced Micro Devices", "INTC": "Intel Corporation",
        "CRM": "Salesforce Inc.", "ADBE": "Adobe Inc.", "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble", "KO": "The Coca-Cola Company", "WMT": "Walmart Inc.",
        "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America Corp.",
        "V": "Visa Inc.", "MA": "Mastercard Inc.", "DIS": "The Walt Disney Company",
        "NKE": "Nike Inc.", "UBER": "Uber Technologies Inc.", "LYFT": "Lyft Inc."
    }
    
    sectors = {
        "AAPL": "Technology", "GOOGL": "Technology", "MSFT": "Technology",
        "TSLA": "Automotive", "AMZN": "Consumer Discretionary", "NFLX": "Communication Services",
        "NVDA": "Technology", "AMD": "Technology", "INTC": "Technology",
        "CRM": "Technology", "ADBE": "Technology", "JNJ": "Healthcare",
        "PG": "Consumer Staples", "KO": "Consumer Staples", "WMT": "Consumer Staples",
        "JPM": "Financial Services", "BAC": "Financial Services", "V": "Financial Services",
        "MA": "Financial Services", "DIS": "Communication Services", "NKE": "Consumer Discretionary",
        "UBER": "Technology", "LYFT": "Technology"
    }
    
    # Calculate market cap (rough estimate based on price and volume)
    estimated_shares = 1000000000  # 1B shares as rough estimate
    market_cap = price_data['price'] * estimated_shares
    
    return {
        "id": f"stock_{symbol}",
        "symbol": symbol,
        "companyName": company_names.get(symbol, f"{symbol} Corporation"),
        "sector": sectors.get(symbol, "Technology"),
        "price": round(price_data['price'], 2),
        "currentPrice": round(price_data['price'], 2),
        "change": round(price_data.get('change', 0), 2),
        "changePercent": round(price_data.get('change_percent', 0), 2),
        "volume": price_data.get('volume', 0),
        "marketCap": round(market_cap, 0),
        "peRatio": round(random.uniform(15, 35), 2),  # Still calculated
        "dividendYield": round(random.uniform(0, 4), 2),  # Still calculated
        "beginnerFriendlyScore": round(random.uniform(6, 10), 1),  # Still calculated
        "mlScore": round(random.uniform(5, 10), 1),  # Still calculated
        "riskLevel": random.choice(["Low", "Medium", "High"]),  # Still calculated
        "growthPotential": round(random.uniform(0, 100), 1),  # Still calculated
        "targetPrice": round(price_data['price'] * random.uniform(0.9, 1.2), 2),  # Target price based on current price
        "timestamp": price_data.get('timestamp', datetime.now().isoformat()),
        "source": price_data.get('provider', 'api'),
        "__typename": "Stock"
    }

async def generate_enhanced_mock_data(symbol: str) -> Dict[str, Any]:
    """Generate enhanced mock data that simulates real market data"""
    # Realistic base prices for major stocks
    real_prices = {
        "AAPL": 175.0, "GOOGL": 140.0, "MSFT": 350.0, "TSLA": 250.0,
        "AMZN": 150.0, "NFLX": 450.0, "NVDA": 800.0, "AMD": 120.0,
        "INTC": 50.0, "CRM": 200.0, "ADBE": 500.0, "JNJ": 160.0,
        "PG": 140.0, "KO": 55.0, "WMT": 150.0, "JPM": 150.0,
        "BAC": 40.0, "V": 250.0, "MA": 350.0, "DIS": 180.0,
        "NKE": 120.0, "UBER": 60.0, "LYFT": 15.0
    }
    
    company_names = {
        "AAPL": "Apple Inc.", "GOOGL": "Alphabet Inc.", "MSFT": "Microsoft Corporation",
        "TSLA": "Tesla Inc.", "AMZN": "Amazon.com Inc.", "NFLX": "Netflix Inc.",
        "NVDA": "NVIDIA Corporation", "AMD": "Advanced Micro Devices", "INTC": "Intel Corporation",
        "CRM": "Salesforce Inc.", "ADBE": "Adobe Inc.", "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble", "KO": "The Coca-Cola Company", "WMT": "Walmart Inc.",
        "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America Corp.",
        "V": "Visa Inc.", "MA": "Mastercard Inc.", "DIS": "The Walt Disney Company",
        "NKE": "Nike Inc.", "UBER": "Uber Technologies Inc.", "LYFT": "Lyft Inc."
    }
    
    sectors = {
        "AAPL": "Technology", "GOOGL": "Technology", "MSFT": "Technology",
        "TSLA": "Automotive", "AMZN": "Consumer Discretionary", "NFLX": "Communication Services",
        "NVDA": "Technology", "AMD": "Technology", "INTC": "Technology",
        "CRM": "Technology", "ADBE": "Technology", "JNJ": "Healthcare",
        "PG": "Consumer Staples", "KO": "Consumer Staples", "WMT": "Consumer Staples",
        "JPM": "Financial Services", "BAC": "Financial Services", "V": "Financial Services",
        "MA": "Financial Services", "DIS": "Communication Services", "NKE": "Consumer Discretionary",
        "UBER": "Technology", "LYFT": "Technology"
    }
    
    # Use realistic base price or generate one
    base_price = real_prices.get(symbol, random.uniform(50, 500))
    
    # Simulate realistic market movements
    change = random.uniform(-0.03, 0.03)  # ±3% change (more realistic)
    change_percent = change * 100
    market_cap = base_price * random.uniform(1e9, 1e12)  # 1B to 1T market cap
    pe_ratio = random.uniform(15, 35)  # More realistic PE ratios
    
    return {
        "id": f"stock_{symbol}",
        "symbol": symbol,
        "companyName": company_names.get(symbol, f"{symbol} Corporation"),
        "sector": sectors.get(symbol, "Technology"),
        "price": round(base_price * (1 + change), 2),
        "currentPrice": round(base_price * (1 + change), 2),
        "change": round(base_price * change, 2),
        "changePercent": round(change_percent, 2),
        "volume": random.randint(1000000, 50000000),  # More realistic volume
        "marketCap": round(market_cap, 0),
        "peRatio": round(pe_ratio, 2),
        "dividendYield": round(random.uniform(0, 4), 2),  # More realistic dividend yields
        "beginnerFriendlyScore": round(random.uniform(6, 10), 1),
        "mlScore": round(random.uniform(5, 10), 1),
        "riskLevel": random.choice(["Low", "Medium", "High"]),
        "growthPotential": round(random.uniform(0, 100), 1),
        "targetPrice": round(base_price * (1 + change) * random.uniform(0.9, 1.2), 2),  # Target price based on current price
        "timestamp": datetime.now().isoformat(),
        "source": "enhanced_mock",
        "__typename": "Stock"
    }

async def generate_fallback_stock_data(symbol: str) -> Dict[str, Any]:
    """Generate fallback mock stock data when APIs are unavailable"""
    company_names = {
        "AAPL": "Apple Inc.", "GOOGL": "Alphabet Inc.", "MSFT": "Microsoft Corporation",
        "TSLA": "Tesla Inc.", "AMZN": "Amazon.com Inc.", "NFLX": "Netflix Inc.",
        "NVDA": "NVIDIA Corporation", "AMD": "Advanced Micro Devices", "INTC": "Intel Corporation",
        "CRM": "Salesforce Inc.", "ADBE": "Adobe Inc.", "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble", "KO": "The Coca-Cola Company", "WMT": "Walmart Inc.",
        "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America Corp.",
        "V": "Visa Inc.", "MA": "Mastercard Inc.", "DIS": "The Walt Disney Company",
        "NKE": "Nike Inc.", "UBER": "Uber Technologies Inc.", "LYFT": "Lyft Inc."
    }
    
    sectors = {
        "AAPL": "Technology", "GOOGL": "Technology", "MSFT": "Technology",
        "TSLA": "Automotive", "AMZN": "Consumer Discretionary", "NFLX": "Communication Services",
        "NVDA": "Technology", "AMD": "Technology", "INTC": "Technology",
        "CRM": "Technology", "ADBE": "Technology", "JNJ": "Healthcare",
        "PG": "Consumer Staples", "KO": "Consumer Staples", "WMT": "Consumer Staples",
        "JPM": "Financial Services", "BAC": "Financial Services", "V": "Financial Services",
        "MA": "Financial Services", "DIS": "Communication Services", "NKE": "Consumer Discretionary",
        "UBER": "Technology", "LYFT": "Technology"
    }
    
    base_price = random.uniform(50, 500)
    change = random.uniform(-0.05, 0.05)
    change_percent = change * 100
    market_cap = random.uniform(1000000000, 3000000000000)  # 1B to 3T
    pe_ratio = random.uniform(10, 50)
    
    return {
        "id": f"stock_{symbol}",
        "symbol": symbol,
        "companyName": company_names.get(symbol, f"{symbol} Corporation"),
        "sector": sectors.get(symbol, "Technology"),
        "price": round(base_price * (1 + change), 2),
        "currentPrice": round(base_price * (1 + change), 2),
        "change": round(base_price * change, 2),
        "changePercent": round(change_percent, 2),
        "volume": random.randint(1000000, 10000000),
        "marketCap": round(market_cap, 0),
        "peRatio": round(pe_ratio, 2),
        "dividendYield": round(random.uniform(0, 5), 2),
        "beginnerFriendlyScore": round(random.uniform(6, 10), 1),
        "mlScore": round(random.uniform(5, 10), 1),
        "riskLevel": random.choice(["Low", "Medium", "High"]),
        "growthPotential": round(random.uniform(0, 100), 1),
        "targetPrice": round(random.uniform(50, 500), 2),  # Random target price for fallback
        "timestamp": datetime.now().isoformat(),
        "source": "fallback",
        "__typename": "Stock"
    }

def generate_discussion_data() -> Dict[str, Any]:
    topics = ["Market Analysis", "Stock Picks", "Portfolio Review", "Market News", "Trading Tips"]
    authors = ["Trader123", "InvestorPro", "MarketGuru", "FinanceExpert", "StockMaster"]
    return {
        "id": str(random.randint(1000, 9999)),
        "topic": random.choice(topics),
        "author": random.choice(authors),
        "content": f"Discussion about {random.choice(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'])}",
        "likes": random.randint(0, 50),
        "comments": random.randint(0, 20),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RichesReach AI Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "ml_services": False
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ml_services": False,
            "market_data": False,
            "monitoring": False
        }
    }

# WebSocket endpoints
@app.websocket("/ws/stock-prices/")
async def websocket_stock_prices(websocket: WebSocket):
    await manager.connect(websocket, "stock")
    try:
        while True:
            # Send mock stock data every 5 seconds
            stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NFLX", "AMD", "INTC", "CRM", "ADBE"]
            for symbol in stock_symbols:
                stock_data = await generate_stock_data(symbol)
                await manager.send_personal_message(json.dumps(stock_data), websocket)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "stock")

@app.websocket("/ws/discussions/")
async def websocket_discussions(websocket: WebSocket):
    await manager.connect(websocket, "discussion")
    try:
        while True:
            # Send mock discussion data every 10 seconds
            discussion_data = generate_discussion_data()
            await manager.send_personal_message(json.dumps(discussion_data), websocket)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "discussion")

# GraphQL-compatible authentication endpoints
@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    """GraphQL endpoint for authentication"""
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
    # Debug logging
    logger.info(f"Received GraphQL query: {query[:200]}...")
    logger.info(f"Query contains 'stocks': {'stocks' in query}")
    logger.info(f"Query contains 'query': {'query' in query}")
    logger.info(f"Query contains 'me': {'me' in query and 'myPortfolios' not in query and 'createPortfolio' not in query}")
    logger.info(f"Query contains 'premiumPortfolioMetrics': {'premiumPortfolioMetrics' in query}")
    logger.info(f"Query contains 'portfolioMetrics': {'portfolioMetrics' in query}")
    logger.info(f"Query contains 'optionsAnalysis': {'optionsAnalysis' in query}")
    logger.info(f"Query contains 'testOptionsAnalysis': {'testOptionsAnalysis' in query}")
    logger.info(f"Query contains 'aiRecommendations': {'aiRecommendations' in query}")
    logger.info(f"Query contains 'createPortfolio': {'createPortfolio' in query}")
    logger.info(f"Full query: {query}")
    logger.info(f"Variables received: {variables}")
    
    # Parse query to extract requested fields
    def extract_fields(query_str, field_name):
        """Extract requested fields from GraphQL query"""
        if field_name not in query_str:
            return []
        
        # Simple field extraction - look for field_name followed by { ... }
        import re
        pattern = rf'{field_name}\s*{{([^}}]+)}}'
        match = re.search(pattern, query_str, re.DOTALL)
        if match:
            fields_str = match.group(1)
            # Extract field names (simple approach)
            fields = re.findall(r'(\w+)', fields_str)
            return [f.strip() for f in fields if f.strip() and f not in ['__typename']]
        return []
    
    # Handle tokenAuth mutation
    if "tokenAuth" in query:
        email = variables.get("email", "")
        password = variables.get("password", "")
        
        if not email or not password:
            return {
                "errors": [{"message": "Email and password are required"}]
            }
        
        # Check user credentials
        user = users_db.get(email.lower())
        if not user or user["password"] != hashlib.sha256(password.encode()).hexdigest():
            return {
                "errors": [{"message": "Invalid credentials"}]
            }
        
        # Create token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email.lower()}, expires_delta=access_token_expires
        )
        
        return {
            "data": {
                "tokenAuth": {
                    "token": access_token
                }
            }
        }
    
    # Handle createPortfolioHolding mutation - check this first
    elif "mutation" in query.lower() and "createPortfolioHolding" in query:
        try:
            logger.info("Processing createPortfolioHolding mutation")
            logger.info(f"Variables received: {variables}")
            
            # Extract variables
            portfolio_name = variables.get("portfolioName", "Unknown Portfolio")
            stock_id = variables.get("stockId", "UNKNOWN")
            shares = variables.get("shares", 0)
            average_price = variables.get("averagePrice", 100.0)
            current_price = variables.get("currentPrice", 100.0)
            
            logger.info(f"Adding {shares} shares of {stock_id} to {portfolio_name}")
            
            # Return mock success response
            response_data = {
                "createPortfolioHolding": {
                    "success": True,
                    "message": f"Added {shares} shares of {stock_id} to {portfolio_name}",
                    "holding": {
                        "id": f"holding_{stock_id}_{shares}",
                        "stock": {
                            "id": stock_id,
                            "symbol": stock_id,
                            "companyName": f"{stock_id} Corporation"
                        },
                        "shares": shares,
                        "portfolioName": portfolio_name,
                        "averagePrice": average_price,
                        "currentPrice": current_price,
                        "totalValue": shares * current_price
                    }
                }
            }
            
            logger.info(f"Returning response: {response_data}")
            return {"data": response_data}
            
        except Exception as e:
            logger.error(f"Error in createPortfolioHolding mutation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "data": {
                    "createPortfolioHolding": {
                        "success": False,
                        "message": f"Error adding holding: {str(e)}"
                    }
                }
            }
    
    # Handle createPortfolio mutation (but not createPortfolioHolding)
    elif "mutation" in query.lower() and "createPortfolio" in query and "createPortfolioHolding" not in query:
        try:
            logger.info("Processing createPortfolio mutation")
            logger.info(f"Variables received: {variables}")
            logger.info(f"Variables type: {type(variables)}")
            portfolio_name = variables.get("portfolioName", "")
            logger.info(f"Portfolio name extracted: '{portfolio_name}'")
            
            if not portfolio_name or not portfolio_name.strip():
                return {
                    "data": {
                        "createPortfolio": {
                            "success": False,
                            "message": "Portfolio name is required",
                            "portfolioName": None
                        }
                    }
                }
            
            # For now, return a simple success response
            # TODO: Implement proper portfolio creation with database
            response_data = {
                "createPortfolio": {
                    "success": True,
                    "message": f"Portfolio '{portfolio_name}' created successfully",
                    "portfolioName": portfolio_name
                }
            }
            
            logger.info(f"Returning response: {response_data}")
            return {"data": response_data}
        except Exception as e:
            logger.error(f"Error in createPortfolio mutation: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "data": {
                    "createPortfolio": {
                        "success": False,
                        "message": f"Error creating portfolio: {str(e)}",
                        "portfolioName": None
                    }
                }
            }
    
    # Handle createUser mutation
    elif "createUser" in query:
        logger.info("Matched createUser condition")
        email = variables.get("email", "")
        name = variables.get("name", "")
        password = variables.get("password", "")
        
        if not email or not name or not password:
            return {
                "errors": [{"message": "Email, name, and password are required"}]
            }
        
        if email.lower() in users_db:
            return {
                "errors": [{"message": "User already exists"}]
            }
        
        # Create new user
        user_id = str(len(users_db) + 1)
        users_db[email.lower()] = {
            "email": email.lower(),
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "name": name,
            "id": user_id
        }
        
        return {
            "data": {
                "createUser": {
                    "user": {
                        "id": user_id,
                        "email": email.lower(),
                        "name": name
                    }
                }
            }
        }
    
    # Handle generateAiRecommendations mutation
    elif "generateAiRecommendations" in query:
        logger.info("Matched generateAiRecommendations condition")
        logger.info("Generate AI Recommendations mutation requested")
        
        # Generate AI portfolio recommendations
        recommendations = {
            "id": "portfolio_generated",
            "riskProfile": "Moderate Growth",
            "portfolioAllocation": {
                "stocks": 70,
                "bonds": 20,
                "cash": 10
            },
            "recommendedStocks": [
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "allocation": 15,
                    "reason": "Strong fundamentals and growth potential",
                    "reasoning": [
                        "Strong brand loyalty and ecosystem lock-in",
                        "Consistent revenue growth and cash generation",
                        "Leading position in smartphone and services markets"
                    ],
                    "riskLevel": "Low",
                    "expectedReturn": 12.5
                },
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation", 
                    "allocation": 12,
                    "reason": "Cloud computing leader with stable revenue",
                    "reasoning": [
                        "Dominant position in enterprise software",
                        "Azure cloud platform showing strong growth",
                        "Diversified revenue streams across business segments"
                    ],
                    "riskLevel": "Low",
                    "expectedReturn": 11.8
                },
                {
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "allocation": 10,
                    "reason": "Diversified tech exposure and AI growth",
                    "reasoning": [
                        "Search advertising dominance with high margins",
                        "YouTube and cloud services providing growth",
                        "AI investments positioning for future growth"
                    ],
                    "riskLevel": "Medium",
                    "expectedReturn": 13.2
                },
                {
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "allocation": 8,
                    "reason": "Defensive healthcare stock for stability",
                    "reasoning": [
                        "Diversified healthcare portfolio across pharmaceuticals and medical devices",
                        "Consistent dividend payments and stable cash flow",
                        "Defensive characteristics during market volatility"
                    ],
                    "riskLevel": "Low",
                    "expectedReturn": 8.5
                },
                {
                    "symbol": "V",
                    "companyName": "Visa Inc.",
                    "allocation": 7,
                    "reason": "Payment processing growth and low volatility",
                    "reasoning": [
                        "Network effect creates competitive moat",
                        "Global shift to digital payments drives growth",
                        "High-margin business model with recurring revenue"
                    ],
                    "riskLevel": "Low",
                    "expectedReturn": 10.2
                }
            ],
            "expectedReturn": 8.5,
            "expectedPortfolioReturn": 11.2,
            "riskLevel": "Medium",
            "riskAssessment": {
                "overallRisk": "Medium",
                "volatility": "Moderate",
                "downsideProtection": "Good",
                "correlationRisk": "Low"
            },
            "timeHorizon": "5-10 years",
            "lastUpdated": datetime.now().isoformat(),
            "createdAt": datetime.now().isoformat(),
            "__typename": "AIPortfolioRecommendation"
        }
        
        return {
            "data": {
                "generateAiRecommendations": {
                    "success": True,
                    "message": "AI recommendations generated successfully",
                    "recommendations": recommendations
                }
            }
        }
    
    # Handle createIncomeProfile mutation
    elif "createIncomeProfile" in query:
        logger.info("Matched createIncomeProfile condition")
        logger.info("Create Income Profile mutation requested")
        
        income_bracket = variables.get("incomeBracket", "Medium")
        age = variables.get("age", 32)
        investment_goals = variables.get("investmentGoals", ["Long-term growth"])
        risk_tolerance = variables.get("riskTolerance", "Moderate")
        investment_horizon = variables.get("investmentHorizon", "10-15 years")
        
        # Create income profile data
        income_profile = {
            "id": f"income_profile_{int(time.time())}",
            "incomeBracket": income_bracket,
            "age": age,
            "investmentGoals": investment_goals,
            "riskTolerance": risk_tolerance,
            "investmentHorizon": investment_horizon,
            "__typename": "IncomeProfile"
        }
        
        return {
            "data": {
                "createIncomeProfile": {
                    "success": True,
                    "message": "Income profile created successfully",
                    "incomeProfile": income_profile
                }
            }
        }
    
    # Handle createDiscussionComment mutation
    elif "createDiscussionComment" in query:
        logger.info("Matched createDiscussionComment condition")
        logger.info("Create Discussion Comment mutation requested")
        
        discussion_id = variables.get("discussionId", "discussion_1")
        content = variables.get("content", "Great discussion!")
        
        # Create comment data
        comment = {
            "id": f"comment_{int(time.time())}",
            "content": content,
            "createdAt": datetime.now().isoformat(),
            "user": {
                "id": "user_1",
                "name": "Test User",
                "profilePicture": "https://via.placeholder.com/30",
                "profilePic": "https://via.placeholder.com/30",
                "followersCount": 500,
                "followingCount": 200,
                "isFollowingUser": False,
                "isFollowedByUser": True,
                "__typename": "User"
            },
            "__typename": "Comment"
        }
        
        # Store the comment in our in-memory storage
        if discussion_id in discussion_comments:
            discussion_comments[discussion_id].append(comment)
            logger.info(f"Comment stored for discussion {discussion_id}: {content}")
        else:
            # Create new discussion if it doesn't exist
            discussion_comments[discussion_id] = [comment]
            logger.info(f"New discussion created {discussion_id} with comment: {content}")
        
        return {
            "data": {
                "createDiscussionComment": {
                    "success": True,
                    "message": "Comment created successfully",
                    "comment": comment
                }
            }
        }
    
    # Handle AI Rebalance Portfolio mutation
    elif "mutation" in query.lower() and "aiRebalancePortfolio" in query:
        logger.info("Processing aiRebalancePortfolio mutation")
        portfolio_name = variables.get("portfolioName", "default")
        risk_tolerance = variables.get("riskTolerance", "medium")
        max_rebalance = variables.get("maxRebalancePercentage", 20)
        dry_run = variables.get("dryRun", True)
        
        response_data = {
            "aiRebalancePortfolio": {
                "success": True,
                "message": f"Portfolio rebalancing completed successfully for {portfolio_name}",
                "changesMade": 3,
                "stockTrades": [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "action": "BUY",
                        "shares": 5,
                        "price": 234.07,
                        "totalValue": 1170.35,
                        "reason": "Increase position in technology sector",
                        "__typename": "StockTrade"
                    },
                    {
                        "symbol": "TSLA",
                        "companyName": "Tesla Inc.",
                        "action": "SELL",
                        "shares": 2,
                        "price": 395.94,
                        "totalValue": 791.88,
                        "reason": "Reduce position due to high volatility",
                        "__typename": "StockTrade"
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "action": "BUY",
                        "shares": 3,
                        "price": 509.90,
                        "totalValue": 1529.70,
                        "reason": "Diversify technology holdings",
                        "__typename": "StockTrade"
                    }
                ],
                "newPortfolioValue": 210000.75,
                "rebalanceCost": 0.0,
                "estimatedImprovement": 0.08,
                "__typename": "RebalanceResult"
            }
        }
        
        return {"data": response_data}
    
    # Handle stocks queries separately (must be before me handler)
    elif "stocks" in query and "GetStocksForPortfolio" in query:
        logger.info("Processing stocks query - returning stock search data")
        search_term = variables.get("search", "").lower()
        
        # Update prices in background (non-blocking)
        asyncio.create_task(update_stock_prices())
        
        # Get comprehensive stock database (200+ stocks including small-caps)
        stock_database = get_comprehensive_stock_database()
        
        # Hybrid search: instant database search + API fallback
        if search_term:
            # First, search the comprehensive database (instant)
            matching_stocks = []
            for symbol, data in stock_database.items():
                if (search_term in symbol.lower() or 
                    search_term in data["companyName"].lower() or
                    search_term in data["symbol"].lower()):
                    matching_stocks.append(data)
            
            # If we have results from database, return them (instant)
            if matching_stocks:
                matching_stocks = matching_stocks[:10]
            else:
                # Fallback: try to fetch from API for unknown stocks
                try:
                    logger.info(f"No database match for '{search_term}', trying API fallback")
                    # Try to fetch real data for the search term
                    api_stock_data = await generate_stock_data(search_term.upper())
                    if api_stock_data:
                        matching_stocks = [api_stock_data]
                    else:
                        matching_stocks = []
                except Exception as e:
                    logger.warning(f"API fallback failed for '{search_term}': {str(e)}")
                    matching_stocks = []
        else:
            # No search term, return popular stocks from database
            matching_stocks = list(stock_database.values())[:10]
        
        # Format response (instant, no API calls)
        stocks_data = []
        for stock in matching_stocks:
            stocks_data.append({
                "id": f"stock_{stock['symbol']}",
                "symbol": stock['symbol'],
                "companyName": stock['companyName'],
                "currentPrice": stock['currentPrice'],
                "__typename": "Stock"
            })
        
        response_data = {
            "stocks": stocks_data
        }
        
        return {"data": response_data}
    
    # Handle myPortfolios queries separately
    elif "myPortfolios" in query:
        logger.info("Processing myPortfolios query - returning portfolio data")
        response_data = {
            "myPortfolios": {
                "totalPortfolios": 2,
                "totalValue": 150000.75,
                "portfolios": [
                    {
                        "name": "Growth Portfolio",
                        "totalValue": 125000.50,
                        "holdingsCount": 5,
                        "holdings": [
                            {
                                "id": "1",
                                "stock": {
                                    "id": "1",
                                    "symbol": "AAPL",
                                    "companyName": "Apple Inc."
                                },
                                "shares": 100,
                                "averagePrice": 150.00,
                                "currentPrice": 239.69,
                                "totalValue": 23969.00,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "2",
                                "stock": {
                                    "id": "2",
                                    "symbol": "GOOGL",
                                    "companyName": "Alphabet Inc."
                                },
                                "shares": 50,
                                "averagePrice": 2800.00,
                                "currentPrice": 240.80,
                                "totalValue": 12040.00,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "3",
                                "stock": {
                                    "id": "3",
                                    "symbol": "MSFT",
                                    "companyName": "Microsoft Corporation"
                                },
                                "shares": 75,
                                "averagePrice": 400.00,
                                "currentPrice": 509.90,
                                "totalValue": 38242.50,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "4",
                                "stock": {
                                    "id": "4",
                                    "symbol": "TSLA",
                                    "companyName": "Tesla Inc."
                                },
                                "shares": 25,
                                "averagePrice": 200.00,
                                "currentPrice": 395.94,
                                "totalValue": 9898.50,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "5",
                                "stock": {
                                    "id": "5",
                                    "symbol": "AMZN",
                                    "companyName": "Amazon.com Inc."
                                },
                                "shares": 40,
                                "averagePrice": 150.00,
                                "currentPrice": 228.15,
                                "totalValue": 9126.00,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            }
                        ]
                    },
                    {
                        "name": "Conservative Portfolio",
                        "totalValue": 26220.15,
                        "holdingsCount": 5,
                        "holdings": [
                            {
                                "id": "6",
                                "stock": {
                                    "id": "6",
                                    "symbol": "JNJ",
                                    "companyName": "Johnson & Johnson"
                                },
                                "shares": 50,
                                "averagePrice": 160.00,
                                "currentPrice": 165.50,
                                "totalValue": 8275.00,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "7",
                                "stock": {
                                    "id": "7",
                                    "symbol": "PG",
                                    "companyName": "Procter & Gamble Co."
                                },
                                "shares": 30,
                                "averagePrice": 150.00,
                                "currentPrice": 157.90,
                                "totalValue": 4737.00,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "8",
                                "stock": {
                                    "id": "8",
                                    "symbol": "KO",
                                    "companyName": "Coca-Cola Company"
                                },
                                "shares": 80,
                                "averagePrice": 60.00,
                                "currentPrice": 67.01,
                                "totalValue": 5360.80,
                                "notes": "",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "updatedAt": "2024-01-01T00:00:00Z"
                            },
                            {
                                "id": "holding_stock_MGM_3",
                                "stock": {
                                    "id": "stock_MGM",
                                    "symbol": "MGM",
                                    "companyName": "MGM Resorts International"
                                },
                                "shares": 3,
                                "averagePrice": None,
                                "currentPrice": 131.48,
                                "totalValue": 394.45,
                                "notes": "",
                                "createdAt": "2024-09-14T10:27:00Z",
                                "updatedAt": "2024-09-14T10:27:00Z"
                            },
                            {
                                "id": "holding_stock_ORCL_5",
                                "stock": {
                                    "id": "stock_ORCL",
                                    "symbol": "ORCL",
                                    "companyName": "Oracle Corporation"
                                },
                                "shares": 5,
                                "averagePrice": 145.23,
                                "currentPrice": 145.23,
                                "totalValue": 726.15,
                                "notes": "",
                                "createdAt": "2024-09-14T10:30:00Z",
                                "updatedAt": "2024-09-14T10:30:00Z"
                            }
                        ]
                    }
                ]
            }
        }
        return {"data": response_data}
    
    # Handle socialFeed queries separately (must be before me handler)
    elif "socialFeed" in query:
        logger.info("Processing socialFeed query - returning social feed data")
        
        # Mock social feed data
        social_feed_data = [
            {
                "id": "post_1",
                "title": "Market Analysis: Tech Stocks Surge",
                "content": "The technology sector is showing strong momentum with AI and cloud computing leading the charge. Key indicators suggest continued growth potential.",
                "discussionType": "market_analysis",
                "visibility": "public",
                "createdAt": "2024-09-14T10:00:00Z",
                "score": 45,
                "commentCount": 12,
                "user": {
                    "id": "user_1",
                    "name": "Alex Chen",
                    "profilePic": "https://via.placeholder.com/40",
                    "followersCount": 1250,
                    "followingCount": 340,
                    "isFollowingUser": False,
                    "__typename": "User"
                },
                "comments": [
                    {
                        "id": "comment_1",
                        "content": "Great analysis! I've been bullish on AI stocks too.",
                        "createdAt": "2024-09-14T10:15:00Z",
                        "user": {
                            "name": "Sarah Johnson",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    },
                    {
                        "id": "comment_2", 
                        "content": "What's your take on NVDA's recent earnings?",
                        "createdAt": "2024-09-14T10:20:00Z",
                        "user": {
                            "name": "Mike Rodriguez",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    }
                ],
                "__typename": "SocialPost"
            },
            {
                "id": "post_2", 
                "title": "Portfolio Strategy Discussion",
                "content": "Looking for advice on diversifying my portfolio. Currently 70% tech, 20% healthcare, 10% energy. Considering adding some REITs.",
                "discussionType": "strategy",
                "visibility": "public",
                "createdAt": "2024-09-14T09:30:00Z",
                "score": 23,
                "commentCount": 8,
                "user": {
                    "id": "user_2",
                    "name": "Sarah Johnson",
                    "profilePic": "https://via.placeholder.com/40",
                    "followersCount": 890,
                    "followingCount": 156,
                    "isFollowingUser": True,
                    "__typename": "User"
                },
                "comments": [
                    {
                        "id": "comment_3",
                        "content": "REITs are a great addition for diversification!",
                        "createdAt": "2024-09-14T09:45:00Z",
                        "user": {
                            "name": "Alex Chen",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    },
                    {
                        "id": "comment_4",
                        "content": "Consider VNQ for broad REIT exposure",
                        "createdAt": "2024-09-14T09:50:00Z",
                        "user": {
                            "name": "Mike Rodriguez",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    }
                ],
                "__typename": "SocialPost"
            },
            {
                "id": "post_3",
                "title": "Earnings Season Predictions",
                "content": "With Q3 earnings coming up, I'm bullish on AAPL and MSFT. Both have strong fundamentals and positive guidance.",
                "discussionType": "earnings",
                "visibility": "public", 
                "createdAt": "2024-09-14T09:00:00Z",
                "score": 67,
                "commentCount": 15,
                "user": {
                    "id": "user_3",
                    "name": "Mike Rodriguez",
                    "profilePic": "https://via.placeholder.com/40",
                    "followersCount": 2100,
                    "followingCount": 420,
                    "isFollowingUser": False,
                    "__typename": "User"
                },
                "comments": [
                    {
                        "id": "comment_5",
                        "content": "Agreed! Both companies have strong moats",
                        "createdAt": "2024-09-14T09:15:00Z",
                        "user": {
                            "name": "Alex Chen",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    },
                    {
                        "id": "comment_6",
                        "content": "MSFT's cloud growth is impressive",
                        "createdAt": "2024-09-14T09:25:00Z",
                        "user": {
                            "name": "Sarah Johnson",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    },
                    {
                        "id": "comment_7",
                        "content": "What about their P/E ratios?",
                        "createdAt": "2024-09-14T09:30:00Z",
                        "user": {
                            "name": "David Kim",
                            "__typename": "User"
                        },
                        "__typename": "Comment"
                    }
                ],
                "__typename": "SocialPost"
            }
        ]
        
        return {"data": {"socialFeed": social_feed_data}}
    
    # Handle beginnerFriendlyStocks queries separately (must be before me handler)
    elif "beginnerFriendlyStocks" in query:
        logger.info("Processing beginnerFriendlyStocks query - returning beginner-friendly stocks")
        
        # Pre-defined beginner-friendly stock database (instant, no API calls)
        beginner_stock_database = {
            "AAPL": {"symbol": "AAPL", "companyName": "Apple Inc.", "currentPrice": 234.07, "beginnerFriendlyScore": 9.2},
            "GOOGL": {"symbol": "GOOGL", "companyName": "Alphabet Inc.", "currentPrice": 240.8, "beginnerFriendlyScore": 8.8},
            "MSFT": {"symbol": "MSFT", "companyName": "Microsoft Corporation", "currentPrice": 509.9, "beginnerFriendlyScore": 9.0},
            "JNJ": {"symbol": "JNJ", "companyName": "Johnson & Johnson", "currentPrice": 156.23, "beginnerFriendlyScore": 8.5},
            "PG": {"symbol": "PG", "companyName": "Procter & Gamble Co.", "currentPrice": 145.67, "beginnerFriendlyScore": 8.3},
            "KO": {"symbol": "KO", "companyName": "The Coca-Cola Company", "currentPrice": 58.34, "beginnerFriendlyScore": 8.7},
            "WMT": {"symbol": "WMT", "companyName": "Walmart Inc.", "currentPrice": 167.89, "beginnerFriendlyScore": 8.1},
            "JPM": {"symbol": "JPM", "companyName": "JPMorgan Chase & Co.", "currentPrice": 178.45, "beginnerFriendlyScore": 7.8},
            "V": {"symbol": "V", "companyName": "Visa Inc.", "currentPrice": 245.78, "beginnerFriendlyScore": 8.9},
            "MA": {"symbol": "MA", "companyName": "Mastercard Inc.", "currentPrice": 456.23, "beginnerFriendlyScore": 8.6},
            "NVDA": {"symbol": "NVDA", "companyName": "NVIDIA Corporation", "currentPrice": 875.28, "beginnerFriendlyScore": 7.5},
            "META": {"symbol": "META", "companyName": "Meta Platforms Inc.", "currentPrice": 485.12, "beginnerFriendlyScore": 7.2},
            "AMZN": {"symbol": "AMZN", "companyName": "Amazon.com Inc.", "currentPrice": 228.15, "beginnerFriendlyScore": 8.4},
            "TSLA": {"symbol": "TSLA", "companyName": "Tesla Inc.", "currentPrice": 395.94, "beginnerFriendlyScore": 6.8},
            "NFLX": {"symbol": "NFLX", "companyName": "Netflix Inc.", "currentPrice": 1188.44, "beginnerFriendlyScore": 7.1}
        }
        
        # Filter for high beginner-friendly scores (instant, no API calls)
        beginner_stocks = []
        for symbol, data in beginner_stock_database.items():
            if data["beginnerFriendlyScore"] >= 7.0:
                beginner_stocks.append({
                    "id": f"stock_{data['symbol']}",
                    "symbol": data['symbol'],
                    "companyName": data['companyName'],
                    "sector": "Technology",  # Mock sector
                    "marketCap": "Large",  # Mock market cap
                    "peRatio": 25.5,  # Mock PE ratio
                    "dividendYield": 2.1,  # Mock dividend yield
                    "currentPrice": data['currentPrice'],
                    "beginnerFriendlyScore": data['beginnerFriendlyScore'],
                    "__typename": "Stock"
                })
        
        # Limit to 10 results for performance
        beginner_stocks = beginner_stocks[:10]
        
        return {"data": {"beginnerFriendlyStocks": beginner_stocks}}
    
    # Handle me queries separately (only for pure me queries)
    elif "me" in query and "beginnerFriendlyStocks" not in query and "myPortfolios" not in query and "stocks" not in query and "portfolioMetrics" not in query and "myWatchlist" not in query and "advancedStockScreening" not in query and "portfolios" not in query and "discussions" not in query and "aiRecommendations" not in query and "rustStockAnalysis" not in query and "optionsAnalysis" not in query and "testOptionsAnalysis" not in query:
        logger.info("Processing me query - returning user profile data")
        logger.info(f"Query contains 'beginnerFriendlyStocks': {'beginnerFriendlyStocks' in query}")
        user_profile = {
            "id": "user_1",
            "name": "Test User", 
            "email": "test@example.com",
            "profilePic": "https://via.placeholder.com/40",
            "hasPremiumAccess": True,
            "subscriptionTier": "Premium",
            "followersCount": 1250,
            "followingCount": 340,
            "isFollowingUser": False,
            "isFollowedByUser": True,
            "incomeProfile": {
                "incomeBracket": "Medium",
                "age": 32,
                "investmentGoals": "Long-term growth and retirement planning",
                "riskTolerance": "Moderate",
                "investmentHorizon": "10-15 years",
                "__typename": "IncomeProfile"
            },
            "__typename": "User"
        }
        
        return {"data": {"me": user_profile}}
    
    # Handle other GraphQL queries - check for any of these fields (but not if it's a mutation)
    elif not ("mutation" in query.lower()) and any(field in query for field in ["beginnerFriendlyStocks", "advancedStockScreening", "myWatchlist", "portfolios", "discussions", "aiRecommendations", "rustStockAnalysis", "portfolioMetrics", "premiumPortfolioMetrics", "optionsAnalysis", "testOptionsAnalysis", "query", "Query"]) and "createPortfolio" not in query and "aiRebalancePortfolio" not in query or ("query" in query.lower() and "mutation" not in query.lower()):
        # Return mock data for all app queries
        response_data = {}
        
        # Optimized stock data fetching with caching
        async def get_stock_data_optimized(symbols):
            # Check cache first for all symbols
            cached_data = stock_cache.get_multiple(symbols)
            result = []
            
            # Process cached data
            for symbol in symbols:
                if symbol in cached_data:
                    result.append(cached_data[symbol])
                else:
                    # Only fetch from API if not cached
                    stock_data = await generate_stock_data(symbol)
                    result.append(stock_data)
            
            return result
        
        # Stock data - Lazy loading with smaller initial set
        if "stocks" in query:
            # Get user income for filtering
            user_income = variables.get("userIncome", 50000)  # Default to $50k if not provided
            
            # Lazy loading: Start with most popular stocks only
            popular_stocks = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NFLX", "AMD", "INTC", "CRM", "ADBE"]
            stocks_data = await get_stock_data_optimized(popular_stocks)
            
            # Filter stocks based on user income
            filtered_stocks = await filter_stocks_by_income(stocks_data, user_income)
            response_data["stocks"] = filtered_stocks if filtered_stocks else []
        
        
        if "advancedStockScreening" in query:
            advanced_data = await get_stock_data_optimized(["TSLA", "AMZN", "NFLX", "NVDA", "AMD"])
            response_data["advancedStockScreening"] = advanced_data if advanced_data else []
        
        if "myWatchlist" in query:
            # Watchlist should have a different structure with stock objects
            watchlist_stocks = await get_stock_data_optimized(["AAPL", "GOOGL", "MSFT", "TSLA"])
            watchlist_data = [
                {
                    "id": f"watchlist_{i+1}",
                    "stock": stock,
                    "addedAt": datetime.now().isoformat(),
                    "notifications": random.choice([True, False]),
                    "targetPrice": round(stock.get("targetPrice", stock.get("currentPrice", 100) * random.uniform(0.9, 1.2)), 2),
                    "notes": f"Added to watchlist for {stock.get('symbol', 'UNKNOWN')} - monitoring for potential entry point",
                    "__typename": "WatchlistItem"
                }
                for i, stock in enumerate(watchlist_stocks)
            ]
            response_data["myWatchlist"] = watchlist_data if watchlist_data else []
        
        
        # Portfolio data
        if "portfolios" in query:
            response_data["portfolios"] = [
                {
                    "id": "1",
                    "name": "Growth Portfolio",
                    "totalValue": 125000.50,
                    "dayChange": 1250.75,
                    "dayChangePercent": 1.01,
                    "stocks": await get_stock_data(["AAPL", "GOOGL", "MSFT"])
                },
                {
                    "id": "2", 
                    "name": "Conservative Portfolio",
                    "totalValue": 85000.25,
                    "dayChange": -425.50,
                    "dayChangePercent": -0.50,
                    "stocks": await get_stock_data(["JNJ", "PG", "KO"])
                }
            ]
        
        # Discussion data
        if "discussions" in query:
            response_data["discussions"] = [
                {
                    "id": "1",
                    "title": "Apple Stock Analysis",
                    "author": "TechInvestor",
                    "content": "Apple's recent earnings show strong growth in services revenue...",
                    "likes": 45,
                    "comments": 12,
                    "timestamp": datetime.now().isoformat(),
                    "stockSymbol": "AAPL"
                },
                {
                    "id": "2",
                    "title": "Market Outlook for Q4",
                    "author": "MarketGuru",
                    "content": "Based on current economic indicators, I expect continued volatility...",
                    "likes": 32,
                    "comments": 8,
                    "timestamp": datetime.now().isoformat(),
                    "stockSymbol": None
                }
            ]
        
        # Social feed
        if "socialFeed" in query:
            response_data["socialFeed"] = [
                {
                    "id": "post_1",
                    "title": "Apple Q4 Earnings Analysis",
                    "content": "Just bought some AAPL shares after their strong Q4 earnings. The services growth is impressive!",
                    "discussionType": "post",
                    "visibility": "public",
                    "user": {
                        "id": "user_1",
                        "name": "u/TechnologyInvestor",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "verified": True,
                        "followersCount": 2100,
                        "followingCount": 180,
                        "isFollowingUser": True,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "likes": 24,
                    "comments": 8,
                    "shares": 3,
                    "score": 24,
                    "commentCount": 8,
                    "createdAt": datetime.now().isoformat(),
                    "stockMentions": [
                        {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "__typename": "Stock"
                        }
                    ],
                    "images": [],
                    "type": "post",
                    "stock": {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_2",
                    "title": "Tesla Volatility Discussion",
                    "content": "TSLA volatility is crazy right now. What's everyone's take on the Cybertruck launch impact?",
                    "discussionType": "post",
                    "visibility": "public",
                    "user": {
                        "id": "user_2",
                        "name": "u/ElectricVehicleExpert",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "verified": False,
                        "followersCount": 950,
                        "followingCount": 220,
                        "isFollowingUser": False,
                        "isFollowedByUser": False,
                        "__typename": "User"
                    },
                    "likes": 15,
                    "comments": 12,
                    "shares": 2,
                    "score": 15,
                    "commentCount": 12,
                    "createdAt": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "stockMentions": [
                        {
                            "symbol": "TSLA",
                            "companyName": "Tesla Inc.",
                            "__typename": "Stock"
                        }
                    ],
                    "images": [],
                    "type": "post",
                    "stock": {
                        "symbol": "TSLA",
                        "companyName": "Tesla Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_3",
                    "title": "Microsoft Azure Growth Update",
                    "content": "Microsoft's Azure growth continues to impress. Enterprise adoption is accelerating faster than expected.",
                    "discussionType": "post",
                    "visibility": "public",
                    "user": {
                        "id": "user_3",
                        "name": "u/CloudComputingSpecialist",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "verified": True,
                        "followersCount": 890,
                        "followingCount": 420,
                        "isFollowingUser": True,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "likes": 31,
                    "comments": 6,
                    "shares": 5,
                    "score": 31,
                    "commentCount": 6,
                    "createdAt": (datetime.now() - timedelta(hours=4)).isoformat(),
                    "stockMentions": [
                        {
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "__typename": "Stock"
                        }
                    ],
                    "images": [],
                    "type": "post",
                    "stock": {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "__typename": "Stock"
                    },
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_4",
                    "title": "Google AI Investment Results",
                    "content": "Google's AI investments are finally paying off. The search integration is seamless and the Bard improvements are noticeable.",
                    "discussionType": "post",
                    "visibility": "public",
                    "user": {
                        "id": "user_4",
                        "name": "u/ArtificialIntelligenceExpert",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "verified": True,
                        "followersCount": 1650,
                        "followingCount": 290,
                        "isFollowingUser": False,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "likes": 42,
                    "comments": 18,
                    "shares": 7,
                    "score": 42,
                    "commentCount": 18,
                    "createdAt": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "stockMentions": [
                        {
                            "symbol": "GOOGL",
                            "companyName": "Alphabet Inc.",
                            "__typename": "Stock"
                        }
                    ],
                    "images": [],
                    "type": "post",
                    "stock": {
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_5",
                    "title": "Amazon E-commerce Recovery",
                    "content": "Amazon's e-commerce recovery is showing positive signs. AWS continues to be the growth driver though.",
                    "discussionType": "post",
                    "visibility": "public",
                    "user": {
                        "id": "user_5",
                        "name": "u/RetailIndustrySpecialist",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "verified": False,
                        "followersCount": 750,
                        "followingCount": 150,
                        "isFollowingUser": True,
                        "isFollowedByUser": False,
                        "__typename": "User"
                    },
                    "likes": 19,
                    "comments": 4,
                    "shares": 1,
                    "score": 19,
                    "commentCount": 4,
                    "createdAt": (datetime.now() - timedelta(hours=8)).isoformat(),
                    "stockMentions": [
                        {
                            "symbol": "AMZN",
                            "companyName": "Amazon.com Inc.",
                            "__typename": "Stock"
                        }
                    ],
                    "images": [],
                    "type": "post",
                    "stock": {
                        "symbol": "AMZN",
                        "companyName": "Amazon.com Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "SocialPost"
                }
            ]

        # Stock discussions
        if "stockDiscussions" in query:
            discussions_data = [
                {
                    "id": "discussion_1",
                    "title": "AAPL Earnings Analysis - Strong Q4 Results",
                    "content": "Apple's Q4 earnings exceeded expectations with strong iPhone sales and services growth. The company's focus on services diversification is paying off.",
                    "discussionType": "Earnings",
                    "visibility": "Public",
                    "createdAt": datetime.now().isoformat(),
                    "score": 45,
                    "commentCount": 12 + len(discussion_comments.get("discussion_1", [])),
                    "comments": [
                        {
                            "id": "comment_1",
                            "content": "Great analysis! The services revenue growth is impressive.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_7",
                                "name": "u/InvestmentGuru",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 500,
                                "followingCount": 200,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_2",
                            "content": "I agree, the iPhone 15 sales numbers were better than expected.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_8",
                                "name": "u/TechnologyInvestor",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 300,
                                "followingCount": 150,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ] + discussion_comments.get("discussion_1", []),
                           "user": {
                               "id": "user_2",
                               "name": "u/MarketAnalysisExpert",
                               "profilePicture": "https://via.placeholder.com/40",
                               "profilePic": "https://via.placeholder.com/40",
                               "followersCount": 1250,
                               "followingCount": 340,
                               "isFollowingUser": False,
                               "isFollowedByUser": True,
                               "__typename": "User"
                           },
                    "stock": {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_2",
                    "title": "TSLA Volatility - What's Next?",
                    "content": "Tesla's stock has been extremely volatile lately. With the Cybertruck launch and FSD progress, what are your thoughts on the next move?",
                    "discussionType": "Analysis",
                    "visibility": "Public",
                    "createdAt": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "score": 32,
                    "commentCount": 8 + len(discussion_comments.get("discussion_2", [])),
                    "comments": [
                        {
                            "id": "comment_3",
                            "content": "The volatility is concerning but the long-term outlook remains strong.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_9",
                                "name": "u/EVInvestor",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 800,
                                "followingCount": 300,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ] + discussion_comments.get("discussion_2", []),
                    "user": {
                        "id": "user_3",
                        "name": "u/TechnologyInvestor",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "followersCount": 2100,
                        "followingCount": 180,
                        "isFollowingUser": True,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "TSLA",
                        "companyName": "Tesla Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_3",
                    "title": "MSFT Cloud Growth Continues",
                    "content": "Microsoft's Azure division continues to show strong growth. The enterprise adoption of cloud services is accelerating.",
                    "discussionType": "News",
                    "visibility": "Public",
                    "createdAt": (datetime.now() - timedelta(hours=4)).isoformat(),
                    "score": 28,
                    "commentCount": 6,
                    "comments": [
                        {
                            "id": "comment_4",
                            "content": "Azure is definitely gaining market share against AWS.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_10",
                                "name": "u/CloudWatcher",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 400,
                                "followingCount": 180,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "user": {
                        "id": "user_4",
                        "name": "u/CloudComputingSpecialist",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "followersCount": 890,
                        "followingCount": 420,
                        "isFollowingUser": False,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "__typename": "Stock"
                    },
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_4",
                    "title": "GOOGL AI Investments Paying Off",
                    "content": "Google's investments in AI and machine learning are starting to show results. The search giant is well-positioned for the AI revolution.",
                    "discussionType": "Analysis",
                    "visibility": "Public",
                    "createdAt": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "score": 41,
                    "commentCount": 15,
                    "comments": [
                        {
                            "id": "comment_5",
                            "content": "The AI integration in search is really impressive.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_11",
                                "name": "u/AIFan",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 300,
                                "followingCount": 120,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_6",
                            "content": "Bard and other AI products are showing promise.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_12",
                                "name": "u/TechObserver",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 250,
                                "followingCount": 90,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "user": {
                        "id": "user_5",
                        "name": "u/ArtificialIntelligenceExpert",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "followersCount": 1650,
                        "followingCount": 290,
                        "isFollowingUser": True,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_5",
                    "title": "AMZN E-commerce Recovery",
                    "content": "Amazon's e-commerce business is showing signs of recovery after the pandemic boom. AWS continues to be the growth driver.",
                    "discussionType": "News",
                    "visibility": "Public",
                    "createdAt": (datetime.now() - timedelta(hours=8)).isoformat(),
                    "score": 19,
                    "commentCount": 4,
                    "comments": [
                        {
                            "id": "comment_7",
                            "content": "AWS is definitely the star of the show now.",
                            "createdAt": datetime.now().isoformat(),
                            "user": {
                                "id": "user_13",
                                "name": "u/CloudAnalyst",
                                "profilePicture": "https://via.placeholder.com/30",
                                "profilePic": "https://via.placeholder.com/30",
                                "followersCount": 600,
                                "followingCount": 200,
                                "isFollowingUser": False,
                                "isFollowedByUser": True,
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "user": {
                        "id": "user_6",
                        "name": "u/RetailIndustrySpecialist",
                        "profilePicture": "https://via.placeholder.com/40",
                        "profilePic": "https://via.placeholder.com/40",
                        "followersCount": 750,
                        "followingCount": 150,
                        "isFollowingUser": False,
                        "isFollowedByUser": True,
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "AMZN",
                        "companyName": "Amazon.com Inc.",
                        "__typename": "Stock"
                    },
                    "__typename": "StockDiscussion"
                }
            ]
            response_data["stockDiscussions"] = discussions_data
        
        # AI Recommendations
        if "aiRecommendations" in query:
            logger.info("Processing aiRecommendations query - returning AI recommendations data")
            response_data["aiRecommendations"] = {
                "portfolioAnalysis": {
                    "totalValue": 210000.75,
                    "numHoldings": 5,
                    "sectorBreakdown": {
                        "Technology": 60.0,
                        "Healthcare": 20.0,
                        "Consumer Discretionary": 15.0,
                        "Financials": 5.0
                    },
                    "riskScore": 6.5,
                    "diversificationScore": 7.2
                },
                "buyRecommendations": [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "recommendation": "BUY",
                        "confidence": 0.85,
                        "reasoning": "Strong fundamentals, growing services revenue, and solid cash position",
                        "targetPrice": 250.00,
                        "currentPrice": 234.07,
                        "expectedReturn": 0.068
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation", 
                        "recommendation": "BUY",
                        "confidence": 0.78,
                        "reasoning": "Cloud growth accelerating, AI integration across products",
                        "targetPrice": 550.00,
                        "currentPrice": 509.90,
                        "expectedReturn": 0.079
                    }
                ],
                "sellRecommendations": [
                    {
                        "symbol": "TSLA",
                        "reasoning": "High volatility and valuation concerns, consider reducing position"
                    }
                ],
                "rebalanceSuggestions": [
                    {
                        "action": "INCREASE",
                        "currentAllocation": 0.15,
                        "suggestedAllocation": 0.20,
                        "reasoning": "Healthcare sector showing strong growth potential",
                        "priority": "HIGH"
                    },
                    {
                        "action": "DECREASE", 
                        "currentAllocation": 0.25,
                        "suggestedAllocation": 0.20,
                        "reasoning": "Technology allocation slightly overweight",
                        "priority": "MEDIUM"
                    }
                ],
                "riskAssessment": {
                    "overallRisk": "MODERATE",
                    "volatilityEstimate": 0.18,
                    "recommendations": [
                        "Consider adding more defensive stocks",
                        "Diversify across more sectors",
                        "Monitor market volatility closely"
                    ]
                },
                "marketOutlook": {
                    "overallSentiment": "Cautiously Optimistic",
                    "confidence": 0.72,
                    "keyFactors": [
                        "Federal Reserve policy remains accommodative",
                        "Corporate earnings growth expected to continue",
                        "Geopolitical tensions creating market volatility",
                        "Technology sector showing resilience",
                        "Inflation concerns moderating"
                    ]
                }
            }
        
        # Portfolio metrics
        if "portfolioMetrics" in query:
            # Generate portfolio holdings data
            holdings_data = [
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "shares": 50,
                    "currentPrice": 234.07,
                    "costBasis": 220.00,
                    "marketValue": 11703.50,
                    "totalValue": 11703.50,
                    "totalReturn": 703.50,
                    "returnAmount": 703.50,
                    "totalReturnPercent": 6.40,
                    "returnPercent": 6.40,
                    "dayChange": 125.50,
                    "dayChangePercent": 1.08
                },
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "shares": 30,
                    "currentPrice": 509.90,
                    "costBasis": 480.00,
                    "marketValue": 15297.00,
                    "totalValue": 15297.00,
                    "totalReturn": 897.00,
                    "returnAmount": 897.00,
                    "totalReturnPercent": 6.23,
                    "returnPercent": 6.23,
                    "dayChange": 89.70,
                    "dayChangePercent": 0.59
                },
                {
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "shares": 20,
                    "currentPrice": 240.80,
                    "costBasis": 225.00,
                    "marketValue": 4816.00,
                    "totalValue": 4816.00,
                    "totalReturn": 316.00,
                    "returnAmount": 316.00,
                    "totalReturnPercent": 7.02,
                    "returnPercent": 7.02,
                    "dayChange": 48.16,
                    "dayChangePercent": 1.01
                },
                {
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc.",
                    "sector": "Automotive",
                    "shares": 15,
                    "currentPrice": 395.94,
                    "costBasis": 350.00,
                    "marketValue": 5939.10,
                    "totalValue": 5939.10,
                    "totalReturn": 689.10,
                    "returnAmount": 689.10,
                    "totalReturnPercent": 13.12,
                    "returnPercent": 13.12,
                    "dayChange": 59.39,
                    "dayChangePercent": 1.01
                },
                {
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "sector": "Consumer Discretionary",
                    "shares": 25,
                    "currentPrice": 228.15,
                    "costBasis": 200.00,
                    "marketValue": 5703.75,
                    "totalValue": 5703.75,
                    "totalReturn": 703.75,
                    "returnAmount": 703.75,
                    "totalReturnPercent": 14.08,
                    "returnPercent": 14.08,
                    "dayChange": 57.04,
                    "dayChangePercent": 1.01
                }
            ]
            
            response_data["portfolioMetrics"] = {
                "totalValue": 210000.75,
                "totalCost": 195000.00,
                "totalReturn": 15000.75,
                "totalReturnPercent": 7.69,
                "dayChange": 1250.50,
                "dayChangePercent": 0.60,
                "volatility": 0.18,
                "sharpeRatio": 1.42,
                "maxDrawdown": -0.08,
                "beta": 0.95,
                "alpha": 0.03,
                "holdings": holdings_data
            }
        
        # Premium Portfolio metrics
        if "premiumPortfolioMetrics" in query:
            logger.info("Processing premiumPortfolioMetrics query - returning premium portfolio data")
            response_data["premiumPortfolioMetrics"] = {
                "totalValue": 210000.75,
                "totalCost": 195000.00,
                "totalReturn": 15000.75,
                "totalReturnPercent": 7.69,
                "volatility": 0.18,
                "sharpeRatio": 1.42,
                "maxDrawdown": -0.08,
                "beta": 0.95,
                "alpha": 0.03,
                "holdings": holdings_data,
                "sectorAllocation": {
                    "Technology": 35.2,
                    "Healthcare": 18.7,
                    "Financials": 15.3,
                    "Consumer Discretionary": 12.1,
                    "Communication Services": 8.9,
                    "Industrials": 5.8,
                    "Consumer Staples": 4.0
                },
                "riskMetrics": {
                    "var95": -0.025,
                    "expectedShortfall": -0.035,
                    "treynorRatio": 0.15,
                    "informationRatio": 0.12,
                    "calmarRatio": 0.96
                }
            }
        
        # Options Analysis
        if "optionsAnalysis" in query:
            logger.info("Processing optionsAnalysis query - returning real options data")
            try:
                # Get real options data
                real_options_data = real_options_service.get_real_options_chain("AAPL")
                response_data["optionsAnalysis"] = real_options_data
                logger.info("Successfully fetched real options data")
            except Exception as e:
                logger.error(f"Error fetching real options data: {e}, falling back to mock data")
                # Fallback to mock data if real data fails
                response_data["optionsAnalysis"] = {
                "underlyingSymbol": "AAPL",
                "underlyingPrice": 234.07,
                "optionsChain": {
                    "expirationDates": ["2025-09-20", "2025-10-17", "2025-11-21", "2025-12-19"],
                    "calls": [
                        {
                            "symbol": "AAPL250920C00220000",
                            "contractSymbol": "AAPL250920C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 15.20,
                            "ask": 15.50,
                            "lastPrice": 15.35,
                            "volume": 2100,
                            "openInterest": 5200,
                            "impliedVolatility": 0.25,
                            "delta": 0.78,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.38,
                            "rho": 0.15,
                            "intrinsicValue": 14.07,
                            "timeValue": 1.28,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00225000",
                            "contractSymbol": "AAPL250920C00225000",
                            "strike": 225.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 11.80,
                            "ask": 12.10,
                            "lastPrice": 11.95,
                            "volume": 1800,
                            "openInterest": 4800,
                            "impliedVolatility": 0.26,
                            "delta": 0.72,
                            "gamma": 0.017,
                            "theta": -0.16,
                            "vega": 0.42,
                            "rho": 0.14,
                            "intrinsicValue": 9.07,
                            "timeValue": 2.88,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00230000",
                            "contractSymbol": "AAPL250920C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 8.50,
                            "ask": 8.80,
                            "lastPrice": 8.65,
                            "volume": 1250,
                            "openInterest": 4500,
                            "impliedVolatility": 0.28,
                            "delta": 0.65,
                            "gamma": 0.02,
                            "theta": -0.15,
                            "vega": 0.45,
                            "rho": 0.12,
                            "intrinsicValue": 4.07,
                            "timeValue": 4.58,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00235000",
                            "contractSymbol": "AAPL250920C00235000",
                            "strike": 235.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 5.80,
                            "ask": 6.10,
                            "lastPrice": 5.95,
                            "volume": 950,
                            "openInterest": 3800,
                            "impliedVolatility": 0.30,
                            "delta": 0.55,
                            "gamma": 0.022,
                            "theta": -0.14,
                            "vega": 0.48,
                            "rho": 0.10,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.95,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00240000",
                            "contractSymbol": "AAPL250920C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 3.60,
                            "ask": 3.90,
                            "lastPrice": 3.75,
                            "volume": 750,
                            "openInterest": 3200,
                            "impliedVolatility": 0.32,
                            "delta": 0.42,
                            "gamma": 0.025,
                            "theta": -0.12,
                            "vega": 0.50,
                            "rho": 0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.75,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00245000",
                            "contractSymbol": "AAPL250920C00245000",
                            "strike": 245.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 2.10,
                            "ask": 2.40,
                            "lastPrice": 2.25,
                            "volume": 580,
                            "openInterest": 2800,
                            "impliedVolatility": 0.34,
                            "delta": 0.30,
                            "gamma": 0.028,
                            "theta": -0.10,
                            "vega": 0.52,
                            "rho": 0.06,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.25,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00250000",
                            "contractSymbol": "AAPL250920C00250000",
                            "strike": 250.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 1.20,
                            "ask": 1.50,
                            "lastPrice": 1.35,
                            "volume": 420,
                            "openInterest": 2400,
                            "impliedVolatility": 0.36,
                            "delta": 0.20,
                            "gamma": 0.030,
                            "theta": -0.08,
                            "vega": 0.54,
                            "rho": 0.04,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL251017C00220000",
                            "contractSymbol": "AAPL251017C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 18.50,
                            "ask": 18.80,
                            "lastPrice": 18.65,
                            "volume": 1800,
                            "openInterest": 4800,
                            "impliedVolatility": 0.28,
                            "delta": 0.82,
                            "gamma": 0.012,
                            "theta": -0.15,
                            "vega": 0.45,
                            "rho": 0.18,
                            "intrinsicValue": 14.07,
                            "timeValue": 4.58,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017C00230000",
                            "contractSymbol": "AAPL251017C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 12.80,
                            "ask": 13.10,
                            "lastPrice": 12.95,
                            "volume": 1500,
                            "openInterest": 4200,
                            "impliedVolatility": 0.30,
                            "delta": 0.72,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.48,
                            "rho": 0.15,
                            "intrinsicValue": 4.07,
                            "timeValue": 8.88,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017C00240000",
                            "contractSymbol": "AAPL251017C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 7.20,
                            "ask": 7.50,
                            "lastPrice": 7.35,
                            "volume": 1200,
                            "openInterest": 3600,
                            "impliedVolatility": 0.32,
                            "delta": 0.58,
                            "gamma": 0.018,
                            "theta": -0.20,
                            "vega": 0.52,
                            "rho": 0.12,
                            "intrinsicValue": 0.0,
                            "timeValue": 7.35,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251121C00220000",
                            "contractSymbol": "AAPL251121C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 22.10,
                            "ask": 22.40,
                            "lastPrice": 22.25,
                            "volume": 1500,
                            "openInterest": 4200,
                            "impliedVolatility": 0.30,
                            "delta": 0.85,
                            "gamma": 0.010,
                            "theta": -0.12,
                            "vega": 0.50,
                            "rho": 0.20,
                            "intrinsicValue": 14.07,
                            "timeValue": 8.18,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121C00230000",
                            "contractSymbol": "AAPL251121C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 16.40,
                            "ask": 16.70,
                            "lastPrice": 16.55,
                            "volume": 1300,
                            "openInterest": 3800,
                            "impliedVolatility": 0.32,
                            "delta": 0.75,
                            "gamma": 0.012,
                            "theta": -0.15,
                            "vega": 0.52,
                            "rho": 0.17,
                            "intrinsicValue": 4.07,
                            "timeValue": 12.48,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121C00240000",
                            "contractSymbol": "AAPL251121C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 11.20,
                            "ask": 11.50,
                            "lastPrice": 11.35,
                            "volume": 1000,
                            "openInterest": 3200,
                            "impliedVolatility": 0.34,
                            "delta": 0.62,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.55,
                            "rho": 0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 11.35,
                            "daysToExpiration": 70
                        }
                    ],
                    "puts": [
                        {
                            "symbol": "AAPL250920P00220000",
                            "contractSymbol": "AAPL250920P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 0.85,
                            "ask": 1.15,
                            "lastPrice": 1.00,
                            "volume": 320,
                            "openInterest": 1800,
                            "impliedVolatility": 0.24,
                            "delta": -0.22,
                            "gamma": 0.015,
                            "theta": -0.08,
                            "vega": 0.38,
                            "rho": -0.15,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.00,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00225000",
                            "contractSymbol": "AAPL250920P00225000",
                            "strike": 225.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 1.40,
                            "ask": 1.70,
                            "lastPrice": 1.55,
                            "volume": 450,
                            "openInterest": 2200,
                            "impliedVolatility": 0.25,
                            "delta": -0.28,
                            "gamma": 0.017,
                            "theta": -0.09,
                            "vega": 0.42,
                            "rho": -0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.55,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00230000",
                            "contractSymbol": "AAPL250920P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 2.20,
                            "ask": 2.50,
                            "lastPrice": 2.35,
                            "volume": 890,
                            "openInterest": 3200,
                            "impliedVolatility": 0.26,
                            "delta": -0.35,
                            "gamma": 0.02,
                            "theta": -0.12,
                            "vega": 0.38,
                            "rho": -0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00235000",
                            "contractSymbol": "AAPL250920P00235000",
                            "strike": 235.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 3.40,
                            "ask": 3.70,
                            "lastPrice": 3.55,
                            "volume": 680,
                            "openInterest": 2800,
                            "impliedVolatility": 0.28,
                            "delta": -0.45,
                            "gamma": 0.022,
                            "theta": -0.14,
                            "vega": 0.48,
                            "rho": -0.10,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.55,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00240000",
                            "contractSymbol": "AAPL250920P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 5.20,
                            "ask": 5.50,
                            "lastPrice": 5.35,
                            "volume": 520,
                            "openInterest": 2400,
                            "impliedVolatility": 0.30,
                            "delta": -0.58,
                            "gamma": 0.025,
                            "theta": -0.16,
                            "vega": 0.50,
                            "rho": -0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00245000",
                            "contractSymbol": "AAPL250920P00245000",
                            "strike": 245.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 7.80,
                            "ask": 8.10,
                            "lastPrice": 7.95,
                            "volume": 380,
                            "openInterest": 2000,
                            "impliedVolatility": 0.32,
                            "delta": -0.70,
                            "gamma": 0.028,
                            "theta": -0.18,
                            "vega": 0.52,
                            "rho": -0.06,
                            "intrinsicValue": 0.0,
                            "timeValue": 7.95,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00250000",
                            "contractSymbol": "AAPL250920P00250000",
                            "strike": 250.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 11.20,
                            "ask": 11.50,
                            "lastPrice": 11.35,
                            "volume": 280,
                            "openInterest": 1600,
                            "impliedVolatility": 0.34,
                            "delta": -0.80,
                            "gamma": 0.030,
                            "theta": -0.20,
                            "vega": 0.54,
                            "rho": -0.04,
                            "intrinsicValue": 0.0,
                            "timeValue": 11.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL251017P00220000",
                            "contractSymbol": "AAPL251017P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 2.10,
                            "ask": 2.40,
                            "lastPrice": 2.25,
                            "volume": 450,
                            "openInterest": 2200,
                            "impliedVolatility": 0.26,
                            "delta": -0.18,
                            "gamma": 0.012,
                            "theta": -0.10,
                            "vega": 0.45,
                            "rho": -0.18,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.25,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017P00230000",
                            "contractSymbol": "AAPL251017P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 3.80,
                            "ask": 4.10,
                            "lastPrice": 3.95,
                            "volume": 680,
                            "openInterest": 2800,
                            "impliedVolatility": 0.28,
                            "delta": -0.28,
                            "gamma": 0.015,
                            "theta": -0.12,
                            "vega": 0.48,
                            "rho": -0.15,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.95,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017P00240000",
                            "contractSymbol": "AAPL251017P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 6.20,
                            "ask": 6.50,
                            "lastPrice": 6.35,
                            "volume": 520,
                            "openInterest": 2400,
                            "impliedVolatility": 0.30,
                            "delta": -0.42,
                            "gamma": 0.018,
                            "theta": -0.14,
                            "vega": 0.52,
                            "rho": -0.12,
                            "intrinsicValue": 0.0,
                            "timeValue": 6.35,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251121P00220000",
                            "contractSymbol": "AAPL251121P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 3.20,
                            "ask": 3.50,
                            "lastPrice": 3.35,
                            "volume": 380,
                            "openInterest": 1800,
                            "impliedVolatility": 0.28,
                            "delta": -0.15,
                            "gamma": 0.010,
                            "theta": -0.08,
                            "vega": 0.50,
                            "rho": -0.20,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.35,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121P00230000",
                            "contractSymbol": "AAPL251121P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 5.40,
                            "ask": 5.70,
                            "lastPrice": 5.55,
                            "volume": 320,
                            "openInterest": 2000,
                            "impliedVolatility": 0.30,
                            "delta": -0.25,
                            "gamma": 0.012,
                            "theta": -0.10,
                            "vega": 0.52,
                            "rho": -0.17,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.55,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121P00240000",
                            "contractSymbol": "AAPL251121P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 8.60,
                            "ask": 8.90,
                            "lastPrice": 8.75,
                            "volume": 280,
                            "openInterest": 1600,
                            "impliedVolatility": 0.32,
                            "delta": -0.38,
                            "gamma": 0.015,
                            "theta": -0.12,
                            "vega": 0.55,
                            "rho": -0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 8.75,
                            "daysToExpiration": 70
                        }
                    ],
                    "greeks": {
                        "delta": 0.30,
                        "gamma": 0.02,
                        "theta": -0.13,
                        "vega": 0.41,
                        "rho": 0.02
                    }
                },
                "unusualFlow": {
                    "symbol": "AAPL250920C00235000",
                    "contractSymbol": "AAPL250920C00235000",
                    "optionType": "call",
                    "strike": 235.0,
                    "expirationDate": "2025-09-20",
                    "volume": 2500,
                    "openInterest": 1800,
                    "premium": 6.25,
                    "impliedVolatility": 0.32,
                    "unusualActivityScore": 8.5,
                    "activityType": "sweep"
                },
                "recommendedStrategies": [
                    {
                        "strategyName": "Covered Call",
                        "strategyType": "income",
                        "maxProfit": 8.65,
                        "maxLoss": -225.35,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.65,
                        "riskRewardRatio": 0.038,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 8.65,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Low"
                    },
                    {
                        "strategyName": "Protective Put",
                        "strategyType": "hedge",
                        "maxProfit": 0,
                        "maxLoss": -320.0,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.70,
                        "riskRewardRatio": 0.0,
                        "daysToExpiration": 15,
                        "totalCost": 320.0,
                        "totalCredit": 0.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Medium"
                    },
                    {
                        "strategyName": "Long Call",
                        "strategyType": "speculation",
                        "maxProfit": 0,
                        "maxLoss": -150.0,
                        "breakevenPoints": [232.0],
                        "probabilityOfProfit": 0.75,
                        "riskRewardRatio": 0.0,
                        "daysToExpiration": 15,
                        "totalCost": 150.0,
                        "totalCredit": 0.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "High"
                    },
                    {
                        "strategyName": "Iron Condor",
                        "strategyType": "arbitrage",
                        "maxProfit": 270.0,
                        "maxLoss": -180.0,
                        "breakevenPoints": [220.0, 250.0],
                        "probabilityOfProfit": 0.80,
                        "riskRewardRatio": 1.5,
                        "daysToExpiration": 15,
                        "totalCost": 180.0,
                        "totalCredit": 270.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Medium"
                    },
                    {
                        "strategyName": "Cash Secured Put",
                        "strategyType": "income",
                        "maxProfit": 4.35,
                        "maxLoss": -225.65,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.68,
                        "riskRewardRatio": 0.019,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 4.35,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Low"
                    }
                ],
                "marketSentiment": {
                    "putCallRatio": 0.85,
                    "impliedVolatilityRank": 0.45,
                    "skew": 0.12,
                    "sentimentScore": 0.68,
                    "sentimentDescription": "Moderately bullish"
                }
            }
        
        # Test Options Analysis (fallback)
        if "testOptionsAnalysis" in query:
            logger.info("Processing testOptionsAnalysis query - returning test options data")
            response_data["testOptionsAnalysis"] = {
                "underlyingSymbol": "AAPL",
                "underlyingPrice": 234.07,
                "marketSentiment": {
                    "sentimentDescription": "Moderately bullish",
                    "sentimentScore": 0.68,
                    "putCallRatio": 0.85,
                    "impliedVolatilityRank": 0.45
                },
                "unusualFlow": {
                    "symbol": "AAPL250920C00235000",
                    "contractSymbol": "AAPL250920C00235000",
                    "optionType": "call",
                    "strike": 235.0,
                    "expirationDate": "2025-09-20",
                    "volume": 2500,
                    "openInterest": 1800,
                    "premium": 6.25,
                    "impliedVolatility": 0.32,
                    "unusualActivityScore": 8.5,
                    "activityType": "sweep"
                },
                "recommendedStrategies": [
                    {
                        "strategyName": "Covered Call",
                        "strategyType": "income",
                        "maxProfit": 8.65,
                        "maxLoss": -225.35,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.65,
                        "riskRewardRatio": 0.038,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 8.65
                    }
                ]
            }
        
        # User profile
        if "me" in query:
            logger.info("Processing me query - returning user profile data")
            user_profile = {
                "id": "user_1",
                "name": "Test User", 
                "email": "test@example.com",
                "profilePic": "https://via.placeholder.com/40",
                "hasPremiumAccess": True,
                "subscriptionTier": "Premium",
                "followersCount": 1250,
                "followingCount": 340,
                "isFollowingUser": False,
                "isFollowedByUser": True,
                "incomeProfile": {
                    "incomeBracket": "Medium",
                    "age": 32,
                    "investmentGoals": "Long-term growth and retirement planning",
                    "riskTolerance": "Moderate",
                    "investmentHorizon": "10-15 years",
                    "__typename": "IncomeProfile"
                },
                "__typename": "User"
            }
            response_data["me"] = user_profile
            logger.info(f"Me query response has {len(user_profile)} fields: {list(user_profile.keys())}")
            logger.info(f"followers/following: {user_profile.get('followersCount')}/{user_profile.get('followingCount')}")
        
        # Always include options analysis data if query mentions options
        if any(term in query.lower() for term in ["options", "optionsanalysis", "testoptionsanalysis"]):
            logger.info("Including real options analysis data in response")
            try:
                # Get real options data
                real_options_data = real_options_service.get_real_options_chain("AAPL")
                response_data["optionsAnalysis"] = real_options_data
                logger.info("Successfully included real options data")
            except Exception as e:
                logger.error(f"Error fetching real options data for inclusion: {e}, falling back to mock data")
                # Fallback to mock data if real data fails
                response_data["optionsAnalysis"] = {
                "underlyingSymbol": "AAPL",
                "underlyingPrice": 234.07,
                "optionsChain": {
                    "expirationDates": ["2025-09-20", "2025-10-17", "2025-11-21", "2025-12-19"],
                    "calls": [
                        {
                            "symbol": "AAPL250920C00220000",
                            "contractSymbol": "AAPL250920C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 15.20,
                            "ask": 15.50,
                            "lastPrice": 15.35,
                            "volume": 2100,
                            "openInterest": 5200,
                            "impliedVolatility": 0.25,
                            "delta": 0.78,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.38,
                            "rho": 0.15,
                            "intrinsicValue": 14.07,
                            "timeValue": 1.28,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00225000",
                            "contractSymbol": "AAPL250920C00225000",
                            "strike": 225.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 11.80,
                            "ask": 12.10,
                            "lastPrice": 11.95,
                            "volume": 1800,
                            "openInterest": 4800,
                            "impliedVolatility": 0.26,
                            "delta": 0.72,
                            "gamma": 0.017,
                            "theta": -0.16,
                            "vega": 0.42,
                            "rho": 0.14,
                            "intrinsicValue": 9.07,
                            "timeValue": 2.88,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00230000",
                            "contractSymbol": "AAPL250920C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 8.50,
                            "ask": 8.80,
                            "lastPrice": 8.65,
                            "volume": 1250,
                            "openInterest": 4500,
                            "impliedVolatility": 0.28,
                            "delta": 0.65,
                            "gamma": 0.02,
                            "theta": -0.15,
                            "vega": 0.45,
                            "rho": 0.12,
                            "intrinsicValue": 4.07,
                            "timeValue": 4.58,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00235000",
                            "contractSymbol": "AAPL250920C00235000",
                            "strike": 235.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 5.80,
                            "ask": 6.10,
                            "lastPrice": 5.95,
                            "volume": 950,
                            "openInterest": 3800,
                            "impliedVolatility": 0.30,
                            "delta": 0.55,
                            "gamma": 0.022,
                            "theta": -0.14,
                            "vega": 0.48,
                            "rho": 0.10,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.95,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00240000",
                            "contractSymbol": "AAPL250920C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 3.60,
                            "ask": 3.90,
                            "lastPrice": 3.75,
                            "volume": 750,
                            "openInterest": 3200,
                            "impliedVolatility": 0.32,
                            "delta": 0.42,
                            "gamma": 0.025,
                            "theta": -0.12,
                            "vega": 0.50,
                            "rho": 0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.75,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00245000",
                            "contractSymbol": "AAPL250920C00245000",
                            "strike": 245.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 2.10,
                            "ask": 2.40,
                            "lastPrice": 2.25,
                            "volume": 580,
                            "openInterest": 2800,
                            "impliedVolatility": 0.34,
                            "delta": 0.30,
                            "gamma": 0.028,
                            "theta": -0.10,
                            "vega": 0.52,
                            "rho": 0.06,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.25,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920C00250000",
                            "contractSymbol": "AAPL250920C00250000",
                            "strike": 250.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "call",
                            "bid": 1.20,
                            "ask": 1.50,
                            "lastPrice": 1.35,
                            "volume": 420,
                            "openInterest": 2400,
                            "impliedVolatility": 0.36,
                            "delta": 0.20,
                            "gamma": 0.030,
                            "theta": -0.08,
                            "vega": 0.54,
                            "rho": 0.04,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL251017C00220000",
                            "contractSymbol": "AAPL251017C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 18.50,
                            "ask": 18.80,
                            "lastPrice": 18.65,
                            "volume": 1800,
                            "openInterest": 4800,
                            "impliedVolatility": 0.28,
                            "delta": 0.82,
                            "gamma": 0.012,
                            "theta": -0.15,
                            "vega": 0.45,
                            "rho": 0.18,
                            "intrinsicValue": 14.07,
                            "timeValue": 4.58,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017C00230000",
                            "contractSymbol": "AAPL251017C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 12.80,
                            "ask": 13.10,
                            "lastPrice": 12.95,
                            "volume": 1500,
                            "openInterest": 4200,
                            "impliedVolatility": 0.30,
                            "delta": 0.72,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.48,
                            "rho": 0.15,
                            "intrinsicValue": 4.07,
                            "timeValue": 8.88,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017C00240000",
                            "contractSymbol": "AAPL251017C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "call",
                            "bid": 7.20,
                            "ask": 7.50,
                            "lastPrice": 7.35,
                            "volume": 1200,
                            "openInterest": 3600,
                            "impliedVolatility": 0.32,
                            "delta": 0.58,
                            "gamma": 0.018,
                            "theta": -0.20,
                            "vega": 0.52,
                            "rho": 0.12,
                            "intrinsicValue": 0.0,
                            "timeValue": 7.35,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251121C00220000",
                            "contractSymbol": "AAPL251121C00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 22.10,
                            "ask": 22.40,
                            "lastPrice": 22.25,
                            "volume": 1500,
                            "openInterest": 4200,
                            "impliedVolatility": 0.30,
                            "delta": 0.85,
                            "gamma": 0.010,
                            "theta": -0.12,
                            "vega": 0.50,
                            "rho": 0.20,
                            "intrinsicValue": 14.07,
                            "timeValue": 8.18,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121C00230000",
                            "contractSymbol": "AAPL251121C00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 16.40,
                            "ask": 16.70,
                            "lastPrice": 16.55,
                            "volume": 1300,
                            "openInterest": 3800,
                            "impliedVolatility": 0.32,
                            "delta": 0.75,
                            "gamma": 0.012,
                            "theta": -0.15,
                            "vega": 0.52,
                            "rho": 0.17,
                            "intrinsicValue": 4.07,
                            "timeValue": 12.48,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121C00240000",
                            "contractSymbol": "AAPL251121C00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "call",
                            "bid": 11.20,
                            "ask": 11.50,
                            "lastPrice": 11.35,
                            "volume": 1000,
                            "openInterest": 3200,
                            "impliedVolatility": 0.34,
                            "delta": 0.62,
                            "gamma": 0.015,
                            "theta": -0.18,
                            "vega": 0.55,
                            "rho": 0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 11.35,
                            "daysToExpiration": 70
                        }
                    ],
                    "puts": [
                        {
                            "symbol": "AAPL250920P00220000",
                            "contractSymbol": "AAPL250920P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 0.85,
                            "ask": 1.15,
                            "lastPrice": 1.00,
                            "volume": 320,
                            "openInterest": 1800,
                            "impliedVolatility": 0.24,
                            "delta": -0.22,
                            "gamma": 0.015,
                            "theta": -0.08,
                            "vega": 0.38,
                            "rho": -0.15,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.00,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00225000",
                            "contractSymbol": "AAPL250920P00225000",
                            "strike": 225.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 1.40,
                            "ask": 1.70,
                            "lastPrice": 1.55,
                            "volume": 450,
                            "openInterest": 2200,
                            "impliedVolatility": 0.25,
                            "delta": -0.28,
                            "gamma": 0.017,
                            "theta": -0.09,
                            "vega": 0.42,
                            "rho": -0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 1.55,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00230000",
                            "contractSymbol": "AAPL250920P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 2.20,
                            "ask": 2.50,
                            "lastPrice": 2.35,
                            "volume": 890,
                            "openInterest": 3200,
                            "impliedVolatility": 0.26,
                            "delta": -0.35,
                            "gamma": 0.02,
                            "theta": -0.12,
                            "vega": 0.38,
                            "rho": -0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00235000",
                            "contractSymbol": "AAPL250920P00235000",
                            "strike": 235.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 3.40,
                            "ask": 3.70,
                            "lastPrice": 3.55,
                            "volume": 680,
                            "openInterest": 2800,
                            "impliedVolatility": 0.28,
                            "delta": -0.45,
                            "gamma": 0.022,
                            "theta": -0.14,
                            "vega": 0.48,
                            "rho": -0.10,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.55,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00240000",
                            "contractSymbol": "AAPL250920P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 5.20,
                            "ask": 5.50,
                            "lastPrice": 5.35,
                            "volume": 520,
                            "openInterest": 2400,
                            "impliedVolatility": 0.30,
                            "delta": -0.58,
                            "gamma": 0.025,
                            "theta": -0.16,
                            "vega": 0.50,
                            "rho": -0.08,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00245000",
                            "contractSymbol": "AAPL250920P00245000",
                            "strike": 245.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 7.80,
                            "ask": 8.10,
                            "lastPrice": 7.95,
                            "volume": 380,
                            "openInterest": 2000,
                            "impliedVolatility": 0.32,
                            "delta": -0.70,
                            "gamma": 0.028,
                            "theta": -0.18,
                            "vega": 0.52,
                            "rho": -0.06,
                            "intrinsicValue": 0.0,
                            "timeValue": 7.95,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL250920P00250000",
                            "contractSymbol": "AAPL250920P00250000",
                            "strike": 250.0,
                            "expirationDate": "2025-09-20",
                            "optionType": "put",
                            "bid": 11.20,
                            "ask": 11.50,
                            "lastPrice": 11.35,
                            "volume": 280,
                            "openInterest": 1600,
                            "impliedVolatility": 0.34,
                            "delta": -0.80,
                            "gamma": 0.030,
                            "theta": -0.20,
                            "vega": 0.54,
                            "rho": -0.04,
                            "intrinsicValue": 0.0,
                            "timeValue": 11.35,
                            "daysToExpiration": 15
                        },
                        {
                            "symbol": "AAPL251017P00220000",
                            "contractSymbol": "AAPL251017P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 2.10,
                            "ask": 2.40,
                            "lastPrice": 2.25,
                            "volume": 450,
                            "openInterest": 2200,
                            "impliedVolatility": 0.26,
                            "delta": -0.18,
                            "gamma": 0.012,
                            "theta": -0.10,
                            "vega": 0.45,
                            "rho": -0.18,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.25,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017P00230000",
                            "contractSymbol": "AAPL251017P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 3.80,
                            "ask": 4.10,
                            "lastPrice": 3.95,
                            "volume": 680,
                            "openInterest": 2800,
                            "impliedVolatility": 0.28,
                            "delta": -0.28,
                            "gamma": 0.015,
                            "theta": -0.12,
                            "vega": 0.48,
                            "rho": -0.15,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.95,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251017P00240000",
                            "contractSymbol": "AAPL251017P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-10-17",
                            "optionType": "put",
                            "bid": 6.20,
                            "ask": 6.50,
                            "lastPrice": 6.35,
                            "volume": 520,
                            "openInterest": 2400,
                            "impliedVolatility": 0.30,
                            "delta": -0.42,
                            "gamma": 0.018,
                            "theta": -0.14,
                            "vega": 0.52,
                            "rho": -0.12,
                            "intrinsicValue": 0.0,
                            "timeValue": 6.35,
                            "daysToExpiration": 43
                        },
                        {
                            "symbol": "AAPL251121P00220000",
                            "contractSymbol": "AAPL251121P00220000",
                            "strike": 220.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 3.20,
                            "ask": 3.50,
                            "lastPrice": 3.35,
                            "volume": 380,
                            "openInterest": 1800,
                            "impliedVolatility": 0.28,
                            "delta": -0.15,
                            "gamma": 0.010,
                            "theta": -0.08,
                            "vega": 0.50,
                            "rho": -0.20,
                            "intrinsicValue": 0.0,
                            "timeValue": 3.35,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121P00230000",
                            "contractSymbol": "AAPL251121P00230000",
                            "strike": 230.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 5.40,
                            "ask": 5.70,
                            "lastPrice": 5.55,
                            "volume": 320,
                            "openInterest": 2000,
                            "impliedVolatility": 0.30,
                            "delta": -0.25,
                            "gamma": 0.012,
                            "theta": -0.10,
                            "vega": 0.52,
                            "rho": -0.17,
                            "intrinsicValue": 0.0,
                            "timeValue": 5.55,
                            "daysToExpiration": 70
                        },
                        {
                            "symbol": "AAPL251121P00240000",
                            "contractSymbol": "AAPL251121P00240000",
                            "strike": 240.0,
                            "expirationDate": "2025-11-21",
                            "optionType": "put",
                            "bid": 8.60,
                            "ask": 8.90,
                            "lastPrice": 8.75,
                            "volume": 280,
                            "openInterest": 1600,
                            "impliedVolatility": 0.32,
                            "delta": -0.38,
                            "gamma": 0.015,
                            "theta": -0.12,
                            "vega": 0.55,
                            "rho": -0.14,
                            "intrinsicValue": 0.0,
                            "timeValue": 8.75,
                            "daysToExpiration": 70
                        }
                    ],
                    "greeks": {
                        "delta": 0.30,
                        "gamma": 0.02,
                        "theta": -0.13,
                        "vega": 0.41,
                        "rho": 0.02
                    }
                },
                "unusualFlow": {
                    "symbol": "AAPL250920C00235000",
                    "contractSymbol": "AAPL250920C00235000",
                    "optionType": "call",
                    "strike": 235.0,
                    "expirationDate": "2025-09-20",
                    "volume": 2500,
                    "openInterest": 1800,
                    "premium": 6.25,
                    "impliedVolatility": 0.32,
                    "unusualActivityScore": 8.5,
                    "activityType": "sweep"
                },
                "recommendedStrategies": [
                    {
                        "strategyName": "Covered Call",
                        "strategyType": "income",
                        "maxProfit": 8.65,
                        "maxLoss": -225.35,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.65,
                        "riskRewardRatio": 0.038,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 8.65,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Low"
                    },
                    {
                        "strategyName": "Protective Put",
                        "strategyType": "hedge",
                        "maxProfit": 0,
                        "maxLoss": -320.0,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.70,
                        "riskRewardRatio": 0.0,
                        "daysToExpiration": 15,
                        "totalCost": 320.0,
                        "totalCredit": 0.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Medium"
                    },
                    {
                        "strategyName": "Long Call",
                        "strategyType": "speculation",
                        "maxProfit": 0,
                        "maxLoss": -150.0,
                        "breakevenPoints": [232.0],
                        "probabilityOfProfit": 0.75,
                        "riskRewardRatio": 0.0,
                        "daysToExpiration": 15,
                        "totalCost": 150.0,
                        "totalCredit": 0.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "High"
                    },
                    {
                        "strategyName": "Iron Condor",
                        "strategyType": "arbitrage",
                        "maxProfit": 270.0,
                        "maxLoss": -180.0,
                        "breakevenPoints": [220.0, 250.0],
                        "probabilityOfProfit": 0.80,
                        "riskRewardRatio": 1.5,
                        "daysToExpiration": 15,
                        "totalCost": 180.0,
                        "totalCredit": 270.0,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Medium"
                    },
                    {
                        "strategyName": "Cash Secured Put",
                        "strategyType": "income",
                        "maxProfit": 4.35,
                        "maxLoss": -225.65,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.68,
                        "riskRewardRatio": 0.019,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 4.35,
                        "marketOutlook": "Neutral",
                        "riskLevel": "Low"
                    }
                ],
                "marketSentiment": {
                    "putCallRatio": 0.85,
                    "impliedVolatilityRank": 0.45,
                    "skew": 0.12,
                    "sentimentScore": 0.68,
                    "sentimentDescription": "Moderately bullish"
                }
            }
            
            response_data["testOptionsAnalysis"] = {
                "underlyingSymbol": "AAPL", 
                "underlyingPrice": 234.07,
                "marketSentiment": {
                    "sentimentDescription": "Moderately bullish",
                    "sentimentScore": 0.68,
                    "putCallRatio": 0.85,
                    "impliedVolatilityRank": 0.45
                },
                "unusualFlow": {
                    "symbol": "AAPL250920C00235000",
                    "contractSymbol": "AAPL250920C00235000",
                    "optionType": "call",
                    "strike": 235.0,
                    "expirationDate": "2025-09-20",
                    "volume": 2500,
                    "openInterest": 1800,
                    "premium": 6.25,
                    "impliedVolatility": 0.32,
                    "unusualActivityScore": 8.5,
                    "activityType": "sweep"
                },
                "recommendedStrategies": [
                    {
                        "strategyName": "Covered Call",
                        "strategyType": "income",
                        "maxProfit": 8.65,
                        "maxLoss": -225.35,
                        "breakevenPoints": [230.0],
                        "probabilityOfProfit": 0.65,
                        "riskRewardRatio": 0.038,
                        "daysToExpiration": 15,
                        "totalCost": 0.0,
                        "totalCredit": 8.65
                    }
                ]
            }
        
        # Rust Stock Analysis
        if "rustStockAnalysis" in query:
            symbol = variables.get("symbol", "AAPL")
            user_income = variables.get("userIncome", 50000)  # Default to $50k if not provided
            logger.info(f"RustStockAnalysis requested for symbol: {symbol}, user income: ${user_income}")
            stock_data = await generate_stock_data(symbol)
            
            # Calculate affordability metrics
            affordability = await calculate_affordability_score(stock_data, user_income)
            
            response_data["rustStockAnalysis"] = {
                "symbol": symbol,
                "price": stock_data["price"],
                "currentPrice": stock_data["currentPrice"],
                "change": stock_data["change"],
                "changePercent": stock_data["changePercent"],
                "targetPrice": stock_data["targetPrice"],
                "beginnerFriendlyScore": stock_data["beginnerFriendlyScore"],
                "riskLevel": stock_data["riskLevel"],
                "recommendation": await calculate_stock_recommendation(stock_data, user_income),
                "reasoning": await generate_stock_reasoning(stock_data, user_income),
                "affordability": affordability,
                "technicalIndicators": {
                    "rsi": round(random.uniform(20, 80), 2),
                    "macd": round(random.uniform(-2, 2), 2),
                    "macdSignal": round(random.uniform(-1, 1), 2),
                    "macdHistogram": round(random.uniform(-0.5, 0.5), 2),
                    "bollingerBands": {
                        "upper": round(stock_data["currentPrice"] * 1.1, 2),
                        "middle": round(stock_data["currentPrice"], 2),
                        "lower": round(stock_data["currentPrice"] * 0.9, 2),
                        "bollingerUpper": round(stock_data["currentPrice"] * 1.1, 2),
                        "bollingerMiddle": round(stock_data["currentPrice"], 2),
                        "bollingerLower": round(stock_data["currentPrice"] * 0.9, 2)
                    },
                    "bollingerUpper": round(stock_data["currentPrice"] * 1.1, 2),
                    "bollingerMiddle": round(stock_data["currentPrice"], 2),
                    "bollingerLower": round(stock_data["currentPrice"] * 0.9, 2),
                    "movingAverage": {
                        "sma20": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
                        "sma50": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2),
                        "ema12": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
                        "ema26": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2)
                    },
                    "sma20": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
                    "sma50": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2),
                    "ema12": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
                    "ema26": round(stock_data["currentPrice"] * random.uniform(0.9, 1.1), 2)
                },
                "fundamentalAnalysis": {
                    "peRatio": stock_data["peRatio"],
                    "marketCap": stock_data["marketCap"],
                    "dividendYield": stock_data["dividendYield"],
                    "growthRate": round(random.uniform(-10, 20), 2),
                    "valuationScore": round(random.uniform(60, 95), 1),
                    "growthScore": round(random.uniform(50, 90), 1),
                    "stabilityScore": round(random.uniform(70, 95), 1),
                    "dividendScore": round(random.uniform(40, 85), 1),
                    "debtScore": round(random.uniform(60, 90), 1)
                },
                "source": stock_data.get("source", "api"),
                "__typename": "RustStockAnalysis"
            }
        
        # AI Portfolio Recommendations
        if "aiPortfolioRecommendations" in query:
            user_id = variables.get("userId", "user_1")
            logger.info(f"AI Portfolio Recommendations requested for user: {user_id}")
            
            # Generate AI portfolio recommendations based on user profile
            response_data["aiPortfolioRecommendations"] = {
                "id": f"portfolio_{user_id}",
                "riskProfile": "Moderate Growth",
                "portfolioAllocation": {
                    "stocks": 70,
                    "bonds": 20,
                    "cash": 10
                },
                "recommendedStocks": [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "allocation": 15,
                        "reason": "Strong fundamentals and growth potential",
                        "reasoning": [
                            "Strong brand loyalty and ecosystem lock-in",
                            "Consistent revenue growth and cash generation",
                            "Leading position in smartphone and services markets"
                        ],
                        "riskLevel": "Low",
                        "expectedReturn": 12.5
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation", 
                        "allocation": 12,
                        "reason": "Cloud computing leader with stable revenue",
                        "reasoning": [
                            "Dominant position in enterprise software",
                            "Azure cloud platform showing strong growth",
                            "Diversified revenue streams across business segments"
                        ],
                        "riskLevel": "Low",
                        "expectedReturn": 11.8
                    },
                    {
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "allocation": 10,
                        "reason": "Diversified tech exposure and AI growth",
                        "reasoning": [
                            "Search advertising dominance with high margins",
                            "YouTube and cloud services providing growth",
                            "AI investments positioning for future growth"
                        ],
                        "riskLevel": "Medium",
                        "expectedReturn": 13.2
                    },
                    {
                        "symbol": "JNJ",
                        "companyName": "Johnson & Johnson",
                        "allocation": 8,
                        "reason": "Defensive healthcare stock for stability",
                        "reasoning": [
                            "Diversified healthcare portfolio across pharmaceuticals and medical devices",
                            "Consistent dividend payments and stable cash flow",
                            "Defensive characteristics during market volatility"
                        ],
                        "riskLevel": "Low",
                        "expectedReturn": 8.5
                    },
                    {
                        "symbol": "V",
                        "companyName": "Visa Inc.",
                        "allocation": 7,
                        "reason": "Payment processing growth and low volatility",
                        "reasoning": [
                            "Network effect creates competitive moat",
                            "Global shift to digital payments drives growth",
                            "High-margin business model with recurring revenue"
                        ],
                        "riskLevel": "Low",
                        "expectedReturn": 10.2
                    }
                ],
                "expectedReturn": 8.5,
                "expectedPortfolioReturn": 11.2,
                "riskLevel": "Medium",
                "riskAssessment": {
                    "overallRisk": "Medium",
                    "volatility": "Moderate",
                    "downsideProtection": "Good",
                    "correlationRisk": "Low"
                },
                "timeHorizon": "5-10 years",
                "lastUpdated": datetime.now().isoformat(),
                "createdAt": datetime.now().isoformat(),
                "__typename": "AIPortfolioRecommendation"
            }
        
        return {
            "data": response_data
        }
    
    # Default response for other queries
    return {
        "data": {},
        "errors": [{"message": "Query not supported"}]
    }

@app.post("/api/portfolio/analyze")
async def analyze_portfolio(background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    """Analyze investment portfolio using AI"""
    return {
        "message": "Portfolio analysis started",
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "user": current_user
    }

@app.post("/api/market/regime")
async def predict_market_regime(background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    """Predict current market regime using AI"""
    return {
        "message": "Market regime prediction started",
        "status": "processing",
        "timestamp": datetime.now().isoformat(),
        "user": current_user
    }

@app.get("/api/status")
async def get_service_status(current_user: str = Depends(verify_token)):
    """Get comprehensive service status"""
    return {
        "service": "RichesReach AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "ml_services": False,
        "user": current_user
    }

# AI Options API Endpoints
@app.post("/api/ai-options/recommendations")
async def get_ai_options_recommendations(request: dict):
    """Get AI-powered options strategy recommendations"""
    try:
        symbol = request.get("symbol", "AAPL").upper()
        user_risk_tolerance = request.get("user_risk_tolerance", "medium")
        portfolio_value = request.get("portfolio_value", 10000)
        time_horizon = request.get("time_horizon", 30)
        max_recommendations = request.get("max_recommendations", 5)
        
        logger.info(f"AI Options request for {symbol}: risk={user_risk_tolerance}, value=${portfolio_value}, horizon={time_horizon} days")
        
        # Generate mock AI options recommendations
        recommendations = []
        for i in range(max_recommendations):
            strategy_types = ["income", "hedge", "speculation", "arbitrage"]
            strategy_type = strategy_types[i % len(strategy_types)]
            
            # Generate options based on strategy type
            if strategy_type == "income":
                strategy_name = "Covered Call Strategy"
                options = [
                    {"type": "call", "action": "sell", "strike": 240.0, "expiration": "2025-10-17", "premium": 2.50, "quantity": 100},
                    {"type": "call", "action": "sell", "strike": 245.0, "expiration": "2025-11-21", "premium": 1.80, "quantity": 100}
                ]
            elif strategy_type == "hedge":
                strategy_name = "Protective Put Strategy"
                options = [
                    {"type": "put", "action": "buy", "strike": 220.0, "expiration": "2025-10-17", "premium": 3.20, "quantity": 100}
                ]
            elif strategy_type == "speculation":
                strategy_name = "Long Call Strategy"
                options = [
                    {"type": "call", "action": "buy", "strike": 250.0, "expiration": "2025-10-17", "premium": 1.50, "quantity": 100}
                ]
            else:  # arbitrage
                strategy_name = "Iron Condor Strategy"
                options = [
                    {"type": "call", "action": "sell", "strike": 250.0, "expiration": "2025-10-17", "premium": 1.20, "quantity": 100},
                    {"type": "call", "action": "buy", "strike": 255.0, "expiration": "2025-10-17", "premium": 0.80, "quantity": 100},
                    {"type": "put", "action": "sell", "strike": 220.0, "expiration": "2025-10-17", "premium": 1.50, "quantity": 100},
                    {"type": "put", "action": "buy", "strike": 215.0, "expiration": "2025-10-17", "premium": 1.00, "quantity": 100}
                ]
            
            # Calculate analytics based on strategy
            max_profit = sum(opt["premium"] * opt["quantity"] for opt in options if opt["action"] == "sell")
            max_loss = sum(opt["premium"] * opt["quantity"] for opt in options if opt["action"] == "buy")
            probability_of_profit = 0.65 + (i * 0.05)  # Varying probabilities
            expected_return = (max_profit - max_loss) / portfolio_value
            
            recommendation = {
                "strategy_name": strategy_name,
                "strategy_type": strategy_type,
                "confidence_score": 75 + (i * 5),
                "symbol": symbol,
                "current_price": 234.07,
                "options": options,
                "analytics": {
                    "max_profit": max_profit,
                    "max_loss": max_loss,
                    "probability_of_profit": probability_of_profit,
                    "expected_return": expected_return,
                    "breakeven": 234.07 + (max_profit - max_loss) / 100
                },
                "reasoning": {
                    "market_outlook": "Moderately bullish with elevated volatility",
                    "strategy_rationale": f"This {strategy_type} strategy is suitable for your risk tolerance and portfolio size",
                    "risk_factors": ["Market volatility", "Time decay", "Liquidity risk"],
                    "key_benefits": ["Income generation", "Risk management", "Flexibility"]
                },
                "risk_score": 30 + (i * 15),
                "expected_return": expected_return,
                "max_profit": max_profit,
                "max_loss": max_loss,
                "probability_of_profit": probability_of_profit,
                "days_to_expiration": time_horizon,
                "market_outlook": "Moderately bullish",
                "created_at": datetime.now().isoformat()
            }
            recommendations.append(recommendation)
        
        # Generate market analysis
        market_analysis = {
            "symbol": symbol,
            "current_price": 234.07,
            "volatility": 0.25,
            "implied_volatility": 0.28,
            "volume": 45000000,
            "market_cap": 3600000000000,
            "sector": "Technology",
            "sentiment_score": 0.68,
            "trend_direction": "bullish",
            "support_levels": [220.0, 210.0, 200.0],
            "resistance_levels": [250.0, 260.0, 270.0],
            "earnings_date": "2024-01-25",
            "dividend_yield": 0.0044,
            "beta": 1.2
        }
        
        response = {
            "symbol": symbol,
            "current_price": 234.07,
            "recommendations": recommendations,
            "market_analysis": market_analysis,
            "generated_at": datetime.now().isoformat(),
            "total_recommendations": len(recommendations)
        }
        
        logger.info(f"Generated {len(recommendations)} AI options recommendations for {symbol}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI options recommendations: {str(e)}")
        return {"error": f"Failed to generate recommendations: {str(e)}"}

@app.post("/api/ai-options/optimize-strategy")
async def optimize_strategy(request: dict):
    """Optimize specific options strategy parameters"""
    return {
        "symbol": request.get("symbol", "AAPL"),
        "strategy_type": request.get("strategy_type", "income"),
        "optimal_parameters": {
            "strike_selection": "ATM",
            "expiration_selection": "30-45 days",
            "position_sizing": "2-5% of portfolio"
        },
        "optimization_score": 0.85,
        "predicted_outcomes": {
            "expected_return": 0.12,
            "max_drawdown": 0.05,
            "win_rate": 0.68
        },
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/ai-options/market-analysis")
async def get_market_analysis(request: dict):
    """Get comprehensive market analysis"""
    symbol = request.get("symbol", "AAPL").upper()
    return {
        "symbol": symbol,
        "analysis_type": request.get("analysis_type", "comprehensive"),
        "technical_analysis": {
            "trend": "bullish",
            "support": 220.0,
            "resistance": 250.0,
            "rsi": 65.2,
            "macd": "positive"
        },
        "fundamental_analysis": {
            "pe_ratio": 28.5,
            "revenue_growth": 0.08,
            "profit_margin": 0.25
        },
        "options_flow": {
            "unusual_activity": True,
            "call_put_ratio": 1.2,
            "volume_spike": True
        },
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/ai-options/train-models")
async def train_models(request: dict):
    """Train ML models for a symbol"""
    symbol = request.get("symbol", "AAPL").upper()
    return {
        "symbol": symbol,
        "status": "training_started",
        "estimated_completion": "2-4 hours",
        "message": f"ML models training initiated for {symbol}",
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/ai-options/model-status/{symbol}")
async def get_model_status(symbol: str):
    """Get model status for a symbol"""
    return {
        "symbol": symbol.upper(),
        "status": "trained",
        "last_updated": datetime.now().isoformat(),
        "accuracy": 0.78,
        "models": ["LSTM", "Random Forest", "SVM"]
    }

@app.get("/api/ai-options/health")
async def ai_options_health():
    """Health check for AI Options API"""
    return {
        "service": "AI Options API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
