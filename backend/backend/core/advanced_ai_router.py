"""
Advanced AI Router - Phase 3 Enhanced AI Integration
GPT-5, Claude, and multi-model AI with advanced capabilities
"""

import os
import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import aiohttp
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

logger = logging.getLogger("richesreach")

class AIModel(Enum):
    """Enhanced AI models with latest versions"""
    # OpenAI Models
    GPT_5 = "gpt-5"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    
    # Anthropic Models
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    
    # Google Models
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_ULTRA = "gemini-ultra"
    
    # Specialized Models
    FINANCIAL_GPT = "financial-gpt"
    TRADING_AI = "trading-ai"
    RISK_ANALYZER = "risk-analyzer"

class RequestType(Enum):
    """Enhanced request types"""
    MARKET_ANALYSIS = "market_analysis"
    OPTIONS_STRATEGY = "options_strategy"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RISK_ASSESSMENT = "risk_assessment"
    NEWS_SENTIMENT = "news_sentiment"
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    FINANCIAL_MODELING = "financial_modeling"
    TRADING_SIGNALS = "trading_signals"
    COMPLIANCE_CHECK = "compliance_check"
    RESEARCH_ANALYSIS = "research_analysis"
    PREDICTIVE_ANALYSIS = "predictive_analysis"

class ModelCapabilities:
    """Enhanced model capabilities"""
    def __init__(self, max_tokens: int, cost_per_1k_tokens: float, 
                 supports_vision: bool, supports_functions: bool,
                 latency_ms: int, context_window: int, reliability_score: float,
                 specialized_for: List[str] = None, reasoning_capability: float = 0.0,
                 mathematical_accuracy: float = 0.0, financial_knowledge: float = 0.0):
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.supports_vision = supports_vision
        self.supports_functions = supports_functions
        self.latency_ms = latency_ms
        self.context_window = context_window
        self.reliability_score = reliability_score
        self.specialized_for = specialized_for or []
        self.reasoning_capability = reasoning_capability
        self.mathematical_accuracy = mathematical_accuracy
        self.financial_knowledge = financial_knowledge

@dataclass
class AIRequest:
    """Enhanced AI request structure"""
    request_id: str
    request_type: RequestType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: float = 1.0  # Default to 1.0 for GPT-5 compatibility
    model_preference: Optional[AIModel] = None
    budget_limit: Optional[float] = None
    timeout_seconds: int = 30
    # Dynamic timeout based on request type
    HEAVY_LIFT_TIMEOUT_SECONDS = 45  # For complex educational content
    priority: str = "normal"  # low, normal, high, critical
    requires_reasoning: bool = False
    requires_math: bool = False
    requires_financial_knowledge: bool = False
    multi_step: bool = False
    confidence_threshold: float = 0.8

