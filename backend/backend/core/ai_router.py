"""
AI Router Microservice - Phase 3 Advanced AI Integration
Intelligent routing between multiple AI models with context management and cost optimization
"""

import os
import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import aiohttp
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai

logger = logging.getLogger("richesreach")

class AIModel(Enum):
    """Supported AI models"""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

class RequestType(Enum):
    """Types of AI requests"""
    MARKET_ANALYSIS = "market_analysis"
    OPTIONS_STRATEGY = "options_strategy"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RISK_ASSESSMENT = "risk_assessment"
    NEWS_SENTIMENT = "news_sentiment"
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"

@dataclass
class ModelCapabilities:
    """Model capabilities and constraints"""
    max_tokens: int
    cost_per_1k_tokens: float
    supports_vision: bool
    supports_functions: bool
    latency_ms: int
    context_window: int
    reliability_score: float

@dataclass
class AIRequest:
    """AI request structure"""
    request_id: str
    request_type: RequestType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: float = 1.0  # Default to 1.0 for GPT-5 compatibility
    model_preference: Optional[AIModel] = None
    budget_limit: Optional[float] = None
    timeout_seconds: int = 30

@dataclass
class AIResponse:
    """AI response structure"""
    request_id: str
    model_used: AIModel
    response: str
    tokens_used: int
    cost: float
    latency_ms: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ModelPerformance:
    """Model performance tracking"""
    model: AIModel
    total_requests: int
    successful_requests: int
    average_latency_ms: float
    average_cost: float
    reliability_score: float
    last_updated: datetime

