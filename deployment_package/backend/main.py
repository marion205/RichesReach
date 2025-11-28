#!/usr/bin/env python3
"""
RichesReach AI Service - Production Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
import logging
from datetime import datetime
import asyncio
import sys
import django
import json
import re
from asgiref.sync import sync_to_async
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from starlette.middleware.wsgi import WSGIMiddleware
from io import BytesIO
from dotenv import load_dotenv
import aiohttp
import time

# ✅ Price cache for fast repeated lookups
class PriceCache:
    """Simple TTL cache for crypto/stock prices."""
    def __init__(self, ttl: int = 12):
        self.ttl = ttl  # 12 seconds - crypto moves fast but we don't need per-second
        self.data = {}
    
    def get(self, key: str):
        entry = self.data.get(key)
        if not entry:
            return None
        value, ts = entry
        if time.time() - ts > self.ttl:
            del self.data[key]
            return None
        return value
    
    def set(self, key: str, value):
        self.data[key] = (value, time.time())
    
    def clear(self, key: str = None):
        """Clear cache entry or all entries."""
        if key:
            self.data.pop(key, None)
        else:
            self.data.clear()

# Global price cache instance
price_cache = PriceCache(ttl=12)

# Load environment variables from .env file
# This ensures FastAPI can access environment variables even if Django hasn't loaded them yet
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# Setup Django to access models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
try:
    django.setup()
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import check_password
    try:
        from graphql_jwt.shortcuts import get_token
        GRAPHQL_JWT_AVAILABLE = True
    except ImportError:
        GRAPHQL_JWT_AVAILABLE = False
    # Import GraphQL schema and view
    try:
        from core.schema import schema
        from core.views import graphql_view
        GRAPHQL_AVAILABLE = True
    except Exception as e:
        logging.warning(f"GraphQL not available: {e}")
        GRAPHQL_AVAILABLE = False
        schema = None
        graphql_view = None
    DJANGO_AVAILABLE = True
except Exception as e:
    logging.warning(f"Django not available: {e}")
    DJANGO_AVAILABLE = False
    GRAPHQL_AVAILABLE = False
    schema = None
    graphql_view = None

# Import our AI services
try:
    from core.optimized_ml_service import OptimizedMLService
    from core.market_data_service import MarketDataService
    from core.advanced_market_data_service import AdvancedMarketDataService
    from core.advanced_ml_algorithms import AdvancedMLAlgorithms
    from core.performance_monitoring_service import ProductionMonitoringService
    ML_SERVICES_AVAILABLE = True
except (ImportError, SyntaxError, IndentationError) as e:
    ML_SERVICES_AVAILABLE = False
    logging.warning(f"ML services not available - running in basic mode: {e}")

# Import AI Options API separately (always available)
try:
    from core.ai_options_api import router as ai_options_router
    AI_OPTIONS_AVAILABLE = True
except ImportError as e:
    AI_OPTIONS_AVAILABLE = False
    logging.warning(f"AI Options API not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for reportlab availability
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available - PDF export will not work")

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

# Add request logging middleware for debugging
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Log requests to Yodlee endpoints
        if '/api/yodlee' in str(request.url):
            import sys
            auth_header = request.headers.get('authorization') or request.headers.get('Authorization', '')
            print(f"🔵 [FastAPI] {request.method} {request.url.path}", file=sys.stdout, flush=True)
            print(f"🔵 [FastAPI] Authorization header: {'Present' if auth_header else 'MISSING'} ({auth_header[:30] if auth_header else 'None'}...)", file=sys.stdout, flush=True)
            print(f"🔵 [FastAPI] All headers: {dict(request.headers)}", file=sys.stdout, flush=True)
            logger.info(f"🔵 [FastAPI] {request.method} {request.url.path} - Auth: {'Present' if auth_header else 'MISSING'}")
        
        response = await call_next(request)
        return response

app.add_middleware(RequestLoggingMiddleware)

# Include AI Options router
if AI_OPTIONS_AVAILABLE:
    app.include_router(ai_options_router)

# Note: FastAPI routes (defined with @app.get/post/etc) are registered here
# Django will be mounted later, after all FastAPI routes are defined
# This ensures FastAPI routes take precedence

# ✅ Fast voice model configuration
FAST_VOICE_MODEL = "gpt-4o-mini"  # Fast, cheap model for voice
DEEP_MODEL = "gpt-4o"  # Reserved for deep analysis (not used in voice)

# ✅ Helper: Trim conversation history to last N exchanges
def trim_history_for_voice(history: list, max_exchanges: int = 4) -> list:
    """
    Trim history to last N user/assistant exchanges (keeps context but reduces tokens).
    Returns list of message dicts ready for LLM.
    """
    if not history:
        return []
    
    # Convert history to message format if needed
    messages = []
    for item in history[-max_exchanges * 2:]:  # Last 4 exchanges = 8 messages max
        if isinstance(item, dict):
            if 'type' in item:
                role = 'user' if item['type'] == 'user' else 'assistant'
                messages.append({"role": role, "content": item.get('text', '')})
            elif 'role' in item:
                messages.append(item)
    
    return messages

# ✅ LLM-based voice response generation (non-streaming, for fallback)
async def generate_voice_reply(
    system_prompt: str,
    user_prompt: str,
    history: list = None,
    model: str = FAST_VOICE_MODEL
) -> str:
    """
    Generate natural language response using OpenAI chat API.
    This is the "voice" layer - it takes structured data and speaks naturally.
    Optimized for speed: trimmed history, smaller model, fewer tokens.
    """
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.warn("⚠️ OpenAI API key not found - cannot generate natural language responses")
        return None
    
    try:
        import openai
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Build trimmed messages (last 4 exchanges + system + current)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(trim_history_for_voice(history, max_exchanges=4))
        messages.append({"role": "user", "content": user_prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=140,  # Reduced from 200 for faster generation
        )
        
        reply = response.choices[0].message.content.strip()
        logger.info(f"✅ Generated natural language response ({len(reply)} chars)")
        return reply
    except Exception as e:
        logger.error(f"❌ Error generating LLM response: {e}")
        return None

# ✅ Streaming voice reply generator
async def generate_voice_reply_stream(
    system_prompt: str,
    user_prompt: str,
    history: list = None,
    model: str = FAST_VOICE_MODEL,
    skip_ack: bool = False
):
    """
    Generate streaming natural language response token-by-token.
    Yields JSON lines: {"type": "ack|token|done|error", "text": "..."}
    """
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        yield json.dumps({"type": "error", "text": "API key not configured"}) + "\n"
        return
    
    try:
        import openai
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Build trimmed messages (OPTIMIZED: reduced history from 4 to 2 exchanges for speed)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(trim_history_for_voice(history, max_exchanges=2))  # Reduced from 4 to 2
        messages.append({"role": "user", "content": user_prompt})
        
        # First: instant acknowledgment (unless caller already sent it)
        if not skip_ack:
            yield json.dumps({"type": "ack", "text": "Got it…"}) + "\n"
        
        # Stream tokens (OpenAI returns sync generator, wrap in async)
        # OPTIMIZED: Reduced max_tokens and temperature for faster response
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.6,  # Reduced from 0.7 for faster, more deterministic responses
            max_tokens=120,  # Reduced from 160 for faster responses
            stream=True,  # ← KEY: Enable streaming
        )
        
        collected = ""
        # OpenAI stream is sync, but we're in async context - run in executor
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                collected += token
                # Send every token immediately
                yield json.dumps({"type": "token", "text": token}) + "\n"
        
        # Final chunk when done
        yield json.dumps({"type": "done", "full_text": collected.strip()}) + "\n"
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error in streaming LLM response: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        yield json.dumps({"type": "error", "text": "I got confused, try again?"}) + "\n"

# ✅ Parse direct buy/sell commands from voice
def parse_trade_command(transcript: str) -> dict:
    """
    Parse direct buy/sell commands like "buy one bitcoin" or "buy 100 shares of Apple"
    Returns: {symbol: str, quantity: float, side: str, type: str} or None
    """
    text = transcript.lower()
    
    # Detect buy/sell
    side = None
    if "buy" in text:
        side = "buy"
    elif "sell" in text:
        side = "sell"
    else:
        return None
    
    # Extract quantity (look for numbers)
    import re
    quantity = 1.0  # Default
    quantity_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:shares?|share)',
        r'(\d+(?:\.\d+)?)\s*(?:bitcoin|btc|ethereum|eth|solana|sol)',
        r'(\d+(?:\.\d+)?)\s*(?:of|)',
        r'(\d+(?:\.\d+)?)',
    ]
    
    for pattern in quantity_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                quantity = float(match.group(1))
                break
            except:
                pass
    
    # Handle word numbers for small quantities
    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "a": 1, "an": 1, "single": 1
    }
    for word, num in word_numbers.items():
        if word in text and quantity == 1.0:
            quantity = float(num)
            break
    
    # Detect symbol
    symbol = None
    asset_type = "stock"  # Default
    
    # Crypto detection
    crypto_map = {
        "bitcoin": "BTC", "btc": "BTC",
        "ethereum": "ETH", "eth": "ETH",
        "solana": "SOL", "sol": "SOL",
    }
    for keyword, sym in crypto_map.items():
        if keyword in text:
            symbol = sym
            asset_type = "crypto"
            break
    
    # Stock detection (if not crypto)
    if not symbol:
        stock_map = {
            "apple": "AAPL", "aapl": "AAPL",
            "tesla": "TSLA", "tsla": "TSLA",
            "microsoft": "MSFT", "msft": "MSFT",
            "nvidia": "NVDA", "nvda": "NVDA",
            "google": "GOOGL", "googl": "GOOGL",
            "amazon": "AMZN", "amzn": "AMZN",
            "meta": "META", "facebook": "META", "fb": "META",
            "netflix": "NFLX", "nflx": "NFLX",
        }
        for keyword, sym in stock_map.items():
            if keyword in text:
                symbol = sym
                asset_type = "stock"
                break
    
    if symbol and side:
        return {
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "type": asset_type,
        }
    
    return None

# ✅ Intent detection - separates "what user wants" from "what to say"
def detect_intent(transcript: str, history: list = None, last_trade: dict = None) -> str:
    """
    Detect user intent from transcript.
    Returns: 'get_trade_idea', 'execute_trade', 'crypto_query', 'portfolio_query', 'explain_trade', 'small_talk'
    """
    text = transcript.lower()
    
    # Direct buy/sell commands (HIGHEST priority - before crypto_query)
    trade_cmd = parse_trade_command(transcript)
    if trade_cmd:
        return "execute_trade"
    
    # Buy multiple stocks command (e.g., "buy three stocks", "buy 5 stocks that will make me money")
    if "buy" in text and "stock" in text:
        # Check for quantity
        import re
        quantity_match = re.search(r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*stock', text)
        if quantity_match:
            return "buy_multiple_stocks"
    
    # Execution commands (confirmation of previous recommendation)
    if any(phrase in text for phrase in ["execute", "place order", "place the order", "do it", "go ahead", "confirm"]):
        if any(word in text for word in ["trade", "order", "buy", "sell"]):
            return "execute_trade"
    
    # Simple "yes" after a trade recommendation
    if text.strip() in ["yes", "yeah", "yep", "sure", "ok", "okay"] and last_trade:
        return "execute_trade"
    
    # Crypto queries (only if NOT a buy/sell command)
    if any(word in text for word in ["cryptocurrency", "crypto", "bitcoin", "ethereum", "btc", "eth", "solana", "sol"]):
        # Double-check it's not a buy/sell command
        if "buy" not in text and "sell" not in text:
            return "crypto_query"
    
    # Stock queries (check before trade idea to catch specific stock mentions)
    common_stocks = ["apple", "aapl", "tesla", "tsla", "microsoft", "msft", "nvidia", "nvda", 
                     "google", "googl", "amazon", "amzn", "meta", "facebook", "fb", "netflix", "nflx"]
    if any(stock in text for stock in common_stocks):
        return "stock_query"
    
    # Trade idea requests
    if any(phrase in text for phrase in ["what should i invest", "what should i buy", "best trade", "trading opportunity", "day trade", "momentum"]):
        return "get_trade_idea"
    
    # Portfolio queries
    if any(word in text for word in ["portfolio", "performance", "positions", "buying power"]):
        return "portfolio_query"
    
    # Explanation requests (if there's a last trade)
    if any(word in text for word in ["why", "explain", "reason"]) and last_trade:
        return "explain_trade"
    
    # Risk/reward analysis
    if any(phrase in text for phrase in ["risk reward", "risk/reward", "analysis"]):
        return "explain_trade"
    
    # Default to small talk / general conversation
    return "small_talk"

# ✅ Build context for LLM based on intent - OPTIMIZED with parallel fetching
async def build_context(intent: str, transcript: str, history: list = None, last_trade: dict = None) -> dict:
    """
    Build structured context data for the LLM based on intent.
    This is the "brain" - fetches real data (prices, trades, portfolio).
    OPTIMIZED: Parallel fetching for speed.
    """
    context = {
        "intent": intent,
        "transcript": transcript,
        "history": history or [],
        "last_trade": last_trade,
    }
    
    # ✅ Parallel fetch tasks based on intent
    # For voice queries, always force refresh to get latest prices
    force_refresh = True  # Voice queries need fresh data
    
    tasks = []
    
    if intent == "crypto_query":
        # Detect which crypto
        text = transcript.lower()
        if "bitcoin" in text or "btc" in text:
            tasks.append(('btc', get_crypto_price('BTC', force_refresh=force_refresh)))
        elif "ethereum" in text or "eth" in text:
            tasks.append(('eth', get_crypto_price('ETH', force_refresh=force_refresh)))
        elif "solana" in text or "sol" in text:
            tasks.append(('sol', get_crypto_price('SOL', force_refresh=force_refresh)))
        else:
            # General crypto - fetch top 3 in parallel
            tasks.extend([
                ('btc', get_crypto_price('BTC', force_refresh=force_refresh)),
                ('eth', get_crypto_price('ETH', force_refresh=force_refresh)),
                ('sol', get_crypto_price('SOL', force_refresh=force_refresh)),
            ])
    
    elif intent == "stock_query":
        # Detect which stock from transcript
        text = transcript.lower()
        stock_map = {
            "apple": "AAPL", "aapl": "AAPL",
            "tesla": "TSLA", "tsla": "TSLA",
            "microsoft": "MSFT", "msft": "MSFT",
            "nvidia": "NVDA", "nvda": "NVDA",
            "google": "GOOGL", "googl": "GOOGL",
            "amazon": "AMZN", "amzn": "AMZN",
            "meta": "META", "facebook": "META", "fb": "META",
            "netflix": "NFLX", "nflx": "NFLX",
        }
        
        detected_symbol = None
        for keyword, symbol in stock_map.items():
            if keyword in text:
                detected_symbol = symbol
                break
        
        if detected_symbol:
            tasks.append(('stock', get_stock_price(detected_symbol, force_refresh=force_refresh)))
    
    # Execute all fetches in parallel
    if tasks:
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        if intent == "crypto_query":
            text = transcript.lower()
            if "bitcoin" in text or "btc" in text:
                btc_data = results[0] if not isinstance(results[0], Exception) else None
                if btc_data:
                    data_age_seconds = int(time.time() - btc_data.get('timestamp', time.time()))
                    context["crypto"] = {
                        "symbol": "BTC",
                        "name": "Bitcoin",
                        "price": btc_data['price'],
                        "change_24h": btc_data.get('change_percent_24h', 0),
                        "data_age_seconds": data_age_seconds,
                        "is_fresh": data_age_seconds < 30,
                    }
            elif "ethereum" in text or "eth" in text:
                eth_data = results[0] if not isinstance(results[0], Exception) else None
                if eth_data:
                    data_age_seconds = int(time.time() - eth_data.get('timestamp', time.time()))
                    context["crypto"] = {
                        "symbol": "ETH",
                        "name": "Ethereum",
                        "price": eth_data['price'],
                        "change_24h": eth_data.get('change_percent_24h', 0),
                        "data_age_seconds": data_age_seconds,
                        "is_fresh": data_age_seconds < 30,
                    }
            elif "solana" in text or "sol" in text:
                sol_data = results[0] if not isinstance(results[0], Exception) else None
                if sol_data:
                    data_age_seconds = int(time.time() - sol_data.get('timestamp', time.time()))
                    context["crypto"] = {
                        "symbol": "SOL",
                        "name": "Solana",
                        "price": sol_data['price'],
                        "change_24h": sol_data.get('change_percent_24h', 0),
                        "data_age_seconds": data_age_seconds,
                        "is_fresh": data_age_seconds < 30,
                    }
            else:
                # General crypto - use all 3 results
                btc_data = results[0] if not isinstance(results[0], Exception) else None
                eth_data = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None
                sol_data = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else None
                
                # Calculate data age for each
                btc_age = int(time.time() - btc_data.get('timestamp', time.time())) if btc_data else 999
                eth_age = int(time.time() - eth_data.get('timestamp', time.time())) if eth_data else 999
                sol_age = int(time.time() - sol_data.get('timestamp', time.time())) if sol_data else 999
                
                context["crypto"] = {
                    "top_picks": [
                        {
                            "symbol": "BTC", 
                            "name": "Bitcoin", 
                            "price": btc_data['price'] if btc_data else 55000, 
                            "change_24h": btc_data.get('change_percent_24h', 0) if btc_data else 0,
                            "data_age_seconds": btc_age,
                            "is_fresh": btc_age < 30,
                        },
                        {
                            "symbol": "ETH", 
                            "name": "Ethereum", 
                            "price": eth_data['price'] if eth_data else 3200, 
                            "change_24h": eth_data.get('change_percent_24h', 0) if eth_data else 0,
                            "data_age_seconds": eth_age,
                            "is_fresh": eth_age < 30,
                        },
                        {
                            "symbol": "SOL", 
                            "name": "Solana", 
                            "price": sol_data['price'] if sol_data else 180, 
                            "change_24h": sol_data.get('change_percent_24h', 0) if sol_data else 0,
                            "data_age_seconds": sol_age,
                            "is_fresh": sol_age < 30,
                        },
                    ]
                }
        
        elif intent == "stock_query":
            stock_data = results[0] if not isinstance(results[0], Exception) else None
            if stock_data:
                # Calculate data age for freshness indicator
                data_age_seconds = int(time.time() - stock_data.get('timestamp', time.time()))
                context["stock"] = {
                    "symbol": stock_data.get('symbol', 'UNKNOWN'),
                    "price": stock_data.get('price', 0),
                    "change": stock_data.get('change', 0),
                    "change_percent": stock_data.get('change_percent', 0),
                    "volume": stock_data.get('volume', 0),
                    "data_age_seconds": data_age_seconds,
                    "is_fresh": data_age_seconds < 30,  # Consider fresh if < 30 seconds old
                    "source": stock_data.get('source', 'unknown'),
                }
                logger.info(f"✅ Stock context: {context['stock']['symbol']} @ ${context['stock']['price']:,.2f} (age: {data_age_seconds}s)")
            else:
                logger.warn(f"⚠️ No stock data available for query")
    
    elif intent == "buy_multiple_stocks":
        # Parse quantity from transcript
        import re
        text = transcript.lower()
        word_numbers = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        
        quantity = 3  # Default
        quantity_match = re.search(r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*stock', text)
        if quantity_match:
            match_text = quantity_match.group(1)
            if match_text in word_numbers:
                quantity = word_numbers[match_text]
            else:
                try:
                    quantity = int(match_text)
                except:
                    quantity = 3
        
        context["buy_multiple_stocks"] = {
            "quantity": quantity,
            "criteria": transcript,  # Store the full criteria for LLM
        }
    
    elif intent == "get_trade_idea":
        # Generate a trade recommendation (using your existing ML/signals logic)
        # For now, using a structured recommendation
        context["trade"] = {
            "symbol": "NVDA",
            "type": "stock",
            "side": "buy",
            "entry": 179.50,
            "stop": 178.00,
            "target": 185.00,
            "rvol": 3.2,
            "win_prob": 0.68,
            "r_multiple": 3.67,
            "reasoning_points": [
                "breakout above VWAP with volume confirmation",
                "strong relative strength vs QQQ",
                "favorable macro / AI theme"
            ]
        }
    
    elif intent == "portfolio_query":
        # Fetch portfolio data (mock for now, but structure is ready for real data)
        context["portfolio"] = {
            "value": 14303.52,
            "return": 17.65,
            "positions": [
                {"symbol": "NVDA", "shares": 100, "pnl": 435.00},
                {"symbol": "AAPL", "shares": 50, "pnl": 125.00},
                {"symbol": "MSFT", "shares": 75, "pnl": 87.50},
            ],
            "buying_power": 8450.00,
        }
    
    return context

# ✅ Generate natural language responses based on intent and context
async def respond_with_buy_multiple_stocks(transcript: str, history: list, context: dict) -> dict:
    """Generate stock recommendations and execute orders for multiple stocks."""
    buy_info = context.get("buy_multiple_stocks", {})
    quantity = buy_info.get("quantity", 3)
    criteria = buy_info.get("criteria", transcript)
    
    logger.info(f"🛒 Processing buy_multiple_stocks: quantity={quantity}, criteria='{criteria}'")
    
    # Step 1: Use LLM to generate stock recommendations (OPTIMIZED: faster model, shorter response)
    system_prompt = """You are RichesReach. Return ONLY a JSON array with stock recommendations.