@dataclass
class AIResponse:
    """Enhanced AI response structure"""
    request_id: str
    model_used: AIModel
    response: str
    tokens_used: int
    cost: float
    latency_ms: int
    timestamp: datetime
    confidence_score: float = 0.0
    reasoning_steps: Optional[List[str]] = None
    mathematical_verification: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __init__(self, request_id: str, model_used: AIModel, response: str, 
                 tokens_used: int, cost: float, latency_ms: int, timestamp: datetime,
                 confidence_score: float = 0.0, reasoning_steps: Optional[List[str]] = None,
                 mathematical_verification: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize AIResponse with all parameters"""
        self.request_id = request_id
        self.model_used = model_used
        self.response = response
        self.tokens_used = tokens_used
        self.cost = cost
        self.latency_ms = latency_ms
        self.timestamp = timestamp
        self.confidence_score = confidence_score
        self.reasoning_steps = reasoning_steps or []
        self.mathematical_verification = mathematical_verification
        self.metadata = metadata or {}
        
        # Handle legacy 'model' parameter
        if 'model' in kwargs:
            self.model_used = kwargs['model']

@dataclass
class ModelPerformance:
    """Enhanced model performance tracking"""
    model: AIModel
    total_requests: int
    successful_requests: int
    average_latency_ms: float
    average_cost: float
    reliability_score: float
    average_confidence: float
    specialized_performance: Dict[str, float]
    last_updated: datetime

class AdvancedAIRouter:
    """Advanced AI Router with GPT-5 and enhanced capabilities"""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.performance_tracking: Dict[AIModel, ModelPerformance] = {}
        self.request_cache: Dict[str, AIResponse] = {}
        self.cache_ttl = timedelta(minutes=30)
        self.model_ensemble = {}
        self.confidence_predictor = None
        
        # Initialize clients
        self._initialize_clients()
        
        # Load performance data
        self._load_performance_data()
        
        # Initialize ensemble models
        self._initialize_ensemble_models()
    
    def _initialize_models(self) -> Dict[AIModel, ModelCapabilities]:
        """Initialize enhanced model capabilities"""
        return {
            # GPT-5 (Latest)
            AIModel.GPT_5: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.01,
                supports_vision=True,
                supports_functions=True,
                latency_ms=600,
                context_window=200000,
                reliability_score=0.99,
                specialized_for=["reasoning", "mathematics", "financial_analysis"],
                reasoning_capability=0.95,
                mathematical_accuracy=0.98,
                financial_knowledge=0.92
            ),
            
            # GPT-4o
            AIModel.GPT_4O: ModelCapabilities(
                max_tokens=128000,
                cost_per_1k_tokens=0.005,
                supports_vision=True,
                supports_functions=True,
                latency_ms=1200,
                context_window=128000,
                reliability_score=0.98,
                specialized_for=["vision", "reasoning", "code"],
                reasoning_capability=0.90,
                mathematical_accuracy=0.95,
                financial_knowledge=0.88
            ),
            
            # GPT-4o-mini
            AIModel.GPT_4O_MINI: ModelCapabilities(
                max_tokens=128000,
                cost_per_1k_tokens=0.00015,
                supports_vision=False,
                supports_functions=True,
                latency_ms=800,
                context_window=128000,
                reliability_score=0.95,
                specialized_for=["general", "fast_responses"],
                reasoning_capability=0.75,
                mathematical_accuracy=0.85,
                financial_knowledge=0.80
            ),
            
            # Claude 3.5 Sonnet
            AIModel.CLAUDE_3_5_SONNET: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.003,
                supports_vision=True,
                supports_functions=False,
                latency_ms=1000,
                context_window=200000,
                reliability_score=0.97,
                specialized_for=["reasoning", "analysis", "writing"],
                reasoning_capability=0.92,
                mathematical_accuracy=0.90,
                financial_knowledge=0.85
            ),
            
            # Claude 3.5 Haiku
            AIModel.CLAUDE_3_5_HAIKU: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.00025,
                supports_vision=True,
                supports_functions=False,
                latency_ms=600,
                context_window=200000,
                reliability_score=0.94,
                specialized_for=["fast_responses", "general"],
                reasoning_capability=0.80,
                mathematical_accuracy=0.85,
                financial_knowledge=0.75
            ),
            
            # Claude 3 Opus
            AIModel.CLAUDE_3_OPUS: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.015,
                supports_vision=True,
                supports_functions=False,
                latency_ms=2000,
                context_window=200000,
                reliability_score=0.99,
                specialized_for=["complex_reasoning", "analysis", "research"],
                reasoning_capability=0.98,
                mathematical_accuracy=0.95,
                financial_knowledge=0.90
            ),
            
            # Gemini 2.5 Flash
            AIModel.GEMINI_PRO: ModelCapabilities(
                max_tokens=1000000,
                cost_per_1k_tokens=0.0005,
                supports_vision=True,
                supports_functions=True,
                latency_ms=600,
                context_window=1000000,
                reliability_score=0.95,
                specialized_for=["general", "fast_responses"],
                reasoning_capability=0.88,
                mathematical_accuracy=0.92,
                financial_knowledge=0.85
            ),
            
            # Gemini 2.5 Pro
            AIModel.GEMINI_ULTRA: ModelCapabilities(
                max_tokens=2000000,
                cost_per_1k_tokens=0.0015,
                supports_vision=True,
                supports_functions=True,
                latency_ms=1200,
                context_window=2000000,
                reliability_score=0.97,
                specialized_for=["reasoning", "analysis", "complex_tasks"],
                reasoning_capability=0.95,
                mathematical_accuracy=0.96,
                financial_knowledge=0.90
            )
        }
    
    def _initialize_clients(self):
        """Initialize AI model clients"""
        try:
            # OpenAI - only initialize if API key is present
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
                logger.info("✅ OpenAI client initialized")
            else:
                self.openai_client = None
                logger.warning("⚠️ OpenAI API key not found, OpenAI features disabled")
            
            # Anthropic - only initialize if API key is present
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
                logger.info("✅ Anthropic client initialized")
            else:
                self.anthropic_client = None
                logger.warning("⚠️ Anthropic API key not found, Anthropic features disabled")
            
            # Google Gemini - only initialize if API key is present
            google_key = os.getenv("GOOGLE_API_KEY")
            if google_key:
                genai.configure(api_key=google_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_vision_model = genai.GenerativeModel('gemini-2.5-flash')
                self.gemini_ultra_model = genai.GenerativeModel('gemini-2.5-pro')
                logger.info("✅ Google Gemini clients initialized")
            else:
                self.gemini_model = None
                self.gemini_vision_model = None
                self.gemini_ultra_model = None
                logger.warning("⚠️ Google API key not found, Gemini features disabled")
            
            logger.info("✅ Advanced AI Router clients initialized (some may be disabled)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI clients: {e}")
            # Don't raise - set clients to None instead
            self.openai_client = None
            self.anthropic_client = None
            self.gemini_model = None
            self.gemini_vision_model = None
            self.gemini_ultra_model = None
    
    def _initialize_ensemble_models(self):
        """Initialize ensemble models for confidence prediction"""
        try:
            # Load or train confidence prediction model
            self.confidence_predictor = self._load_confidence_predictor()
            logger.info("✅ Ensemble models initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize ensemble models: {e}")
    
    def _load_confidence_predictor(self):
        """Load or create confidence prediction model"""
        try:
            # Try to load existing model
            if os.path.exists("models/confidence_predictor.joblib"):
                return joblib.load("models/confidence_predictor.joblib")
            else:
                # Create a simple confidence predictor
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                # Train with dummy data (in production, use real historical data)
                X_dummy = np.random.rand(100, 5)  # 5 features
                y_dummy = np.random.rand(100)     # confidence scores
                model.fit(X_dummy, y_dummy)
                
                # Save model
                os.makedirs("models", exist_ok=True)
                joblib.dump(model, "models/confidence_predictor.joblib")
                return model
        except Exception as e:
            logger.warning(f"Failed to load confidence predictor: {e}")
            return None
    
    def _load_performance_data(self):
        """Load historical performance data"""
        for model in self.models.keys():
            self.performance_tracking[model] = ModelPerformance(
                model=model,
                total_requests=0,
                successful_requests=0,
                average_latency_ms=self.models[model].latency_ms,
                average_cost=self.models[model].cost_per_1k_tokens,
                reliability_score=self.models[model].reliability_score,
                average_confidence=0.8,
                specialized_performance={},
                last_updated=datetime.now()
            )
    
    def _get_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request"""
        content = f"{request.request_type.value}:{request.prompt}:{request.temperature}:{request.priority}"
        if request.context:
            content += f":{json.dumps(request.context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _select_optimal_model(self, request: AIRequest) -> AIModel:
        """Enhanced model selection with advanced criteria"""
        # If model preference specified, use it
        if request.model_preference:
            return request.model_preference
        
        # Filter models by capabilities
        suitable_models = []
        for model, capabilities in self.models.items():
            if self._is_model_suitable(model, request):
                suitable_models.append((model, capabilities))
        
        if not suitable_models:
            # Fallback to GPT-5
            return AIModel.GPT_5
        
        # Enhanced scoring based on request requirements
        scored_models = []
        for model, capabilities in suitable_models:
            performance = self.performance_tracking[model]
            
            # Base scores
            cost_score = 1.0 / (capabilities.cost_per_1k_tokens + 0.001)
            latency_score = 1.0 / (capabilities.latency_ms / 1000.0 + 0.1)
            reliability_score = performance.reliability_score
            
            # Specialized scores
            reasoning_score = capabilities.reasoning_capability if request.requires_reasoning else 0.5
            math_score = capabilities.mathematical_accuracy if request.requires_math else 0.5
            financial_score = capabilities.financial_knowledge if request.requires_financial_knowledge else 0.5
            
            # Priority multiplier
            priority_multiplier = {
                "low": 0.8,
                "normal": 1.0,
                "high": 1.2,
                "critical": 1.5
            }.get(request.priority, 1.0)
            
            # Calculate composite score
            if request.request_type in [RequestType.MARKET_ANALYSIS, RequestType.RISK_ASSESSMENT, RequestType.FINANCIAL_MODELING]:
                # Prioritize financial knowledge and reasoning
                composite_score = (
                    financial_score * 0.3 +
                    reasoning_score * 0.25 +
                    reliability_score * 0.2 +
                    cost_score * 0.15 +
                    latency_score * 0.1
                ) * priority_multiplier
            elif request.request_type in [RequestType.TRADING_SIGNALS, RequestType.PREDICTIVE_ANALYSIS]:
                # Prioritize reasoning and mathematical accuracy
                composite_score = (
                    reasoning_score * 0.3 +
                    math_score * 0.25 +
                    reliability_score * 0.2 +
                    latency_score * 0.15 +
                    cost_score * 0.1
                ) * priority_multiplier
            elif request.request_type == RequestType.GENERAL_CHAT:
                # Balance all factors
                composite_score = (
                    reliability_score * 0.3 +
                    cost_score * 0.3 +
                    latency_score * 0.2 +
                    reasoning_score * 0.1 +
                    math_score * 0.1
                ) * priority_multiplier
            else:
                # Default weighting
                composite_score = (
                    reliability_score * 0.3 +
                    reasoning_score * 0.2 +
                    cost_score * 0.2 +
                    latency_score * 0.2 +
                    financial_score * 0.1
                ) * priority_multiplier
            
            scored_models.append((model, composite_score))
        
        # Return highest scoring model
        return max(scored_models, key=lambda x: x[1])[0]
    
    def _is_model_suitable(self, model: AIModel, request: AIRequest) -> bool:
        """Enhanced model suitability check"""
        capabilities = self.models[model]
        
        # Check token limits
        estimated_tokens = len(request.prompt.split()) * 1.3
        if estimated_tokens > capabilities.max_tokens:
            return False
        
        # Check if vision is needed
        if request.context and request.context.get('has_images', False):
            if not capabilities.supports_vision:
                return False
        
        # Check budget constraints
        if request.budget_limit:
            estimated_cost = (estimated_tokens / 1000) * capabilities.cost_per_1k_tokens
            if estimated_cost > request.budget_limit:
                return False
        
        # Check specialized requirements
        if request.requires_reasoning and capabilities.reasoning_capability < 0.8:
            return False
        
        if request.requires_math and capabilities.mathematical_accuracy < 0.85:
            return False
        
        if request.requires_financial_knowledge and capabilities.financial_knowledge < 0.8:
            return False
        
        return True
    
    def _get_effective_timeout(self, request: AIRequest) -> int:
        """Calculate effective timeout based on request complexity"""
        base_timeout = request.timeout_seconds or 30
        
        # Heavy lift indicators
        if (request.requires_reasoning or 
            request.multi_step or 
            request.max_tokens and request.max_tokens > 2000 or
            "quiz" in request.prompt.lower() or
            "path" in request.prompt.lower() or
            "module" in request.prompt.lower()):
            return max(base_timeout, 45)  # Heavy lift timeout
        
        return base_timeout
    
    async def route_request(self, request: AIRequest) -> AIResponse:
        """Enhanced request routing with confidence scoring and dynamic timeouts"""
        start_time = time.time()
        
        # Dynamic timeout based on request complexity
        effective_timeout = self._get_effective_timeout(request)
        
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self.request_cache:
            cached_response = self.request_cache[cache_key]
            if datetime.now() - cached_response.timestamp < self.cache_ttl:
                logger.info(f"Cache hit for request {request.request_id}")
                return cached_response
        
        # Select optimal model
        selected_model = self._select_optimal_model(request)
        logger.info(f"Routing request {request.request_id} to {selected_model.value}")
        
        try:
            # Route to appropriate model with dynamic timeout
            if selected_model in [AIModel.GPT_5, AIModel.GPT_4O, AIModel.GPT_4O_MINI, AIModel.GPT_4_TURBO]:
                response = await asyncio.wait_for(
                    self._call_openai(request, selected_model), 
                    timeout=effective_timeout
                )
            elif selected_model in [AIModel.CLAUDE_3_5_SONNET, AIModel.CLAUDE_3_5_HAIKU, AIModel.CLAUDE_3_OPUS]:
                response = await asyncio.wait_for(
                    self._call_anthropic(request, selected_model), 
                    timeout=effective_timeout
                )
            elif selected_model in [AIModel.GEMINI_PRO, AIModel.GEMINI_PRO_VISION, AIModel.GEMINI_ULTRA]:
                response = await asyncio.wait_for(
                    self._call_gemini(request, selected_model), 
                    timeout=effective_timeout
                )
            else:
                raise ValueError(f"Unsupported model: {selected_model}")
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(request, response, selected_model)
            response.confidence_score = confidence_score
            
            # Add reasoning steps if requested
            if request.requires_reasoning:
                response.reasoning_steps = await self._extract_reasoning_steps(response.response)
            
            # Add mathematical verification if requested
            if request.requires_math:
                response.mathematical_verification = await self._verify_mathematics(response.response)
            
            # Update performance tracking
            self._update_performance_tracking(selected_model, response, start_time)
            
            # Cache response
            self.request_cache[cache_key] = response
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request {request.request_id} timed out after {effective_timeout}s")
            # Try fallback model with shorter timeout
            if selected_model != AIModel.GPT_4O_MINI:
                logger.info(f"Falling back to GPT-4o-mini for request {request.request_id}")
                fallback_request = AIRequest(
                    request_id=request.request_id,
                    request_type=request.request_type,
                    prompt=request.prompt,
                    context=request.context,
                    max_tokens=min(request.max_tokens or 1000, 1000),  # Reduce tokens for speed
                    temperature=request.temperature,
                    model_preference=AIModel.GPT_4O_MINI,
                    budget_limit=request.budget_limit,
                    timeout_seconds=20,  # Shorter timeout for fallback
                    priority=request.priority,
                    requires_reasoning=False,  # Disable reasoning for speed
                    requires_math=request.requires_math,
                    requires_financial_knowledge=request.requires_financial_knowledge,
                    multi_step=request.multi_step,
                    confidence_threshold=request.confidence_threshold
                )
                return await self.route_request(fallback_request)
            else:
                raise
                
        except Exception as e:
            logger.error(f"Error routing request {request.request_id}: {e}")
            
            # Handle specific temperature errors for GPT-5
            if "temperature" in str(e) and "unsupported" in str(e) and selected_model == AIModel.GPT_5:
                logger.info(f"Retrying {selected_model.value} with temperature 1.0")
                # Create a new request with temperature 1.0 and call the API directly
                retry_request = AIRequest(
                    request_id=request.request_id,
                    request_type=request.request_type,
                    prompt=request.prompt,
                    context=request.context,
                    max_tokens=request.max_tokens,
                    temperature=1.0,  # Force temperature 1.0 for GPT-5
                    model_preference=request.model_preference,
                    budget_limit=request.budget_limit,
                    priority=request.priority,
                    timeout_seconds=request.timeout_seconds,
                    requires_reasoning=request.requires_reasoning,
                    requires_math=request.requires_math,
                    requires_financial_knowledge=request.requires_financial_knowledge,
                    multi_step=request.multi_step,
                    confidence_threshold=request.confidence_threshold
                )
                # Call the API directly instead of recursing
                return await self._call_openai(retry_request, selected_model)
            
            # Handle Anthropic credit issues
            elif "credit balance is too low" in str(e) and selected_model in [AIModel.CLAUDE_3_5_SONNET, AIModel.CLAUDE_3_5_HAIKU]:
                logger.info(f"Anthropic credits low, falling back to GPT-4o-mini")
                fallback_request = AIRequest(
                    request_id=request.request_id,
                    request_type=request.request_type,
                    prompt=request.prompt,
                    context=request.context,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    model_preference=AIModel.GPT_4O_MINI,
                    budget_limit=request.budget_limit,
                    priority=request.priority,
                    timeout_seconds=request.timeout_seconds,
                    requires_reasoning=False,  # Disable reasoning for speed
                    requires_math=request.requires_math,
                    requires_financial_knowledge=request.requires_financial_knowledge,
                    multi_step=request.multi_step,
                    confidence_threshold=request.confidence_threshold
                )
                # Call the API directly instead of recursing
                return await self._call_openai(fallback_request, AIModel.GPT_4O_MINI)
            
            # Return a basic fallback response for other errors
            return AIResponse(
                request_id=request.request_id,
                model_used=selected_model,
                response="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                tokens_used=0,
                cost=0.0,
                latency_ms=0,
                timestamp=datetime.now(),
                confidence_score=0.1,
                reasoning_steps=[],
                metadata={"error": str(e), "fallback": True}
            )
    
    async def _call_openai(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Enhanced OpenAI API call"""
        start_time = time.time()
        
        messages = [{"role": "user", "content": request.prompt}]
        
        # Enhanced parameters for GPT-5
        # GPT-5 only supports temperature 1.0, other models can use custom temperature
        temperature = 1.0 if model == AIModel.GPT_5 else request.temperature
        
        params = {
            "model": model.value,
            "messages": messages,
            "max_completion_tokens": request.max_tokens or 4000,  # Use max_completion_tokens for newer models
            "temperature": temperature,
            "timeout": request.timeout_seconds
        }
        
        # Add specialized parameters for GPT-5 (only supported parameters)
        if model == AIModel.GPT_5:
            # Note: reasoning and mathematical_verification are not yet supported in OpenAI API
            # These would be handled in post-processing if needed
            if request.requires_reasoning:
                # Add reasoning instruction to the prompt instead
                params["messages"][0]["content"] += "\n\nPlease show your reasoning step by step."
        
        try:
            response = await self.openai_client.chat.completions.create(**params)
            
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * self.models[model].cost_per_1k_tokens
            
            return AIResponse(
                request_id=request.request_id,
                model_used=model,
                response=response.choices[0].message.content,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                timestamp=datetime.now(),
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
        except Exception as e:
            # Handle OpenAI API errors
            if "temperature" in str(e) and "unsupported" in str(e):
                logger.warning(f"OpenAI temperature error for {model.value}: {e}")
                # Retry with temperature 1.0
                params["temperature"] = 1.0
                response = await self.openai_client.chat.completions.create(**params)
                
                latency_ms = int((time.time() - start_time) * 1000)
                tokens_used = response.usage.total_tokens
                cost = (tokens_used / 1000) * self.models[model].cost_per_1k_tokens
                
                return AIResponse(
                    request_id=request.request_id,
                    model_used=model,
                    response=response.choices[0].message.content,
                    tokens_used=tokens_used,
                    cost=cost,
                    latency_ms=latency_ms,
                    timestamp=datetime.now(),
                    metadata={"finish_reason": response.choices[0].finish_reason, "temperature_fixed": True}
                )
            else:
                raise e
    
    async def _call_anthropic(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Enhanced Anthropic API call"""
        start_time = time.time()
        
        # Enhanced parameters for Claude
        params = {
            "model": model.value,
            "max_tokens": request.max_tokens or 4000,  # Anthropic still uses max_tokens
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}]
        }
        
        # Add specialized parameters for Claude 3.5
        if model in [AIModel.CLAUDE_3_5_SONNET, AIModel.CLAUDE_3_OPUS]:
            # Note: reasoning parameter is not supported in current Anthropic API
            # Add reasoning instruction to the prompt instead
            if request.requires_reasoning:
                params["messages"][0]["content"] += "\n\nPlease show your reasoning step by step."
        
        try:
            response = await self.anthropic_client.messages.create(**params)
            
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = (tokens_used / 1000) * self.models[model].cost_per_1k_tokens
            
            return AIResponse(
                request_id=request.request_id,
                model_used=model,
                response=response.content[0].text,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                timestamp=datetime.now(),
                metadata={"stop_reason": response.stop_reason}
            )
        except Exception as e:
            # Handle Anthropic credit issues and other errors
            if "credit balance is too low" in str(e) or "invalid_request_error" in str(e):
                logger.warning(f"Anthropic API error for {model.value}: {e}")
                # Fallback to GPT-4o-mini for cost-effective alternative
                fallback_model = AIModel.GPT_4O_MINI
                logger.info(f"Falling back to {fallback_model.value} due to Anthropic issues")
                return await self._call_openai(request, fallback_model)
            else:
                raise e
    
    async def _call_gemini(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Enhanced Google Gemini API call"""
        start_time = time.time()
        
        # Select appropriate Gemini model
        if model == AIModel.GEMINI_ULTRA:
            genai_model = self.gemini_ultra_model
        elif model == AIModel.GEMINI_PRO_VISION:
            genai_model = self.gemini_vision_model
        else:
            genai_model = self.gemini_model
        
        # Enhanced generation config
        config = genai.types.GenerationConfig(
            max_output_tokens=request.max_tokens or 4000,
            temperature=request.temperature
        )
        
        # Add specialized parameters for Gemini Ultra
        if model == AIModel.GEMINI_ULTRA:
            # Note: reasoning and mathematical_verification are not supported in current Gemini API
            # Add instructions to the prompt instead
            if request.requires_reasoning:
                request.prompt += "\n\nPlease show your reasoning step by step."
            if request.requires_math:
                request.prompt += "\n\nPlease verify your mathematical calculations."
        
        response = await genai_model.generate_content_async(
            request.prompt,
            generation_config=config
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = len(request.prompt.split()) + len(response.text.split())
        cost = (tokens_used / 1000) * self.models[model].cost_per_1k_tokens
        
        return AIResponse(
            request_id=request.request_id,
            model_used=model,
            response=response.text,
            tokens_used=tokens_used,
            cost=cost,
            latency_ms=latency_ms,
            timestamp=datetime.now(),
            metadata={"candidates": len(response.candidates)}
        )
    
    async def _calculate_confidence_score(self, request: AIRequest, response: AIResponse, model: AIModel) -> float:
        """Calculate confidence score for the response"""
        try:
            if self.confidence_predictor:
                # Use ML model to predict confidence
                features = np.array([[
                    response.latency_ms / 1000.0,
                    response.tokens_used / 1000.0,
                    self.models[model].reliability_score,
                    self.models[model].reasoning_capability,
                    len(response.response) / 1000.0
                ]])
                confidence = self.confidence_predictor.predict(features)[0]
                return min(1.0, max(0.0, confidence))
            else:
                # Fallback confidence calculation
                base_confidence = self.models[model].reliability_score
                
                # Adjust based on response characteristics
                if response.latency_ms < 1000:
                    base_confidence += 0.05
                if response.tokens_used > 100:
                    base_confidence += 0.02
                if len(response.response) > 100:
                    base_confidence += 0.03
                
                return min(1.0, base_confidence)
        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.8  # Default confidence
    
    async def _extract_reasoning_steps(self, response: str) -> List[str]:
        """Extract reasoning steps from response"""
        try:
            # Simple extraction of reasoning steps
            # In production, use more sophisticated NLP
            steps = []
            lines = response.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['step', 'reasoning', 'because', 'therefore', 'thus']):
                    steps.append(line.strip())
            return steps[:5]  # Limit to 5 steps
        except Exception as e:
            logger.warning(f"Error extracting reasoning steps: {e}")
            return []
    
    async def _verify_mathematics(self, response: str) -> Dict[str, Any]:
        """Verify mathematical content in response"""
        try:
            # Simple mathematical verification
            # In production, use more sophisticated mathematical verification
            import re
            
            # Find mathematical expressions
            math_expressions = re.findall(r'\d+\.?\d*\s*[+\-*/]\s*\d+\.?\d*', response)
            
            verification = {
                "expressions_found": len(math_expressions),
                "expressions": math_expressions,
                "verification_status": "basic_check_completed"
            }
            
            return verification
        except Exception as e:
            logger.warning(f"Error verifying mathematics: {e}")
            return {"error": str(e)}
    
    def _update_performance_tracking(self, model: AIModel, response: AIResponse, start_time: float):
        """Update enhanced model performance tracking"""
        performance = self.performance_tracking[model]
        performance.total_requests += 1
        performance.successful_requests += 1
        
        # Update running averages
        alpha = 0.1  # Smoothing factor
        performance.average_latency_ms = (
            (1 - alpha) * performance.average_latency_ms + 
            alpha * response.latency_ms
        )
        performance.average_cost = (
            (1 - alpha) * performance.average_cost + 
            alpha * response.cost
        )
        performance.reliability_score = (
            performance.successful_requests / performance.total_requests
        )
        performance.average_confidence = (
            (1 - alpha) * performance.average_confidence + 
            alpha * response.confidence_score
        )
        performance.last_updated = datetime.now()
    
    async def get_ensemble_prediction(self, request: AIRequest) -> Dict[str, Any]:
        """Get ensemble prediction from multiple models"""
        try:
            # Select top 3 models for ensemble
            suitable_models = []
            for model, capabilities in self.models.items():
                if self._is_model_suitable(model, request):
                    suitable_models.append((model, capabilities))
            
            # Sort by composite score and take top 3
            suitable_models.sort(key=lambda x: x[1].reliability_score, reverse=True)
            ensemble_models = suitable_models[:3]
            
            if len(ensemble_models) < 2:
                # Fallback to single model
                return await self.route_request(request)
            
            # Get predictions from multiple models
            predictions = []
            for model, _ in ensemble_models:
                try:
                    prediction = await self.route_request(request)
                    predictions.append(prediction)
                except Exception as e:
                    logger.warning(f"Ensemble model {model.value} failed: {e}")
            
            if not predictions:
                raise Exception("All ensemble models failed")
            
            # Combine predictions
            combined_response = self._combine_predictions(predictions)
            
            return {
                "ensemble_prediction": combined_response,
                "individual_predictions": [asdict(p) for p in predictions],
                "ensemble_size": len(predictions),
                "confidence": np.mean([p.confidence_score for p in predictions])
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            # Fallback to single model
            return await self.route_request(request)
    
    def _combine_predictions(self, predictions: List[AIResponse]) -> AIResponse:
        """Combine multiple predictions into a single response"""
        if len(predictions) == 1:
            return predictions[0]
        
        # Simple combination strategy (in production, use more sophisticated methods)
        combined_response = predictions[0].response
        combined_confidence = np.mean([p.confidence_score for p in predictions])
        combined_cost = sum([p.cost for p in predictions])
        combined_tokens = sum([p.tokens_used for p in predictions])
        combined_latency = max([p.latency_ms for p in predictions])
        
        return AIResponse(
            request_id=predictions[0].request_id,
            model_used=predictions[0].model_used,
            response=combined_response,
            tokens_used=combined_tokens,
            cost=combined_cost,
            latency_ms=combined_latency,
            timestamp=datetime.now(),
            confidence_score=combined_confidence,
            metadata={"ensemble": True, "model_count": len(predictions)}
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get enhanced performance statistics"""
        stats = {}
        for model, performance in self.performance_tracking.items():
            stats[model.value] = {
                "total_requests": performance.total_requests,
                "successful_requests": performance.successful_requests,
                "success_rate": performance.reliability_score,
                "average_latency_ms": performance.average_latency_ms,
                "average_cost": performance.average_cost,
                "average_confidence": performance.average_confidence,
                "specialized_performance": performance.specialized_performance,
                "last_updated": performance.last_updated.isoformat()
            }
        return stats
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get enhanced model capabilities"""
        capabilities = {}
        for model, caps in self.models.items():
            capabilities[model.value] = {
                "max_tokens": caps.max_tokens,
                "cost_per_1k_tokens": caps.cost_per_1k_tokens,
                "supports_vision": caps.supports_vision,
                "supports_functions": caps.supports_functions,
                "latency_ms": caps.latency_ms,
                "context_window": caps.context_window,
                "reliability_score": caps.reliability_score,
                "specialized_for": caps.specialized_for,
                "reasoning_capability": caps.reasoning_capability,
                "mathematical_accuracy": caps.mathematical_accuracy,
                "financial_knowledge": caps.financial_knowledge
            }
        return capabilities

# Global Advanced AI Router instance (lazy initialization)
advanced_ai_router = None

def get_advanced_ai_router() -> AdvancedAIRouter:
    """Get or create the global Advanced AI Router instance"""
    global advanced_ai_router
    if advanced_ai_router is None:
        advanced_ai_router = AdvancedAIRouter()
    return advanced_ai_router