class AIRouter:
    """Intelligent AI Router with multi-model support"""
    
    def __init__(self):
        self.models = {
            AIModel.GPT_4O_MINI: ModelCapabilities(
                max_tokens=128000,
                cost_per_1k_tokens=0.00015,
                supports_vision=False,
                supports_functions=True,
                latency_ms=800,
                context_window=128000,
                reliability_score=0.95
            ),
            AIModel.GPT_4O: ModelCapabilities(
                max_tokens=128000,
                cost_per_1k_tokens=0.005,
                supports_vision=True,
                supports_functions=True,
                latency_ms=1200,
                context_window=128000,
                reliability_score=0.98
            ),
            AIModel.CLAUDE_3_5_SONNET: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.003,
                supports_vision=True,
                supports_functions=False,
                latency_ms=1000,
                context_window=200000,
                reliability_score=0.97
            ),
            AIModel.CLAUDE_3_5_HAIKU: ModelCapabilities(
                max_tokens=200000,
                cost_per_1k_tokens=0.00025,
                supports_vision=True,
                supports_functions=False,
                latency_ms=600,
                context_window=200000,
                reliability_score=0.94
            ),
            AIModel.GEMINI_PRO: ModelCapabilities(
                max_tokens=32000,
                cost_per_1k_tokens=0.0005,
                supports_vision=False,
                supports_functions=True,
                latency_ms=900,
                context_window=32000,
                reliability_score=0.92
            ),
            AIModel.GEMINI_PRO_VISION: ModelCapabilities(
                max_tokens=16000,
                cost_per_1k_tokens=0.0005,
                supports_vision=True,
                supports_functions=True,
                latency_ms=1100,
                context_window=16000,
                reliability_score=0.90
            )
        }
        
        self.performance_tracking: Dict[AIModel, ModelPerformance] = {}
        self.request_cache: Dict[str, AIResponse] = {}
        self.cache_ttl = timedelta(minutes=30)
        
        # Initialize clients
        self._initialize_clients()
        
        # Load performance data
        self._load_performance_data()
    
    def _initialize_clients(self):
        """Initialize AI model clients"""
        try:
            # OpenAI
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = openai.AsyncOpenAI()
            
            # Anthropic
            self.anthropic_client = AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            
            # Google Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            self.gemini_vision_model = genai.GenerativeModel('gemini-pro-vision')
            
            logger.info("✅ AI Router clients initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI clients: {e}")
            raise
    
    def _load_performance_data(self):
        """Load historical performance data"""
        for model in AIModel:
            self.performance_tracking[model] = ModelPerformance(
                model=model,
                total_requests=0,
                successful_requests=0,
                average_latency_ms=self.models[model].latency_ms,
                average_cost=self.models[model].cost_per_1k_tokens,
                reliability_score=self.models[model].reliability_score,
                last_updated=datetime.now()
            )
    
    def _get_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request"""
        content = f"{request.request_type.value}:{request.prompt}:{request.temperature}"
        if request.context:
            content += f":{json.dumps(request.context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _select_optimal_model(self, request: AIRequest) -> AIModel:
        """Select optimal model based on request characteristics"""
        # If model preference specified, use it
        if request.model_preference:
            return request.model_preference
        
        # Filter models by capabilities
        suitable_models = []
        for model, capabilities in self.models.items():
            # Check if model supports the request type
            if self._is_model_suitable(model, request):
                suitable_models.append((model, capabilities))
        
        if not suitable_models:
            # Fallback to GPT-4o-mini
            return AIModel.GPT_4O_MINI
        
        # Score models based on multiple factors
        scored_models = []
        for model, capabilities in suitable_models:
            performance = self.performance_tracking[model]
            
            # Calculate composite score
            cost_score = 1.0 / (capabilities.cost_per_1k_tokens + 0.001)
            latency_score = 1.0 / (capabilities.latency_ms / 1000.0 + 0.1)
            reliability_score = performance.reliability_score
            
            # Weight factors based on request type
            if request.request_type in [RequestType.MARKET_ANALYSIS, RequestType.RISK_ASSESSMENT]:
                # Prioritize reliability for financial analysis
                composite_score = (reliability_score * 0.5) + (cost_score * 0.2) + (latency_score * 0.3)
            elif request.request_type == RequestType.GENERAL_CHAT:
                # Balance all factors for general chat
                composite_score = (reliability_score * 0.3) + (cost_score * 0.4) + (latency_score * 0.3)
            else:
                # Default weighting
                composite_score = (reliability_score * 0.4) + (cost_score * 0.3) + (latency_score * 0.3)
            
            scored_models.append((model, composite_score))
        
        # Return highest scoring model
        return max(scored_models, key=lambda x: x[1])[0]
    
    def _is_model_suitable(self, model: AIModel, request: AIRequest) -> bool:
        """Check if model is suitable for the request"""
        capabilities = self.models[model]
        
        # Check token limits
        estimated_tokens = len(request.prompt.split()) * 1.3  # Rough estimation
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
        
        return True
    
    async def route_request(self, request: AIRequest) -> AIResponse:
        """Route AI request to optimal model"""
        start_time = time.time()
        
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
            # Route to appropriate model
            if selected_model in [AIModel.GPT_4O_MINI, AIModel.GPT_4O]:
                response = await self._call_openai(request, selected_model)
            elif selected_model in [AIModel.CLAUDE_3_5_SONNET, AIModel.CLAUDE_3_5_HAIKU]:
                response = await self._call_anthropic(request, selected_model)
            elif selected_model in [AIModel.GEMINI_PRO, AIModel.GEMINI_PRO_VISION]:
                response = await self._call_gemini(request, selected_model)
            else:
                raise ValueError(f"Unsupported model: {selected_model}")
            
            # Update performance tracking
            self._update_performance_tracking(selected_model, response, start_time)
            
            # Cache response
            self.request_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Error routing request {request.request_id}: {e}")
            # Try fallback model
            if selected_model != AIModel.GPT_4O_MINI:
                logger.info(f"Falling back to GPT-4o-mini for request {request.request_id}")
                fallback_request = AIRequest(
                    request_id=request.request_id,
                    request_type=request.request_type,
                    prompt=request.prompt,
                    context=request.context,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    model_preference=AIModel.GPT_4O_MINI,
                    budget_limit=request.budget_limit,
                    timeout_seconds=request.timeout_seconds
                )
                return await self.route_request(fallback_request)
            else:
                raise
    
    async def _call_openai(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Call OpenAI API"""
        start_time = time.time()
        
        messages = [{"role": "user", "content": request.prompt}]
        
        response = await self.openai_client.chat.completions.create(
            model=model.value,
            messages=messages,
            max_tokens=request.max_tokens or 4000,
            temperature=request.temperature,
            timeout=request.timeout_seconds
        )
        
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
    
    async def _call_anthropic(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Call Anthropic API"""
        start_time = time.time()
        
        response = await self.anthropic_client.messages.create(
            model=model.value,
            max_tokens=request.max_tokens or 4000,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}]
        )
        
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
    
    async def _call_gemini(self, request: AIRequest, model: AIModel) -> AIResponse:
        """Call Google Gemini API"""
        start_time = time.time()
        
        if model == AIModel.GEMINI_PRO_VISION:
            genai_model = self.gemini_vision_model
        else:
            genai_model = self.gemini_model
        
        response = await genai_model.generate_content_async(
            request.prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or 4000,
                temperature=request.temperature
            )
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
    
    def _update_performance_tracking(self, model: AIModel, response: AIResponse, start_time: float):
        """Update model performance tracking"""
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
        performance.last_updated = datetime.now()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models"""
        stats = {}
        for model, performance in self.performance_tracking.items():
            stats[model.value] = {
                "total_requests": performance.total_requests,
                "successful_requests": performance.successful_requests,
                "success_rate": performance.reliability_score,
                "average_latency_ms": performance.average_latency_ms,
                "average_cost": performance.average_cost,
                "last_updated": performance.last_updated.isoformat()
            }
        return stats
    
    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all models"""
        capabilities = {}
        for model, caps in self.models.items():
            capabilities[model.value] = asdict(caps)
        return capabilities

# Global AI Router instance
ai_router = AIRouter()