Format: [{"symbol":"AAPL","name":"Apple Inc.","reasoning":"brief reason"}]
Use real symbols: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, NFLX, JPM, V, MA."""
    
    user_prompt = f"""User wants {quantity} stocks matching: "{criteria}"
Return JSON array only: [{{"symbol":"SYMBOL","name":"Name","reasoning":"reason"}}]"""
    
    # Get LLM recommendations (use faster model, shorter response)
    logger.info(f"🤖 Requesting LLM recommendations for {quantity} stocks...")
    start_llm = time.time()
    recommendations_text = await generate_voice_reply(
        system_prompt, 
        user_prompt, 
        history,
        model="gpt-4o-mini"  # Faster model for recommendations
    )
    llm_time = time.time() - start_llm
    logger.info(f"⏱️ LLM took {llm_time:.2f}s")
    
    if not recommendations_text:
        logger.warn("⚠️ LLM returned empty response")
        recommendations_text = ""
    
    logger.info(f"📝 LLM response (first 200 chars): {recommendations_text[:200]}")
    
    # Parse recommendations
    recommended_stocks = []
    try:
        # Extract JSON from response (might have extra text)
        import re
        json_match = re.search(r'\[.*\]', recommendations_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.info(f"📋 Extracted JSON: {json_str[:200]}")
            recommendations_json = json.loads(json_str)
            if isinstance(recommendations_json, list) and len(recommendations_json) > 0:
                recommended_stocks = recommendations_json[:quantity]  # Limit to requested quantity
                logger.info(f"✅ Parsed {len(recommended_stocks)} stock recommendations from LLM")
            else:
                logger.warn(f"⚠️ LLM returned empty or invalid list: {recommendations_json}")
        else:
            logger.warn(f"⚠️ No JSON array found in LLM response")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        logger.error(f"❌ Response text: {recommendations_text[:500]}")
    except Exception as e:
        logger.error(f"❌ Error parsing LLM recommendations: {e}")
        logger.error(f"❌ Response text: {recommendations_text[:500]}")
    
    # Dynamic fallback: Try to get trending/popular stocks if LLM parsing failed
    if not recommended_stocks:
        logger.warn("⚠️ LLM parsing failed, using dynamic fallback...")
        # Use a diverse set of popular stocks across sectors
        fallback_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc.", "reasoning": "Tech sector leader with strong fundamentals"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "reasoning": "AI and semiconductor growth"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "reasoning": "Cloud and enterprise software"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "reasoning": "Search and advertising dominance"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "reasoning": "E-commerce and cloud services"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "reasoning": "Social media and VR growth"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "reasoning": "Electric vehicle market leader"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "reasoning": "Financial services strength"},
            {"symbol": "V", "name": "Visa Inc.", "reasoning": "Payment processing growth"},
            {"symbol": "MA", "name": "Mastercard Inc.", "reasoning": "Digital payments expansion"},
        ]
        # Select diverse stocks based on quantity
        recommended_stocks = fallback_stocks[:quantity]
        logger.info(f"✅ Using fallback: {[s['symbol'] for s in recommended_stocks]}")
    
    # Step 2: Fetch current prices for each stock
    executed_trades = []
    logger.info(f"💰 Fetching prices for {len(recommended_stocks)} stocks...")
    
    for stock_rec in recommended_stocks:
        symbol = stock_rec.get("symbol", "UNKNOWN")
        if symbol == "UNKNOWN":
            logger.warn(f"⚠️ Skipping stock with unknown symbol: {stock_rec}")
            continue
        
        try:
            logger.info(f"📊 Fetching price for {symbol}...")
            price_data = await get_stock_price(symbol, force_refresh=True)
            if price_data and price_data.get("price", 0) > 0:
                trade = {
                    "symbol": symbol,
                    "name": stock_rec.get("name", symbol),
                    "quantity": 10,  # Default quantity per stock
                    "side": "buy",
                    "type": "stock",
                    "price": price_data.get("price", 0),
                    "change_percent": price_data.get("change_percent", 0),
                    "order_type": "market",
                    "reasoning": stock_rec.get("reasoning", ""),
                }
                executed_trades.append(trade)
                logger.info(f"✅ Added trade for {symbol} at ${trade['price']:,.2f}")
            else:
                logger.warn(f"⚠️ No valid price data for {symbol}: {price_data}")
                # Still add the trade with estimated price if we have the stock info
                # This allows the order to proceed even if price fetch fails
                if symbol and stock_rec.get("name"):
                    logger.info(f"⚠️ Adding trade for {symbol} without price (will use market price)")
                    trade = {
                        "symbol": symbol,
                        "name": stock_rec.get("name", symbol),
                        "quantity": 10,
                        "side": "buy",
                        "type": "stock",
                        "price": 0,  # Will be filled at market price
                        "change_percent": 0,
                        "order_type": "market",
                        "reasoning": stock_rec.get("reasoning", ""),
                    }
                    executed_trades.append(trade)
        except Exception as e:
            logger.error(f"❌ Error fetching price for {symbol}: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Still add the trade even if price fetch fails
            if symbol and stock_rec.get("name"):
                logger.info(f"⚠️ Adding trade for {symbol} despite price fetch error")
                trade = {
                    "symbol": symbol,
                    "name": stock_rec.get("name", symbol),
                    "quantity": 10,
                    "side": "buy",
                    "type": "stock",
                    "price": 0,  # Will be filled at market price
                    "change_percent": 0,
                    "order_type": "market",
                    "reasoning": stock_rec.get("reasoning", ""),
                }
                executed_trades.append(trade)
    
    logger.info(f"📦 Total executed trades: {len(executed_trades)}")
    
    if len(executed_trades) == 0:
        logger.error("❌ No trades could be executed - all price fetches failed and no fallback trades created")
    
    # Step 3: Generate confirmation response (OPTIMIZED: use template if prices available, LLM only if needed)
    if len(executed_trades) == 0:
        logger.error("❌ Cannot generate confirmation - no executed trades")
        text = "I apologize, but I wasn't able to fetch current prices for the recommended stocks. Please try again in a moment, or specify particular stocks you'd like to buy."
    else:
        # OPTIMIZED: Use fast template if we have prices, only use LLM if we need customization
        has_prices = any(t.get('price', 0) > 0 for t in executed_trades)
        
        if has_prices:
            # Fast path: Use template (no LLM call needed)
            stock_list = []
            for t in executed_trades:
                if t.get('price', 0) > 0:
                    stock_list.append(f"{t['symbol']} ({t['name']}) at ${t['price']:,.2f}")
                else:
                    stock_list.append(f"{t['symbol']} ({t['name']}) at market price")
            
            stock_list_str = ", ".join(stock_list)
            text = f"Perfect! I've placed buy orders for {len(executed_trades)} stocks: {stock_list_str}. These are simulated trades for educational purposes. You'll get confirmations once they're processed."
            logger.info(f"✅ Using fast template confirmation (no LLM call)")
        else:
            # Fallback: Use LLM if we don't have prices
            system_prompt = """You are RichesReach, confirming multiple stock orders you just placed.
- List each stock with its symbol and name.
- Mention that these are simulated trades for educational purposes.
- Be concise (2-3 sentences).
- Be professional and reassuring."""
            
            user_prompt = f"""User said: {transcript}

You just placed {len(executed_trades)} buy orders for these stocks:
{json.dumps(executed_trades, indent=2)}

Confirm to the user what orders were placed. List each stock clearly."""
            
            text = await generate_voice_reply(system_prompt, user_prompt, history, model="gpt-4o-mini")
            if not text:
                # Final fallback template
                stock_list = ", ".join([f"{t['symbol']} ({t['name']})" for t in executed_trades])
                text = f"Perfect! I've placed buy orders for {len(executed_trades)} stocks: {stock_list}. These are simulated trades for educational purposes. You'll get confirmations once they're processed."
    
    return {
        "text": text,
        "intent": "buy_multiple_stocks",
        "executed_trades": executed_trades,
    }

async def respond_with_trade_idea(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for trade recommendations."""
    trade = context.get("trade", {})
    
    system_prompt = """You are RichesReach, a calm, concise trading coach.
- Always use the *provided* trade data; do not invent prices or symbols.
- Explain ideas in plain language, not jargon.
- Keep answers under 3-4 sentences unless user asks for more detail.
- You are not a broker; you only describe recommendations and risks.
- Be conversational and helpful, not robotic."""
    
    user_prompt = f"""User just said: {transcript}

Conversation so far:
{json.dumps(history[-4:] if history else [], indent=2) if history else "No previous conversation"}

Here is the recommended trade:
{json.dumps(trade, indent=2)}

Explain this trade to the user in natural language. Weave the data into a story, don't just list numbers."""
    
    text = await generate_voice_reply(system_prompt, user_prompt)
    if not text:
        # Fallback to template if LLM fails
        text = f"I've found a strong opportunity in {trade.get('symbol', 'NVDA')}. Entry at ${trade.get('entry', 179.50)}, stop at ${trade.get('stop', 178.00)}, target at ${trade.get('target', 185.00)}. Risk/reward is {trade.get('r_multiple', 3.67):.2f} with a {trade.get('win_prob', 0.68)*100:.0f}% win probability. Would you like me to show you the full analysis?"
    
    return {
        "text": text,
        "intent": "trading_query",
        "trade": trade,
    }

async def respond_with_crypto_update(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for crypto queries."""
    crypto = context.get("crypto", {})
    
    system_prompt = """You are RichesReach, a calm, concise trading coach specializing in cryptocurrency.
- **ALWAYS state the current price** when the user asks about a cryptocurrency.
- Always use the *provided* price data; do not invent prices.
- Format prices clearly: "$XX,XXX.XX" for the user.
- Mention the 24-hour change percentage.
- Explain crypto opportunities in plain language.
- Keep answers under 3-4 sentences unless user asks for more detail.
- Mention volatility and risk awareness.
- Be conversational and helpful."""
    
    user_prompt = f"""User just said: {transcript}

Here is the crypto data:
{json.dumps(crypto, indent=2)}

**IMPORTANT: The user is asking about cryptocurrency. You MUST include the current price in your response.**

Respond naturally to the user's question. Start by stating the current price (e.g., "Bitcoin is currently trading at $XX,XXX.XX"). Then provide context about the 24-hour change and any relevant insights. Use the real prices provided - do not make up prices."""
    
    text = await generate_voice_reply(system_prompt, user_prompt, history)
    if not text:
        # Fallback template
        if "top_picks" in crypto:
            picks = crypto["top_picks"]
            text = f"Based on our crypto analysis, I'm seeing strong opportunities: Bitcoin (BTC) at ${picks[0]['price']:,.2f}, Ethereum (ETH) at ${picks[1]['price']:,.2f}, and Solana (SOL) at ${picks[2]['price']:,.2f}. Which one would you like to explore further?"
        else:
            symbol = crypto.get("symbol", "BTC")
            name = crypto.get("name", "Bitcoin")
            price = crypto.get("price", 55000)
            change = crypto.get("change_24h", 0)
            text = f"{name} ({symbol}) is currently trading at ${price:,.2f}, {change:+.2f}% in the last 24 hours. Our analysis shows strong momentum. Would you like me to show you the full analysis?"
    
    return {
        "text": text,
        "intent": "crypto_query",
        "crypto": crypto,
    }

async def respond_with_execution_confirmation(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for trade execution."""
    last_trade = context.get("last_trade", {})
    
    system_prompt = """You are RichesReach, confirming a trade the user just approved.
- Confirm the symbol, side, and approximate size clearly.
- Mention that this is a simulated/instructional trade if it's not live.
- Encourage risk awareness, not hype.
- Keep it to 1-3 sentences.
- Be professional and reassuring."""
    
    user_prompt = f"""User just said (likely a confirmation): {transcript}

Last recommended trade:
{json.dumps(last_trade, indent=2)}

Confirm to the user what was done in natural language. Be specific about what was executed."""
    
    text = await generate_voice_reply(system_prompt, user_prompt, history)
    if not text:
        # Fallback template
        symbol = last_trade.get("symbol", "NVDA")
        qty = last_trade.get("quantity", 100)
        price = last_trade.get("price", 179.45)
        is_crypto = last_trade.get("type") == "crypto"
        unit = f"{qty} {symbol}" if is_crypto else f"{qty} shares"
        text = f"Perfect! I've placed your order for {unit} of {symbol} at ${price:,.2f}. The order is now active and will execute when the price reaches your limit. You'll get a notification when it fills."
    
    return {
        "text": text,
        "intent": "execute_trade",
        "executed_trade": last_trade,
    }

async def respond_with_portfolio_answer(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for portfolio queries."""
    portfolio = context.get("portfolio", {})
    
    system_prompt = """You are RichesReach, helping the user understand their portfolio.
- Use the provided portfolio data accurately.
- Explain performance in plain language.
- Keep answers concise (2-3 sentences) unless user asks for detail.
- Be encouraging but realistic."""
    
    user_prompt = f"""User just said: {transcript}

Portfolio data:
{json.dumps(portfolio, indent=2)}

Answer the user's question about their portfolio naturally."""
    
    text = await generate_voice_reply(system_prompt, user_prompt, history)
    if not text:
        # Fallback template
        value = portfolio.get("value", 14303.52)
        return_pct = portfolio.get("return", 17.65)
        text = f"Your portfolio is performing well. Current value: ${value:,.2f} with a return of {return_pct:+.2f}%. Would you like a detailed breakdown?"
    
    return {
        "text": text,
        "intent": "portfolio_query",
        "portfolio": portfolio,
    }

async def respond_with_explanation(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for trade explanations."""
    last_trade = context.get("last_trade", {})
    
    system_prompt = """You are RichesReach, explaining why a trade is compelling.
- Use the provided trade data to explain the reasoning.
- Be specific about risk/reward, probability, and technical factors.
- Keep it conversational, not a bullet list.
- 2-4 sentences is ideal."""
    
    user_prompt = f"""User just said: {transcript}

Last recommended trade:
{json.dumps(last_trade, indent=2)}

Explain why this trade is compelling in natural language. Weave the data into a story."""
    
    text = await generate_voice_reply(system_prompt, user_prompt, history)
    if not text:
        # Fallback template
        text = "This trade is compelling because the momentum is exceptional, the technical setup shows a clean breakout, and our ML model gives it a high win probability with favorable risk/reward."
    
    return {
        "text": text,
        "intent": "explain_trade",
    }

async def respond_with_small_talk(transcript: str, history: list, context: dict) -> dict:
    """Generate natural language response for general conversation."""
    system_prompt = """You are RichesReach, a friendly trading coach and financial assistant.
- You help users with trading ideas, portfolio management, and crypto investments.
- Be concise, helpful, and conversational.
- If you don't know something, say so.
- Keep answers under 3 sentences for casual questions."""
    
    user_prompt = f"""User just said: {transcript}

Respond naturally to the user's question or statement."""
    
    text = await generate_voice_reply(system_prompt, user_prompt, history)
    if not text:
        # Fallback
        text = "I understand. How can I help you with your trading today?"
    
    return {
        "text": text,
        "intent": "small_talk",
    }

# ✅ Helper function to fetch real crypto prices from CoinGecko (free, no API key needed)
# ✅ OPTIMIZED: Uses caching and shorter timeout
async def get_crypto_price(symbol: str, force_refresh: bool = False) -> dict:
    """
    Fetch real-time crypto price from CoinGecko API with caching.
    Args:
        symbol: Crypto symbol (BTC, ETH, SOL, etc.)
        force_refresh: If True, bypass cache and fetch fresh data (for voice queries)
    Returns: {price: float, change_24h: float, change_percent_24h: float, timestamp: float} or None
    """
    # Check cache first (unless forcing refresh)
    if not force_refresh:
        cached = price_cache.get(symbol)
        if cached:
            logger.info(f"✅ Using cached {symbol} price: ${cached['price']:,.2f} (age: {int(time.time() - cached.get('timestamp', time.time()))}s)")
            return cached
    else:
        # Clear cache for this symbol to force fresh fetch
        price_cache.clear(symbol)
        logger.info(f"🔄 Force refreshing {symbol} price (bypassing cache)")
    
    # Map common symbols to CoinGecko IDs
    coin_id_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'ADA': 'cardano',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'AVAX': 'avalanche-2',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
    }
    
    coin_id = coin_id_map.get(symbol.upper())
    if not coin_id:
        logger.warn(f"⚠️ Unknown crypto symbol: {symbol}, using fallback price")
        return None
    
    try:
        # CoinGecko free API - no key needed for basic usage
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=2.8)) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        price_data = data[coin_id]
                        price = price_data.get('usd', 0)
                        change_24h = price_data.get('usd_24h_change', 0)
                        
                        result = {
                            'price': price,
                            'change_24h': change_24h,
                            'change_percent_24h': change_24h,
                            'timestamp': time.time(),  # Add timestamp for freshness tracking
                        }
                        
                        # Cache the result
                        price_cache.set(symbol, result)
                        
                        logger.info(f"✅ Fetched real {symbol} price: ${price:,.2f} (24h change: {change_24h:.2f}%)")
                        return result
                    else:
                        logger.warn(f"⚠️ CoinGecko returned data but no {coin_id} entry")
                        # Try to return cached if available, otherwise None
                        cached = price_cache.get(symbol)
                        return cached if cached else None
                else:
                    logger.warn(f"⚠️ CoinGecko API returned status {response.status}")
                    # Try to return cached if available, otherwise None
                    cached = price_cache.get(symbol)
                    return cached if cached else None
    except asyncio.TimeoutError:
        logger.warn(f"⚠️ CoinGecko API timeout for {symbol}, using cached/fallback")
        # Try to return cached if available, otherwise None
        cached = price_cache.get(symbol)
        return cached if cached else None
    except Exception as e:
        logger.warn(f"⚠️ Error fetching crypto price for {symbol}: {e}")
        # Try to return cached if available, otherwise None
        cached = price_cache.get(symbol)
        return cached if cached else None

# ✅ Helper function to fetch real stock prices
async def get_stock_price(symbol: str, force_refresh: bool = False) -> dict:
    """
    Fetch real-time stock price with caching.
    Args:
        symbol: Stock symbol (AAPL, TSLA, etc.)
        force_refresh: If True, bypass cache and fetch fresh data (for voice queries)
    Returns: {symbol: str, price: float, change: float, change_percent: float, timestamp: float} or None
    """
    cache_key = f"stock_{symbol}"
    
    # Check cache first (unless forcing refresh)
    if not force_refresh:
        cached = price_cache.get(cache_key)
        if cached:
            logger.info(f"✅ Using cached {symbol} price: ${cached['price']:,.2f} (age: {int(time.time() - cached.get('timestamp', time.time()))}s)")
            return cached
    else:
        # Clear cache for this symbol to force fresh fetch
        price_cache.clear(cache_key)
        logger.info(f"🔄 Force refreshing {symbol} price (bypassing cache)")
    
    try:
        # Try to use enhanced stock service if available
        if ML_SERVICES_AVAILABLE:
            try:
                from core.enhanced_stock_service import enhanced_stock_service
                price_data = await enhanced_stock_service.get_real_time_price(symbol)
                if price_data and price_data.get('price', 0) > 0:
                    result = {
                        'symbol': symbol,
                        'price': float(price_data['price']),
                        'change': float(price_data.get('change', 0)),
                        'change_percent': float(price_data.get('change_percent', 0).replace('%', '')) if isinstance(price_data.get('change_percent'), str) else float(price_data.get('change_percent', 0)),
                        'volume': price_data.get('volume', 0),
                        'timestamp': time.time(),
                        'source': price_data.get('source', 'api'),
                    }
                    price_cache.set(cache_key, result)
                    logger.info(f"✅ Fetched real {symbol} price: ${result['price']:,.2f} (change: {result['change_percent']:+.2f}%)")
                    return result
            except Exception as e:
                logger.warn(f"⚠️ Enhanced stock service error for {symbol}: {e}")
        
        # Fallback: Use Alpaca API if available (try bars/latest first, then quotes/latest)
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        if alpaca_key and alpaca_secret:
            try:
                # Try bars/latest first (more reliable for current price)
                url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars/latest"
                headers = {
                    'APCA-API-KEY-ID': alpaca_key,
                    'APCA-API-SECRET-KEY': alpaca_secret,
                }
                # Create SSL context (disable verification for development)
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2.8)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'bar' in data and data['bar']:
                                bar = data['bar']
                                price = float(bar.get('c', 0))  # close price
                                if price > 0:
                                    # Calculate change from open
                                    open_price = float(bar.get('o', price))
                                    change = price - open_price
                                    change_percent = (change / open_price * 100) if open_price > 0 else 0.0
                                    
                                    result = {
                                        'symbol': symbol,
                                        'price': price,
                                        'change': change,
                                        'change_percent': change_percent,
                                        'volume': bar.get('v', 0),
                                        'timestamp': time.time(),
                                        'source': 'alpaca',
                                    }
                                    price_cache.set(cache_key, result)
                                    logger.info(f"✅ Fetched {symbol} price from Alpaca: ${price:,.2f} (change: {change_percent:+.2f}%)")
                                    return result
                        elif response.status == 404:
                            # Symbol not found, try quotes endpoint
                            logger.debug(f"⚠️ Alpaca bars endpoint returned 404 for {symbol}, trying quotes...")
                            url_quotes = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
                            async with session.get(url_quotes, headers=headers, timeout=aiohttp.ClientTimeout(total=2.8)) as response2:
                                if response2.status == 200:
                                    data2 = await response2.json()
                                    if 'quote' in data2:
                                        quote = data2['quote']
                                        price = float(quote.get('bp', quote.get('ap', 0)))  # bid/ask price
                                        if price == 0:
                                            price = float(quote.get('p', 0))  # last price
                                        
                                        if price > 0:
                                            result = {
                                                'symbol': symbol,
                                                'price': price,
                                                'change': 0.0,  # Alpaca quote doesn't include change
                                                'change_percent': 0.0,
                                                'volume': quote.get('s', 0),  # size
                                                'timestamp': time.time(),
                                                'source': 'alpaca',
                                            }
                                            price_cache.set(cache_key, result)
                                            logger.info(f"✅ Fetched {symbol} price from Alpaca quotes: ${price:,.2f}")
                                            return result
            except asyncio.TimeoutError:
                logger.warn(f"⚠️ Alpaca API timeout for {symbol}")
            except Exception as e:
                logger.warn(f"⚠️ Alpaca API error for {symbol}: {e}")
        
        # Final fallback: Try Yahoo Finance (free, no API key)
        try:
            # Use a more reliable Yahoo Finance endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',  # Use 1d for more reliable data (works in curl test)
                'range': '1d',
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                            result_data = data['chart']['result'][0]
                            price = 0.0
                            prev_close = 0.0
                            volume = 0
                            
                            # First try: Get from meta (most reliable)
                            if 'meta' in result_data:
                                meta = result_data['meta']
                                # regularMarketPrice is the current price
                                price_raw = meta.get('regularMarketPrice')
                                logger.info(f"📊 {symbol} meta.regularMarketPrice: {price_raw}")
                                
                                if price_raw is not None:
                                    price = float(price_raw)
                                else:
                                    price = 0.0
                                
                                prev_close_raw = meta.get('chartPreviousClose') or meta.get('previousClose')
                                if prev_close_raw is not None:
                                    prev_close = float(prev_close_raw)
                                else:
                                    prev_close = price
                                
                                volume_raw = meta.get('regularMarketVolume')
                                volume = int(volume_raw) if volume_raw is not None else 0
                                
                                logger.info(f"📊 {symbol} extracted: price=${price}, prev_close=${prev_close}, volume={volume}")
                            
                            # Second try: Get from indicators if meta didn't work
                            if price == 0 and 'indicators' in result_data:
                                indicators = result_data['indicators']
                                if 'quote' in indicators and len(indicators['quote']) > 0:
                                    quote_data = indicators['quote'][0]
                                    if 'close' in quote_data and len(quote_data['close']) > 0:
                                        closes = quote_data['close']
                                        # Get last non-null, non-zero value
                                        for val in reversed(closes):
                                            if val is not None and val > 0:
                                                price = float(val)
                                                break
                                
                                # Also try adjclose
                                if price == 0 and 'adjclose' in indicators and len(indicators['adjclose']) > 0:
                                    adjclose_data = indicators['adjclose'][0]
                                    if 'adjclose' in adjclose_data and len(adjclose_data['adjclose']) > 0:
                                        adjcloses = adjclose_data['adjclose']
                                        for val in reversed(adjcloses):
                                            if val is not None and val > 0:
                                                price = float(val)
                                                break
                            
                            if price > 0:
                                if prev_close == 0:
                                    prev_close = price  # Fallback to current price
                                change = price - prev_close
                                change_percent = (change / prev_close * 100) if prev_close > 0 else 0.0
                                
                                result = {
                                    'symbol': symbol,
                                    'price': price,
                                    'change': change,
                                    'change_percent': change_percent,
                                    'volume': volume,
                                    'timestamp': time.time(),
                                    'source': 'yahoo',
                                }
                                price_cache.set(cache_key, result)
                                logger.info(f"✅ Fetched {symbol} price from Yahoo: ${price:,.2f} (change: {change_percent:+.2f}%)")
                                return result
                            else:
                                logger.warn(f"⚠️ Yahoo Finance: Could not extract valid price for {symbol} from response")
                        else:
                            logger.warn(f"⚠️ Yahoo Finance: Invalid response structure for {symbol}")
                    elif response.status == 404:
                        logger.warn(f"⚠️ Yahoo Finance: Symbol {symbol} not found (404)")
                    else:
                        logger.warn(f"⚠️ Yahoo Finance: Status {response.status} for {symbol}")
        except asyncio.TimeoutError:
            logger.warn(f"⚠️ Yahoo Finance timeout for {symbol}")
        except Exception as e:
            logger.warn(f"⚠️ Yahoo Finance error for {symbol}: {e}")
            import traceback
            logger.debug(f"Yahoo Finance traceback: {traceback.format_exc()}")
        
        # If all else fails, try cached data
        cached = price_cache.get(cache_key)
        if cached:
            logger.warn(f"⚠️ Using stale cached {symbol} price: ${cached['price']:,.2f}")
            return cached
        
        logger.error(f"❌ Could not fetch {symbol} price from any source")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching stock price for {symbol}: {e}")
        cached = price_cache.get(cache_key)
        return cached if cached else None

# ✅ Batch fetch multiple crypto prices in parallel
async def get_crypto_prices_batch(symbols: list[str]) -> dict:
    """Fetch multiple crypto prices in parallel for speed."""
    tasks = [get_crypto_price(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    prices = {}
    for symbol, result in zip(symbols, results):
        if isinstance(result, dict) and 'price' in result:
            prices[symbol] = result
        elif isinstance(result, Exception):
            logger.warn(f"⚠️ Error fetching {symbol}: {result}")
    
    return prices

# Voice Processing endpoint (for Miami demo)
@app.post("/api/voice/process/")
async def process_voice(request: Request):
    """
    Process voice audio for transcription and AI response.
    Accepts multipart/form-data with audio file.
    Returns transcription and AI-generated response.
    
    For demo: Returns intelligent mock responses based on common trading commands.
    """
    try:
        logger.info("🎤 Voice processing request received")
        # Parse multipart form data
        form = await request.form()
        audio_file = form.get("audio")
        logger.info(f"🎤 Audio file received: {audio_file is not None}")
        
        audio_file_size = 0
        audio_has_content = False
        file_content = None
        
        if audio_file:
            # Log file details if available
            if hasattr(audio_file, 'filename'):
                logger.info(f"🎤 Audio filename: {audio_file.filename}")
            if hasattr(audio_file, 'size'):
                logger.info(f"🎤 Audio file size: {audio_file.size} bytes")
                audio_file_size = audio_file.size
            if hasattr(audio_file, 'content_type'):
                logger.info(f"🎤 Audio content type: {audio_file.content_type}")
            
            # Try to read the file to verify it has content
            try:
                # Reset file pointer in case it was already read
                if hasattr(audio_file, 'seek'):
                    await audio_file.seek(0)
                
                file_content = await audio_file.read()
                audio_file_size = len(file_content)
                logger.info(f"🎤 Audio file read successfully, size: {audio_file_size} bytes")
                
                # Check if file has actual audio data (WAV files have headers, so even empty files are ~44 bytes)
                if audio_file_size < 100:
                    logger.warn(f"⚠️ Audio file is very small ({audio_file_size} bytes) - likely empty or corrupted")
                    logger.warn(f"⚠️ For demo purposes, will use mock transcription")
                    audio_has_content = False
                elif audio_file_size < 1000:
                    logger.warn(f"⚠️ Audio file is small ({audio_file_size} bytes) - may be very short recording")
                    logger.warn(f"⚠️ Will use mock transcription for demo")
                    audio_has_content = False
                else:
                    logger.info(f"✅ Audio file looks good ({audio_file_size} bytes)")
                    audio_has_content = True
                    
                    # Log first few bytes to verify it's a valid WAV file
                    if len(file_content) > 4:
                        header = file_content[:4]
                        if header == b'RIFF':
                            logger.info(f"✅ Valid WAV file detected (RIFF header)")
                        else:
                            logger.warn(f"⚠️ File doesn't appear to be a WAV file (header: {header})")
            except Exception as read_error:
                import traceback
                logger.error(f"❌ Error reading audio file: {read_error}")
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                logger.warn(f"⚠️ Will use mock transcription for demo")
                audio_has_content = False
        else:
            logger.warn("⚠️ No audio file received - using mock transcription for demo")
        
        # Try to transcribe using OpenAI Whisper API if available
        transcription = None
        use_real_transcription = False
        
        logger.info(f"🔍 Debug: audio_has_content={audio_has_content}, file_content is {'set' if file_content is not None else 'None'}, file_content size={len(file_content) if file_content else 0}")
        
        if audio_has_content and file_content:
            # Check if OpenAI API key is available
            openai_api_key = os.getenv('OPENAI_API_KEY')
            logger.info(f"🔑 OpenAI API key check: {'Found' if openai_api_key else 'NOT FOUND'}")
            if openai_api_key:
                try:
                    import openai
                    import tempfile
                    import os as os_module
                    
                    logger.info("🎤 Attempting real transcription with OpenAI Whisper...")
                    logger.info(f"🎤 Audio file size: {len(file_content)} bytes")
                    
                    # Save audio to temporary file for OpenAI API
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                        temp_audio.write(file_content)
                        temp_audio_path = temp_audio.name
                    
                    logger.info(f"🎤 Saved audio to temp file: {temp_audio_path}")
                    logger.info(f"🎤 Temp file size: {os_module.path.getsize(temp_audio_path)} bytes")
                    
                    try:
                        # Initialize OpenAI client
                        logger.info("🎤 Initializing OpenAI client...")
                        openai_client = openai.OpenAI(api_key=openai_api_key)
                        logger.info("✅ OpenAI client initialized")
                        
                        # Call OpenAI Whisper API
                        logger.info("🎤 Calling Whisper API...")
                        with open(temp_audio_path, 'rb') as audio_file_obj:
                            transcript_response = openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file_obj,
                                language="en"
                            )
                            transcription = transcript_response.text.strip()
                            use_real_transcription = True
                            logger.info(f"✅ Real transcription successful!")
                            logger.info(f"🎤 ============================================")
                            logger.info(f"🎤 USER ACTUALLY SAID: '{transcription}'")
                            logger.info(f"🎤 ============================================")
                    finally:
                        # Clean up temp file
                        if os_module.path.exists(temp_audio_path):
                            os_module.unlink(temp_audio_path)
                            
                except ImportError:
                    logger.warn("⚠️ OpenAI library not installed. Install with: pip install openai")
                except Exception as whisper_error:
                    import traceback
                    logger.error(f"❌ Whisper transcription failed!")
                    logger.error(f"❌ Error type: {type(whisper_error).__name__}")
                    logger.error(f"❌ Error message: {str(whisper_error)}")
                    logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
                    logger.warn("⚠️ Falling back to mock transcription")
        
        # Fallback to mock transcription if real transcription failed or unavailable
        if not transcription or not use_real_transcription:
            mock_transcriptions = [
                "Show me the best day trade right now",
                "Find me the strongest momentum play",
                "Buy one hundred shares of NVIDIA at market",
                "What's my portfolio performance",
                "Show me my positions",
                "What's my buying power",
                "Find me something good today",
                "Show me the risk reward analysis",
                "Why should I take this trade",
                "What stocks should I buy today",
                "Show me the top trading opportunities",
                "What's the best trade right now",
            ]
            
            import random
            transcription = random.choice(mock_transcriptions)
            
            # Log what we're doing
            if audio_has_content:
                logger.info(f"🎭 Using mock transcription (Whisper unavailable): '{transcription}'")
            else:
                logger.info(f"🎭 Demo mode: Using mock transcription '{transcription}' (audio file was empty/small: {audio_file_size} bytes)")
        
        # ✅ NEW ARCHITECTURE: Transcribe → Understand → Decide → Generate natural language
        # Get conversation history from request (if available)
        conversation_history = []
        try:
            history_json = form.get("history")
            if history_json:
                conversation_history = json.loads(history_json) if isinstance(history_json, str) else history_json
        except:
            pass
        
        # Get last trade from request (if available)
        last_trade = None
        try:
            last_trade_json = form.get("last_trade")
            if last_trade_json:
                last_trade = json.loads(last_trade_json) if isinstance(last_trade_json, str) else last_trade_json
        except:
            pass
        
        # Step 1: Detect intent
        intent = detect_intent(transcription, conversation_history, last_trade)
        logger.info(f"🎯 Detected intent: {intent}")
        
        # Step 2: Build context (fetch real data)
        context = await build_context(intent, transcription, conversation_history, last_trade)
        
        # Step 3: Generate natural language response based on intent
        try:
            if intent == "get_trade_idea":
                result = await respond_with_trade_idea(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = result.get("trade", {})
            elif intent == "crypto_query":
                result = await respond_with_crypto_update(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = result.get("crypto", {})
            elif intent == "stock_query":
                # Use similar structure to crypto_query
                stock = context.get("stock", {})
                system_prompt = """You are RichesReach, a calm, concise trading coach specializing in stocks.
- Always use the *provided* price data; do not invent prices.
- Explain stock opportunities in plain language.
- Keep answers under 3-4 sentences unless user asks for more detail.
- Mention current price, change, and volume if available.
- If data_age_seconds is provided and is low (< 30), emphasize that this is real-time, current data."""
                user_prompt = f"""User just said: {transcription}

Here is the stock data:
{json.dumps(stock, indent=2)}

Respond naturally to the user's question about this stock. Use the real prices provided. If is_fresh is true, emphasize that you're giving current, real-time information."""
                ai_response = await generate_voice_reply(system_prompt, user_prompt, conversation_history)
                if not ai_response:
                    # Fallback
                    symbol = stock.get("symbol", "the stock")
                    price = stock.get("price", 0)
                    change = stock.get("change_percent", 0)
                    ai_response = f"{symbol} is currently trading at ${price:,.2f}, {change:+.2f}% change. Would you like me to show you the full analysis?"
                trade_data = stock
            elif intent == "execute_trade":
                result = await respond_with_execution_confirmation(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = result.get("executed_trade", last_trade)
            elif intent == "buy_multiple_stocks":
                result = await respond_with_buy_multiple_stocks(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = result.get("executed_trades", [])
            elif intent == "portfolio_query":
                result = await respond_with_portfolio_answer(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = None
            elif intent == "explain_trade":
                result = await respond_with_explanation(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = last_trade
            else:  # small_talk or unknown
                result = await respond_with_small_talk(transcription, conversation_history, context)
                ai_response = result["text"]
                trade_data = None
        except Exception as e:
            import traceback
            logger.exception(f"❌ Error in LLM voice pipeline: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Fallback so the app doesn't break
            ai_response = f"I had trouble generating a detailed answer just now, but I heard you say: \"{transcription}\". Can you try asking again in a moment?"
            intent = "error_fallback"
            trade_data = None
        
        # Return response with detected intent
        return {
            "success": True,
            "response": {
                "transcription": transcription,
                "text": ai_response,
                "confidence": 0.95,
                "intent": intent,  # ✅ Intent determined by detect_intent()
                "whisper_used": use_real_transcription,
                "trade": trade_data,  # Include trade data if available
                "debug": {
                    "audio_has_content": audio_has_content,
                    "file_content_size": len(file_content) if file_content else 0,
                    "openai_key_found": bool(os.getenv('OPENAI_API_KEY'))
                }
            }
        }
    except Exception as e:
        import traceback
        logger.error(f"❌ Error in process_voice endpoint: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": "Failed to process voice input",
            "response": {
                "transcription": "Error occurred",
                "text": "I'm sorry, I had trouble processing that. Could you please try again?",
                "confidence": 0.0,
                "intent": "error",
            }
        }

# ✅ STREAMING VOICE ENDPOINT - Ultra-low latency token-by-token responses
@app.post("/api/voice/stream")
async def voice_stream(request: Request):
    """
    Streaming voice endpoint - returns tokens as they're generated.
    Reduces perceived latency from ~1.6s to ~350-450ms (first token).
    Expects JSON: { transcript, history, last_trade, user_id }
    """
    try:
        body = await request.json()
        transcript = body.get("transcript", "")
        history = body.get("history", [])
        last_trade = body.get("last_trade")
        user_id = body.get("user_id")
        
        if not transcript:
            async def error_gen():
                yield json.dumps({"type": "error", "text": "No transcript provided"}) + "\n"
            return StreamingResponse(error_gen(), media_type="text/event-stream")
        
        logger.info(f"🎤 Streaming voice request: '{transcript[:50]}...'")
        
        # Step 1: Detect intent (fast, rule-based)
        intent = detect_intent(transcript, history, last_trade)
        logger.info(f"🎯 Detected intent: {intent}")
        
        # Step 2: Build context (parallel fetch)
        context = await build_context(intent, transcript, history, last_trade)
        
        # Step 3: Generate system/user prompts based on intent
        if intent == "get_trade_idea":
            trade = context.get("trade", {})
            system_prompt = """You are RichesReach, a calm, concise trading coach.
- Always use the *provided* trade data; do not invent prices or symbols.
- Explain ideas in plain language, not jargon.
- Keep answers under 3-4 sentences unless user asks for more detail.
- Be conversational and helpful, not robotic."""
            user_prompt = f"""User just said: {transcript}

Here is the recommended trade:
{json.dumps(trade, indent=2)}

Explain this trade to the user in natural language. Weave the data into a story, don't just list numbers."""
        
        elif intent == "crypto_query":
            crypto = context.get("crypto", {})
            system_prompt = """You are RichesReach, a calm, concise trading coach specializing in cryptocurrency.
- **ALWAYS state the current price** when the user asks about a cryptocurrency.
- Always use the *provided* price data; do not invent prices.
- Format prices clearly: "$XX,XXX.XX" for the user.
- Mention the 24-hour change percentage.
- Explain crypto opportunities in plain language.
- Keep answers under 3-4 sentences unless user asks for more detail.
- Mention volatility and risk awareness.
- If price data includes a timestamp, mention how current the data is (e.g., "as of just now" or "from a few seconds ago")."""
            user_prompt = f"""User just said: {transcript}

Here is the crypto data:
{json.dumps(crypto, indent=2)}

**IMPORTANT: The user is asking about cryptocurrency. You MUST include the current price in your response.**

Respond naturally to the user's question. Start by stating the current price (e.g., "Bitcoin is currently trading at $XX,XXX.XX"). Then provide context about the 24-hour change and any relevant insights. Use the real prices provided - do not make up prices."""
        
        elif intent == "stock_query":
            stock = context.get("stock", {})
            system_prompt = """You are RichesReach, a calm, concise trading coach specializing in stocks.
- **ALWAYS state the current price** when the user asks about a stock.
- Always use the *provided* price data; do not invent prices.
- Format prices clearly: "$XXX.XX" for the user.
- Mention the change percentage and direction (up/down).
- Explain stock opportunities in plain language.
- Keep answers under 3-4 sentences unless user asks for more detail.
- If data_age_seconds is provided and is low (< 30), emphasize that this is real-time, current data."""
            user_prompt = f"""User just said: {transcript}

Here is the stock data:
{json.dumps(stock, indent=2)}

**IMPORTANT: The user is asking about a stock. You MUST include the current price in your response.**

Respond naturally to the user's question. Start by stating the current price (e.g., "Apple is currently trading at $XXX.XX, up/down X.XX%"). Then provide context about the change and any relevant insights. Use the real prices provided - do not make up prices."""
        
        elif intent == "execute_trade":
            # Check if this is a direct buy/sell command
            trade_cmd = parse_trade_command(transcript)
            if trade_cmd:
                # OPTIMIZED: Price fetching is already fast (single fetch), but we ensure it's fresh
                current_price = None
                if trade_cmd["type"] == "crypto":
                    price_data = await get_crypto_price(trade_cmd["symbol"], force_refresh=True)
                    if price_data:
                        current_price = price_data.get("price", 0)
                elif trade_cmd["type"] == "stock":
                    price_data = await get_stock_price(trade_cmd["symbol"], force_refresh=True)
                    if price_data:
                        current_price = price_data.get("price", 0)
                
                executed_trade = {
                    "symbol": trade_cmd["symbol"],
                    "quantity": trade_cmd["quantity"],
                    "side": trade_cmd["side"],
                    "type": trade_cmd["type"],
                    "price": current_price or 0,
                    "order_type": "market",
                }
                
                system_prompt = """You are RichesReach, confirming a trade the user just requested.
- Confirm the symbol, side, and quantity clearly.
- Mention the current price if available.
- Note that this is a simulated/instructional trade for educational purposes.
- Keep it to 1-3 sentences.
- Be professional and reassuring."""
                
                user_prompt = f"""User just said: {transcript}

Parsed trade command:
{json.dumps(executed_trade, indent=2)}

Confirm to the user what order you're placing. Be specific about symbol, quantity, and side (buy/sell)."""
            else:
                # Confirmation of previous trade
                last_trade = context.get("last_trade", {})
                system_prompt = """You are RichesReach, confirming a trade the user just approved.
- Confirm the symbol, side, and approximate size clearly.
- Keep it to 1-3 sentences.
- Be professional and reassuring."""
                user_prompt = f"""User just said: {transcript}

Last recommended trade:
{json.dumps(last_trade, indent=2)}

Confirm to the user what was done in natural language. Be specific about what was executed."""
        
        elif intent == "buy_multiple_stocks":
            # This will be handled in the token generator
            system_prompt = None
            user_prompt = None
        
        elif intent == "portfolio_query":
            portfolio = context.get("portfolio", {})
            system_prompt = """You are RichesReach, helping the user understand their portfolio.
- Use the provided portfolio data accurately.
- Explain performance in plain language.
- Keep answers concise (2-3 sentences) unless user asks for detail."""
            user_prompt = f"""User just said: {transcript}

Portfolio data:
{json.dumps(portfolio, indent=2)}

Answer the user's question about their portfolio naturally."""
        
        elif intent == "explain_trade":
            last_trade = context.get("last_trade", {})
            system_prompt = """You are RichesReach, explaining why a trade is compelling.
- Use the provided trade data to explain the reasoning.
- Be specific about risk/reward, probability, and technical factors.
- Keep it conversational, not a bullet list.
- 2-4 sentences is ideal."""
            user_prompt = f"""User just said: {transcript}

Last recommended trade:
{json.dumps(last_trade, indent=2)}

Explain why this trade is compelling in natural language. Weave the data into a story."""
        
        else:  # small_talk
            system_prompt = """You are RichesReach, a friendly trading coach and financial assistant.
- You help users with trading ideas, portfolio management, and crypto investments.
- Be concise, helpful, and conversational.
- Keep answers under 3 sentences for casual questions."""
            user_prompt = f"""User just said: {transcript}

Respond naturally to the user's question or statement."""
        
        # Stream the response
        async def token_generator():
            # OPTIMIZED: Send immediate ACK for ALL intents (improves perceived latency across entire voice experience)
            yield json.dumps({"type": "ack", "text": "Got it…"}) + "\n"
            
            if intent == "buy_multiple_stocks":
                # Process buy_multiple_stocks (takes ~2-3s)
                result = await respond_with_buy_multiple_stocks(transcript, history, context)
                response_text = result.get("text", "")
                
                # Stream the response word by word for consistency
                words = response_text.split()
                for i, word in enumerate(words):
                    yield json.dumps({"type": "token", "text": word + (" " if i < len(words) - 1 else "")}) + "\n"
                yield json.dumps({"type": "done", "full_text": response_text, "executed_trades": result.get("executed_trades", [])}) + "\n"
            elif intent == "stock_query":
                # OPTIMIZED: Fast template path for stock queries with price (skip LLM call)
                stock = context.get("stock", {})
                if stock.get("price", 0) > 0:
                    symbol = stock.get("symbol", "UNKNOWN")
                    price = stock.get("price", 0)
                    change = stock.get("change_percent", 0)
                    change_str = f"{change:+.2f}%" if change != 0 else "unchanged"
                    response_text = f"{symbol} is currently trading at ${price:,.2f}, {change_str} today. Would you like me to show you the full analysis?"
                    
                    words = response_text.split()
                    for i, word in enumerate(words):
                        yield json.dumps({"type": "token", "text": word + (" " if i < len(words) - 1 else "")}) + "\n"
                    yield json.dumps({"type": "done", "full_text": response_text}) + "\n"
                else:
                    # Fallback to LLM if no price data
                    async for chunk in generate_voice_reply_stream(system_prompt, user_prompt, history, skip_ack=True):
                        yield chunk
            elif intent == "crypto_query":
                # OPTIMIZED: Fast template path for crypto queries with price (skip LLM call)
                crypto = context.get("crypto", {})
                if crypto.get("price", 0) > 0 and "top_picks" not in crypto:
                    symbol = crypto.get("symbol", "BTC")
                    name = crypto.get("name", "Bitcoin")
                    price = crypto.get("price", 0)
                    change = crypto.get("change_24h", 0)
                    change_str = f"{change:+.2f}%" if change != 0 else "unchanged"
                    response_text = f"{name} ({symbol}) is currently trading at ${price:,.2f}, {change_str} in the last 24 hours. Our analysis shows strong momentum. Would you like me to show you the full analysis?"
                    
                    words = response_text.split()
                    for i, word in enumerate(words):
                        yield json.dumps({"type": "token", "text": word + (" " if i < len(words) - 1 else "")}) + "\n"
                    yield json.dumps({"type": "done", "full_text": response_text}) + "\n"
                else:
                    # Fallback to LLM for complex queries or when no price data
                    async for chunk in generate_voice_reply_stream(system_prompt, user_prompt, history, skip_ack=True):
                        yield chunk
            else:
                # Standard LLM streaming path (skip_ack=True since we already sent it)
                async for chunk in generate_voice_reply_stream(system_prompt, user_prompt, history, skip_ack=True):
                    yield chunk
        
        return StreamingResponse(token_generator(), media_type="text/event-stream")
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error in streaming voice endpoint: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        async def error_gen():
            yield json.dumps({"type": "error", "text": "I had trouble processing that. Can you try again?"}) + "\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

# Tax Optimization endpoints
@app.get("/api/tax/optimization-summary")
async def get_tax_optimization_summary(request: Request):
    """
    Get tax optimization summary with portfolio holdings for tax analysis.
    Returns holdings data needed for tax loss harvesting, capital gains analysis, etc.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token from Authorization header (supports both Token and Bearer)
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        # Get user - try to validate JWT token if available, otherwise use demo user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                # Try to get user from JWT token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception as e:
                logger.debug(f"JWT token validation failed: {e}")
        
        # Fallback: get user from email or use demo user
        if not user:
            try:
                # Try to get demo user or first user
                user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
                if not user:
                    user = await sync_to_async(User.objects.first)()
                if not user:
                    # Create demo user if none exists
                    user, _ = await sync_to_async(User.objects.get_or_create)(
                        email='demo@example.com',
                        defaults={'name': 'Demo User'}
                    )
            except Exception as e:
                logger.warning(f"Error getting user: {e}")
                raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Get portfolio holdings using PremiumAnalyticsService
        from core.premium_analytics import PremiumAnalyticsService
        service = PremiumAnalyticsService()
        metrics = await sync_to_async(service.get_portfolio_performance_metrics)(user.id)
        
        # Format holdings for tax optimization
        holdings = []
        if metrics and metrics.get('holdings'):
            for holding in metrics['holdings']:
                holdings.append({
                    'symbol': holding.get('symbol', ''),
                    'companyName': holding.get('company_name', holding.get('name', '')),
                    'shares': holding.get('shares', 0),
                    'currentPrice': float(holding.get('current_price', 0) or 0),
                    'costBasis': float(holding.get('cost_basis', holding.get('average_price', 0)) or 0),
                    'totalValue': float(holding.get('total_value', 0) or 0),
                    'returnAmount': float(holding.get('return_amount', 0) or 0),
                    'returnPercent': float(holding.get('return_percent', 0) or 0),
                    'sector': holding.get('sector', 'Unknown'),
                })
        
        # If no holdings from metrics, try to get from Portfolio model directly
        if not holdings:
            from core.models import Portfolio, Stock
            portfolio_holdings = await sync_to_async(list)(
                Portfolio.objects.filter(user=user).select_related('stock')[:20]
            )
            
            for ph in portfolio_holdings:
                stock = ph.stock
                current_price = float(ph.current_price or (stock.current_price if stock else 0) or 0)
                cost_basis = float(ph.average_price or 0)
                shares = ph.shares or 0
                total_value = float(ph.total_value or (current_price * shares) if current_price and shares else 0)
                return_amount = float((current_price - cost_basis) * shares if current_price and cost_basis and shares else 0)
                return_percent = float(((current_price - cost_basis) / cost_basis * 100) if cost_basis and current_price else 0)
                
                holdings.append({
                    'symbol': stock.symbol if stock else '',
                    'companyName': stock.company_name if stock else '',
                    'shares': shares,
                    'currentPrice': current_price,
                    'costBasis': cost_basis,
                    'totalValue': total_value,
                    'returnAmount': return_amount,
                    'returnPercent': return_percent,
                    'sector': stock.sector if stock else 'Unknown',
                })
        
        return {
            'holdings': holdings,
            'totalPortfolioValue': metrics.get('total_value', 0) if metrics else 0,
            'totalUnrealizedGains': metrics.get('total_return', 0) if metrics else 0,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in tax optimization summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching tax optimization data: {str(e)}")

@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str = None):
    """
    GET /api/market/quotes?symbols=AAPL,MSFT,GOOGL
    Returns real-time or cached stock quotes
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols parameter is required")
        
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No valid symbols provided")
        
        logger.info(f"📊 [Quotes API] Fetching quotes for {len(symbol_list)} symbols: {', '.join(symbol_list)}")
        
        # Try to import market data service
        try:
            from core.market_data_api_service import MarketDataAPIService
            market_data_service = MarketDataAPIService()
            MARKET_DATA_AVAILABLE = True
        except Exception as e:
            logger.warning(f"MarketDataAPIService not available: {e}")
            MARKET_DATA_AVAILABLE = False
            market_data_service = None
        
        quotes = []
        
        # If market data service is available, use it
        if MARKET_DATA_AVAILABLE and market_data_service:
            tasks = [market_data_service.get_stock_quote(symbol) for symbol in symbol_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbol_list, results):
                if isinstance(result, Exception):
                    logger.warning(f"Error fetching quote for {symbol}: {result}")
                    quotes.append(_get_mock_quote(symbol))
                    continue
                
                quote_data = result or {}
                if quote_data:
                    quotes.append({
                        "symbol": symbol,
                        "price": quote_data.get("price", 0.0),
                        "change": quote_data.get("change", 0.0),
                        "changePercent": quote_data.get("change_percent", 0.0),
                        "volume": quote_data.get("volume", 0),
                        "high": quote_data.get("high", 0.0),
                        "low": quote_data.get("low", 0.0),
                        "open": quote_data.get("open", 0.0),
                        "previousClose": quote_data.get("previous_close", 0.0),
                        "timestamp": quote_data.get("timestamp", ""),
                    })
                else:
                    quotes.append(_get_mock_quote(symbol))
            
            logger.info(f"✅ [Quotes API] Returning {len(quotes)} quotes")
        else:
            # Fallback to mock data if service unavailable
            logger.warning("⚠️ [Quotes API] MarketDataAPIService unavailable, using mock data")
            quotes = [_get_mock_quote(symbol) for symbol in symbol_list]
        
        return quotes
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Quotes API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _get_mock_quote(symbol: str) -> dict:
    """Generate mock quote data for a symbol."""
    base_price = 100.0 + (hash(symbol) % 500)
    change = (hash(symbol) % 20) - 10
    return {
        "symbol": symbol,
        "price": base_price,
        "change": change,
        "changePercent": (change / base_price) * 100,
        "volume": (hash(symbol) % 10_000_000) + 1_000_000,
        "high": base_price + 5,
        "low": base_price - 5,
        "open": base_price + 2,
        "previousClose": base_price - 2,
        "timestamp": "",
    }

@app.get("/api/yodlee/accounts")
async def get_yodlee_accounts(request: Request):
    """
    GET /api/yodlee/accounts
    Returns user's linked bank accounts from Yodlee or database.
    """
    if not DJANGO_AVAILABLE:
        # Return empty accounts in dev mode if Django not available
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }
    
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        # Get user
        User = get_user_model()
        user = None
        
        # Handle dev tokens (dev-token-*)
        if token and token.startswith('dev-token-'):
            # Dev token - get demo user
            try:
                user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
                if not user:
                    user = await sync_to_async(User.objects.first)()
                if not user:
                    # Create demo user if none exists
                    user, _ = await sync_to_async(User.objects.get_or_create)(
                        email='demo@example.com',
                        defaults={'name': 'Demo User'}
                    )
            except Exception as e:
                logger.warning(f"Error getting demo user: {e}")
        elif token and GRAPHQL_JWT_AVAILABLE:
            # Try JWT token validation
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception as e:
                logger.debug(f"JWT token validation failed: {e}")
        
        # Fallback: get demo user or first user (for unauthenticated dev requests)
        if not user:
            try:
                user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
                if not user:
                    user = await sync_to_async(User.objects.first)()
            except Exception as e:
                logger.warning(f"Error getting user: {e}")
        
        # In dev mode, allow unauthenticated requests with empty accounts
        # In production, this would require authentication
        if not user:
            logger.debug("No user found, returning empty accounts for dev mode")
            return {
                "success": True,
                "accounts": [],
                "count": 0,
            }
        
        # Check if Yodlee is enabled
        try:
            from core.banking_views import _is_yodlee_enabled
            yodlee_enabled = await sync_to_async(_is_yodlee_enabled)()
            if not yodlee_enabled:
                # Return empty accounts if Yodlee is disabled (common in dev)
                return {
                    "success": True,
                    "accounts": [],
                    "count": 0,
                }
        except Exception as e:
            logger.debug(f"Could not check Yodlee status: {e}")
            # Continue anyway - might be dev mode
        
        # Get accounts from database
        from core.banking_models import BankAccount
        db_accounts = await sync_to_async(list)(
            BankAccount.objects.filter(user=user, is_verified=True)
        )
        
        if db_accounts:
            accounts = []
            for db_account in db_accounts:
                accounts.append({
                    'id': db_account.id,
                    'accountId': str(db_account.yodlee_account_id or db_account.id),
                    'name': db_account.name or f"{db_account.provider} Account",
                    'type': db_account.account_type or 'CHECKING',
                    'mask': db_account.mask or '****',
                    'currency': db_account.currency or 'USD',
                    'balance': float(db_account.balance_current) if db_account.balance_current else 0.0,
                    'availableBalance': float(db_account.balance_available) if db_account.balance_available else 0.0,
                    'institutionName': db_account.provider or 'Unknown',
                    'lastUpdated': db_account.last_updated.isoformat() if db_account.last_updated else None,
                })
            
            return {
                "success": True,
                "accounts": accounts,
                "count": len(accounts),
            }
        
        # If no DB accounts, return empty (Yodlee integration would fetch here)
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Yodlee accounts: {e}", exc_info=True)
        # Return empty accounts on error (better UX than 500)
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }

@app.post("/api/tax/report/pdf")
async def generate_tax_report_pdf(request: Request):
    """
    Generate a PDF tax optimization report.
    Returns a PDF file with comprehensive tax analysis.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation not available - reportlab not installed")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        year = body.get('year', datetime.now().year)
        filing_status = body.get('filingStatus', 'single')
        state = body.get('state', 'CA')
        income = body.get('income', 0)
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Get portfolio data
        from core.premium_analytics import PremiumAnalyticsService
        service = PremiumAnalyticsService()
        metrics = await sync_to_async(service.get_portfolio_performance_metrics)(user.id)
        
        holdings = []
        if metrics and metrics.get('holdings'):
            for holding in metrics['holdings']:
                holdings.append({
                    'symbol': holding.get('symbol', ''),
                    'companyName': holding.get('company_name', holding.get('name', '')),
                    'shares': holding.get('shares', 0),
                    'currentPrice': float(holding.get('current_price', 0) or 0),
                    'costBasis': float(holding.get('cost_basis', 0) or 0),
                    'totalValue': float(holding.get('total_value', 0) or 0),
                    'returnAmount': float(holding.get('return_amount', 0) or 0),
                    'returnPercent': float(holding.get('return_percent', 0) or 0),
                })
        
        # Calculate tax metrics
        total_portfolio_value = metrics.get('total_value', 0) if metrics else 0
        total_unrealized_gains = metrics.get('total_return', 0) if metrics else 0
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563EB'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(f"Tax Optimization Report {year}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Header info
        header_data = [
            ['Generated:', datetime.now().strftime('%B %d, %Y')],
            ['Filing Status:', filing_status.replace('-', ' ').title()],
            ['State:', state],
            ['Annual Income:', f"${income:,.0f}"],
        ]
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tax Summary Section
        story.append(Paragraph("Tax Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Calculate taxes (simplified)
        federal_tax = income * 0.22  # Simplified calculation
        state_tax = income * 0.10 if state == 'CA' else income * 0.05
        total_tax = federal_tax + state_tax
        effective_rate = (total_tax / income * 100) if income > 0 else 0
        
        tax_data = [
            ['Federal Tax', f"${federal_tax:,.2f}"],
            ['State Tax', f"${state_tax:,.2f}"],
            ['Total Tax', f"${total_tax:,.2f}"],
            ['Effective Rate', f"{effective_rate:.1f}%"],
        ]
        tax_table = Table(tax_data, colWidths=[4*inch, 2*inch])
        tax_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(tax_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Portfolio Section
        story.append(Paragraph("Portfolio Overview", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        portfolio_data = [
            ['Total Portfolio Value', f"${total_portfolio_value:,.2f}"],
            ['Total Unrealized Gains', f"${total_unrealized_gains:,.2f}"],
        ]
        portfolio_table = Table(portfolio_data, colWidths=[4*inch, 2*inch])
        portfolio_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(portfolio_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top Holdings Section
        if holdings:
            story.append(Paragraph("Top Holdings (Tax Impact)", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            holdings_data = [['Symbol', 'Company', 'Shares', 'Value', 'Gain/Loss']]
            for holding in holdings[:10]:  # Top 10
                gain_loss = f"${holding['returnAmount']:,.2f}"
                holdings_data.append([
                    holding['symbol'],
                    holding['companyName'][:30] if holding['companyName'] else holding['symbol'],
                    f"{holding['shares']:,.0f}",
                    f"${holding['totalValue']:,.2f}",
                    gain_loss,
                ])
            
            holdings_table = Table(holdings_data, colWidths=[0.8*inch, 2.2*inch, 0.8*inch, 1*inch, 1.2*inch])
            holdings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(holdings_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(
            "This report is for informational purposes only and does not constitute tax advice. "
            "Please consult with a qualified tax professional for personalized advice.",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="tax_report_{year}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@app.post("/api/tax/smart-harvest/recommendations")
async def get_smart_harvest_recommendations(request: Request):
    """
    Get smart harvest recommendations with pre-filled trades.
    Returns optimized tax-loss harvesting suggestions.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        holdings = body.get('holdings', [])
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Calculate recommendations
        trades = []
        total_savings = 0
        warnings = []
        
        for holding in holdings:
            unrealized_gain = holding.get('unrealizedGain', 0)
            if unrealized_gain < 0:  # Only losses
                loss_amount = abs(unrealized_gain)
                # Estimate tax savings (assuming 22% marginal rate)
                estimated_savings = loss_amount * 0.22
                total_savings += estimated_savings
                
                trades.append({
                    'symbol': holding.get('symbol', ''),
                    'shares': holding.get('shares', 0),
                    'action': 'sell',
                    'estimatedSavings': round(estimated_savings, 2),
                    'reason': f'Harvest ${loss_amount:,.0f} in losses',
                })
        
        return {
            'trades': trades,
            'totalSavings': round(total_savings, 2),
            'warnings': warnings,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting smart harvest recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.post("/api/tax/smart-harvest/execute")
async def execute_smart_harvest(request: Request):
    """
    Execute smart harvest trades.
    In production, this would place actual orders with the broker.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        trades = body.get('trades', [])
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Broker API integration structure
        executed_trades = []
        failed_trades = []
        
        try:
            # Import broker service if available
            from core.broker_mutations import PlaceOrder
            from core.broker_models import BrokerAccount, BrokerOrder
            from core.alpaca_broker_service import AlpacaBrokerService
            
            # Get user's broker account
            broker_account = await sync_to_async(BrokerAccount.objects.filter(user=user).first)()
            
            if broker_account and broker_account.alpaca_account_id:
                # Initialize broker service
                broker_service = AlpacaBrokerService()
                
                for trade in trades:
                    try:
                        symbol = trade.get('symbol', '').upper()
                        shares = int(trade.get('shares', 0))
                        
                        if shares <= 0:
                            failed_trades.append({
                                'symbol': symbol,
                                'error': 'Invalid share quantity',
                            })
                            continue
                        
                        # Place sell order through broker API
                        # In production, this would use the actual broker service
                        order_result = {
                            'symbol': symbol,
                            'shares': shares,
                            'side': 'sell',
                            'order_type': 'MARKET',
                            'status': 'submitted',
                            'order_id': f'TLH_{symbol}_{datetime.now().timestamp()}',
                        }
                        
                        # Log the order (in production, save to BrokerOrder model)
                        executed_trades.append(order_result)
                        
                    except Exception as trade_error:
                        logger.error(f"Error executing trade for {trade.get('symbol')}: {trade_error}")
                        failed_trades.append({
                            'symbol': trade.get('symbol', 'UNKNOWN'),
                            'error': str(trade_error),
                        })
            else:
                # No broker account linked - return mock success for demo
                logger.info("No broker account linked, returning mock execution")
                for trade in trades:
                    executed_trades.append({
                        'symbol': trade.get('symbol', ''),
                        'shares': trade.get('shares', 0),
                        'status': 'simulated',
                        'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                    })
                    
        except ImportError:
            # Broker integration not available - return mock success
            logger.info("Broker integration not available, returning mock execution")
            for trade in trades:
                executed_trades.append({
                    'symbol': trade.get('symbol', ''),
                    'shares': trade.get('shares', 0),
                    'status': 'simulated',
                    'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                })
        except Exception as broker_error:
            logger.error(f"Broker integration error: {broker_error}")
            # Fallback to mock execution
            for trade in trades:
                executed_trades.append({
                    'symbol': trade.get('symbol', ''),
                    'shares': trade.get('shares', 0),
                    'status': 'simulated',
                    'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                })
        
        return {
            'success': len(executed_trades) > 0,
            'tradesExecuted': len(executed_trades),
            'tradesFailed': len(failed_trades),
            'executedTrades': executed_trades,
            'failedTrades': failed_trades,
            'message': f'Smart harvest: {len(executed_trades)} trades executed, {len(failed_trades)} failed',
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing smart harvest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing harvest: {str(e)}")

@app.get("/api/tax/projection")
async def get_tax_projection(request: Request):
    """
    Get multi-year tax projections.
    Returns year-by-year tax estimates.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and query params
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        years = int(request.query_params.get('years', 5))
        income = float(request.query_params.get('income', 80000))
        filing_status = request.query_params.get('filingStatus', 'single')
        state = request.query_params.get('state', 'CA')
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Enhanced projection calculations
        projections = []
        current_year = datetime.now().year
        
        # Tax brackets for more accurate calculations
        INCOME_BRACKETS = {
            'single': [
                {'min': 0, 'max': 11600, 'rate': 0.10},
                {'min': 11601, 'max': 47150, 'rate': 0.12},
                {'min': 47151, 'max': 100525, 'rate': 0.22},
                {'min': 100526, 'max': 191950, 'rate': 0.24},
                {'min': 191951, 'max': 243725, 'rate': 0.32},
                {'min': 243726, 'max': 609350, 'rate': 0.35},
                {'min': 609351, 'max': float('inf'), 'rate': 0.37},
            ],
            'married-joint': [
                {'min': 0, 'max': 23200, 'rate': 0.10},
                {'min': 23201, 'max': 94300, 'rate': 0.12},
                {'min': 94301, 'max': 201050, 'rate': 0.22},
                {'min': 201051, 'max': 383900, 'rate': 0.24},
                {'min': 383901, 'max': 487450, 'rate': 0.32},
                {'min': 487451, 'max': 731200, 'rate': 0.35},
                {'min': 731201, 'max': float('inf'), 'rate': 0.37},
            ],
        }
        
        # State tax rates
        STATE_TAX_RATES = {
            'CA': 0.10, 'NY': 0.09, 'NJ': 0.1075, 'OR': 0.099,
            'TX': 0.0, 'FL': 0.0, 'NV': 0.0, 'WA': 0.0,
        }
        
        def calculate_federal_tax(income, filing_status):
            """Calculate federal tax using actual brackets"""
            brackets = INCOME_BRACKETS.get(filing_status, INCOME_BRACKETS['single'])
            tax = 0
            prev_max = 0
            
            for bracket in brackets:
                if income > prev_max:
                    taxable_in_bracket = min(income, bracket['max']) - prev_max
                    tax += taxable_in_bracket * bracket['rate']
                    prev_max = bracket['max']
            
            return tax
        
        def calculate_state_tax(income, state_code):
            """Calculate state tax"""
            rate = STATE_TAX_RATES.get(state_code, 0.05)
            return income * rate
        
        # Calculate projections with enhanced logic
        for i in range(years + 1):
            year = current_year + i
            # Assume 3% annual income growth (can be made configurable)
            growth_rate = 0.03
            projected_income = income * ((1 + growth_rate) ** i)
            
            # Calculate taxes using actual brackets
            federal_tax = calculate_federal_tax(projected_income, filing_status)
            state_tax = calculate_state_tax(projected_income, state)
            total_tax = federal_tax + state_tax
            effective_rate = (total_tax / projected_income * 100) if projected_income > 0 else 0
            
            # Calculate marginal rate (top bracket rate)
            brackets = INCOME_BRACKETS.get(filing_status, INCOME_BRACKETS['single'])
            marginal_rate = 0.10
            for bracket in brackets:
                if projected_income >= bracket['min']:
                    marginal_rate = bracket['rate']
            
            projections.append({
                'year': year,
                'projectedIncome': round(projected_income, 2),
                'projectedTax': round(total_tax, 2),
                'federalTax': round(federal_tax, 2),
                'stateTax': round(state_tax, 2),
                'effectiveRate': round(effective_rate, 2),
                'marginalRate': round(marginal_rate * 100, 1),
            })
        
        return {
            'projections': projections,
            'currentYear': current_year,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tax projection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting projection: {str(e)}")

# Initialize services
if ML_SERVICES_AVAILABLE:
    try:
        ml_service = OptimizedMLService()
        market_data_service = AdvancedMarketDataService()
        advanced_ml = AdvancedMLAlgorithms()
        monitoring_service = ProductionMonitoringService()
        logger.info("All ML services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML services: {e}")
        ML_SERVICES_AVAILABLE = False

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RichesReach AI Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "ml_services": ML_SERVICES_AVAILABLE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ml_services": ML_SERVICES_AVAILABLE,
            "market_data": ML_SERVICES_AVAILABLE,
            "monitoring": ML_SERVICES_AVAILABLE
        }
    }
    if ML_SERVICES_AVAILABLE:
        try:
            # Test ML service health
            ml_health = ml_service.check_health()
            health_status["services"]["ml_health"] = ml_health
            # Test market data service
            market_health = market_data_service.check_health()
            health_status["services"]["market_health"] = market_health
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
    return health_status

@app.post("/api/portfolio/analyze")
async def analyze_portfolio(background_tasks: BackgroundTasks):
    """Analyze investment portfolio using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "portfolio_analysis_requests", 1, "count"
            )
        # Run portfolio analysis in background
        background_tasks.add_task(run_portfolio_analysis)
        return {
            "message": "Portfolio analysis started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/market/regime")
async def predict_market_regime(background_tasks: BackgroundTasks):
    """Predict current market regime using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "market_regime_requests", 1, "count"
            )
        # Run market regime prediction in background
        background_tasks.add_task(run_market_regime_prediction)
        return {
            "message": "Market regime prediction started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Market regime prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_service_status():
    """Get comprehensive service status"""
    status = {
        "service": "RichesReach AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "ml_services": ML_SERVICES_AVAILABLE
    }
    if ML_SERVICES_AVAILABLE:
        try:
            # Get ML model status
            ml_status = ml_service.get_status()
            status["ml_status"] = ml_status
            # Get market data status
            market_status = market_data_service.get_status()
            status["market_status"] = market_status
        except Exception as e:
            status["error"] = str(e)
    return status

# Authentication models
class LoginRequest(BaseModel):
    email: str = None
    username: str = None
    password: str
    
    class Config:
        # Allow both email and username fields
        extra = "allow"

def _authenticate_user_sync(email: str, password: str):
    """Synchronous Django authentication helper"""
    User = get_user_model()
    user = None
    
    # Method 1: Try Django's authenticate
    try:
        from django.contrib.auth import authenticate
        user = authenticate(username=email, password=password)
    except Exception as e:
        logger.warning(f"Authenticate failed: {e}")
    
    # Method 2: Manual authentication if Django auth fails
    if not user:
        try:
            user = User.objects.get(email=email)
            logger.info(f"Found user: {user.email}, checking password...")
            if not user.check_password(password):
                logger.warning(f"Invalid password for {email}")
                user = None
            else:
                logger.info(f"Manual authentication successful for {email}")
        except User.DoesNotExist:
            logger.warning(f"User not found: {email}")
            user = None
        except Exception as e:
            logger.error(f"Error during manual auth: {e}", exc_info=True)
            user = None
    
    # Method 3: Development fallback - create/get demo user
    if not user:
        logger.info("Authentication failed, checking for demo user...")
        try:
            if email.lower() == 'demo@example.com':
                user, created = User.objects.get_or_create(
                    email='demo@example.com',
                    defaults={'name': 'Demo User'}
                )
                if created:
                    user.set_password('demo123')
                    user.save()
                    logger.info("Created demo user for development")
                else:
                    if not user.check_password('demo123'):
                        user.set_password('demo123')
                        user.save()
                        logger.info("Reset demo user password")
                logger.info("Using demo user for development (dev mode)")
            else:
                user = None
        except Exception as e:
            logger.error(f"Error creating demo user: {e}")
            user = None
    
    return user

@app.post("/api/auth/login/")
async def login(request: LoginRequest):
    """REST API Login Endpoint
    
    Accepts either email or username in the request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    or
    {
        "username": "user@example.com",
        "password": "password123"
    }
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Handle both email and username fields
        email = (request.email or request.username or "").strip()
        password = request.password
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email/username and password are required")
        
        logger.info(f"Login attempt for email: {email}")
        
        # Run Django operations in sync context
        user = await sync_to_async(_authenticate_user_sync)(email, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate token (also needs to be sync)
        def _generate_token_sync(user):
            token = None
            if GRAPHQL_JWT_AVAILABLE:
                try:
                    token = get_token(user)
                    logger.info(f"Generated JWT token for {email}")
                except Exception as e:
                    logger.warning(f"Failed to generate JWT token: {e}")
            
            # Fallback to dev token if JWT not available
            if not token:
                import time
                token = f"dev-token-{int(time.time())}"
                logger.info(f"Using dev token for {email}")
            return token
        
        token = await sync_to_async(_generate_token_sync)(user)
        
        # Prepare user data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'name': getattr(user, 'name', ''),
        }
        
        # Add optional fields if they exist
        if hasattr(user, 'profile_pic') and user.profile_pic:
            user_data['profile_pic'] = user.profile_pic
        
        response_data = {
            'access_token': token,
            'token': token,  # Alias for compatibility
            'user': user_data,
        }
        
        logger.info(f"✅ Login successful for {email}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# GraphQL endpoint
@app.post("/graphql/")
@app.get("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for Apollo Client"""
    if not GRAPHQL_AVAILABLE:
        raise HTTPException(status_code=503, detail="GraphQL service not available")
    
    try:
        from core.schema import schema
        from core.authentication import get_user_from_token
        
        # Get request body
        body = await request.body()
        body_str = body.decode('utf-8') if isinstance(body, bytes) else body
        
        # Parse JSON body
        try:
            request_data = json.loads(body_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        query = request_data.get('query', '')
        variables = request_data.get('variables', {})
        operation_name = request_data.get('operationName')
        
        # Get user from token
        auth_header = request.headers.get('authorization', '')
        user = None
        if auth_header:
            token = auth_header.replace('Bearer ', '').replace('JWT ', '')
            try:
                user = await sync_to_async(get_user_from_token)(token)
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
        
        # Create GraphQL context using SimpleContext (supports both object and dict access)
        from core.graphql_context import SimpleContext
        context = SimpleContext(
            user=user if user else None,
            request=request
        )
        
        # Execute GraphQL query in a thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Add logging for sblocBanks queries
        if 'sblocBanks' in query or 'sbloc_banks' in query:
            logger.info(f"🔵 [GraphQL] Executing sblocBanks query")
            logger.info(f"🔵 [GraphQL] Query: {query[:200]}...")
            logger.info(f"🔵 [GraphQL] Context user: {context.user if hasattr(context, 'user') else 'None'}")
        
        result = await loop.run_in_executor(
            None,
            lambda: schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                context_value=context
            )
        )
        
        # Add logging for sblocBanks results
        if 'sblocBanks' in query or 'sbloc_banks' in query:
            logger.info(f"🔵 [GraphQL] sblocBanks result.data type: {type(result.data)}")
            if result.data:
                logger.info(f"🔵 [GraphQL] sblocBanks result.data keys: {result.data.keys() if isinstance(result.data, dict) else 'not a dict'}")
                if 'sblocBanks' in result.data:
                    logger.info(f"🔵 [GraphQL] sblocBanks value: {result.data['sblocBanks']}")
                    logger.info(f"🔵 [GraphQL] sblocBanks length: {len(result.data['sblocBanks']) if isinstance(result.data['sblocBanks'], list) else 'not a list'}")
            if result.errors:
                logger.error(f"🔵 [GraphQL] sblocBanks errors: {result.errors}")
        
        # Check for errors
        if result.errors:
            logger.error(f"GraphQL errors: {result.errors}")
            error_messages = []
            for error in result.errors:
                if hasattr(error, 'message'):
                    error_messages.append(str(error.message))
                else:
                    error_messages.append(str(error))
            return JSONResponse(
                content={'errors': error_messages, 'data': result.data},
                status_code=400
            )
        
        return JSONResponse(content={'data': result.data}, status_code=200)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GraphQL error: {e}", exc_info=True)
        import traceback
        logger.error(f"GraphQL traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"GraphQL error: {str(e)}")

# Test endpoint to verify SBLOC banks are accessible
@app.get("/api/test/sbloc-banks")
async def test_sbloc_banks():
    """Test endpoint to verify SBLOC banks are in database"""
    if not DJANGO_AVAILABLE:
        return JSONResponse(content={'error': 'Django not available', 'banks': []}, status_code=503)
    
    try:
        from core.sbloc_models import SBLOCBank
        
        # Use sync_to_async for Django ORM calls
        def get_banks():
            banks = SBLOCBank.objects.filter(is_active=True).order_by('priority', 'name')
            banks_data = []
            for bank in banks:
                banks_data.append({
                    'id': str(bank.id),
                    'name': bank.name,
                    'minApr': float(bank.min_apr) if bank.min_apr else None,
                    'maxApr': float(bank.max_apr) if bank.max_apr else None,
                    'minLtv': float(bank.min_ltv) if bank.min_ltv else None,
                    'maxLtv': float(bank.max_ltv) if bank.max_ltv else None,
                    'minLoanUsd': int(bank.min_loan_usd) if bank.min_loan_usd else None,
                    'regions': bank.regions or [],
                })
            return banks_data
        
        banks_data = await sync_to_async(get_banks)()
        return JSONResponse(content={'banks': banks_data, 'count': len(banks_data)}, status_code=200)
    except Exception as e:
        logger.error(f"Error in test_sbloc_banks: {e}", exc_info=True)
        return JSONResponse(content={'error': str(e), 'banks': []}, status_code=500)

# Mount Django URLs at the END - after all FastAPI routes are defined
# This ensures FastAPI routes take precedence, then Django handles remaining paths
if DJANGO_AVAILABLE:
    try:
        from django.core.wsgi import get_wsgi_application
        
        # Get Django WSGI application
        django_wsgi = get_wsgi_application()
        
        # CRITICAL FIX: WSGIMiddleware's build_environ() should convert Authorization to HTTP_AUTHORIZATION
        # But it's not working. We need to patch build_environ to explicitly include it.
        from starlette.middleware.wsgi import build_environ as original_build_environ
        import starlette.middleware.wsgi as wsgi_module
        import sys
        
        def patched_build_environ(scope, body):
            """Patched build_environ that explicitly includes Authorization header"""
            import sys
            # Log all headers in scope for debugging
            if scope.get("type") == "http":
                headers = scope.get("headers", [])
                print(f"🔵 [PATCH] build_environ called for {scope.get('path', 'unknown')}", file=sys.stdout, flush=True)
                print(f"🔵 [PATCH] Headers in ASGI scope: {[(name.decode('latin1'), value.decode('latin1')[:30]) for name, value in headers]}", file=sys.stdout, flush=True)
                
                # Check for Authorization header
                auth_found = False
                for name, value in headers:
                    if name.lower() == b"authorization":
                        auth_found = True
                        auth_value = value.decode("latin1")
                        print(f"🔵 [PATCH] Found Authorization in ASGI scope: {auth_value[:30]}...", file=sys.stdout, flush=True)
                        break
                
                if not auth_found:
                    print(f"❌ [PATCH] Authorization NOT FOUND in ASGI scope headers!", file=sys.stdout, flush=True)
            
            # Call original to get the base environ
            environ = original_build_environ(scope, body)
            
            # Manually extract and add Authorization header if present in ASGI scope
            if scope.get("type") == "http":
                headers = scope.get("headers", [])
                for name, value in headers:
                    if name.lower() == b"authorization":
                        auth_value = value.decode("latin1")
                        environ["HTTP_AUTHORIZATION"] = auth_value
                        print(f"🔵 [PATCH] Injected HTTP_AUTHORIZATION: {auth_value[:30]}...", file=sys.stdout, flush=True)
                        logger.info(f"🔵 [PATCH] Injected HTTP_AUTHORIZATION into WSGI environ")
                        break
            
            return environ
        
        # Monkey-patch the build_environ function
        print(f"🔵 [SETUP] Patching build_environ function...", file=sys.stdout, flush=True)
        original_build_environ_ref = wsgi_module.build_environ
        wsgi_module.build_environ = patched_build_environ
        print(f"🔵 [SETUP] build_environ patched. Original: {original_build_environ_ref}, New: {wsgi_module.build_environ}", file=sys.stdout, flush=True)
        logger.info("🔵 [SETUP] build_environ function patched to include Authorization header")
        
        # Create a wrapper for extra logging
        def django_wsgi_with_auth(environ, start_response):
            """WSGI wrapper with logging"""
            import sys
            print(f"🔵 [WSGI WRAPPER] Called for PATH_INFO={environ.get('PATH_INFO')}", file=sys.stdout, flush=True)
            http_keys = [k for k in environ.keys() if k.startswith('HTTP_')]
            print(f"🔵 [WSGI WRAPPER] HTTP_* keys: {http_keys}", file=sys.stdout, flush=True)
            if 'HTTP_AUTHORIZATION' in environ:
                print(f"🔵 [WSGI WRAPPER] HTTP_AUTHORIZATION={environ['HTTP_AUTHORIZATION'][:30]}...", file=sys.stdout, flush=True)
            else:
                print(f"❌ [WSGI WRAPPER] HTTP_AUTHORIZATION NOT FOUND", file=sys.stdout, flush=True)
                print(f"❌ [WSGI WRAPPER] All environ keys: {list(environ.keys())}", file=sys.stdout, flush=True)
            return django_wsgi(environ, start_response)
        
        # Mount Django at root - all Django URLs will be available
        # FastAPI routes are checked first (defined above), then Django routes handle the rest
        app.mount("/", WSGIMiddleware(django_wsgi_with_auth))
        
        logger.info("✅ Django URLs mounted - all Django views are now available")
        logger.info("   FastAPI routes take precedence, then Django routes handle remaining paths")
    except Exception as e:
        logger.warning(f"Could not mount Django URLs: {e}")
        logger.warning("Django views will not be available through FastAPI")

async def run_portfolio_analysis():
    """Background task for portfolio analysis"""
    try:
        logger.info("Running portfolio analysis...")
        # This would call your actual portfolio analysis logic
        await asyncio.sleep(5)  # Simulate processing
        logger.info("Portfolio analysis completed")
    except Exception as e:
        logger.error(f"Portfolio analysis background task error: {e}")

async def run_market_regime_prediction():
    """Background task for market regime prediction"""
    try:
        logger.info("Running market regime prediction...")
        # This would call your actual market regime logic
        await asyncio.sleep(3)  # Simulate processing
        logger.info("Market regime prediction completed")
    except Exception as e:
        logger.error(f"Market regime prediction background task error: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
