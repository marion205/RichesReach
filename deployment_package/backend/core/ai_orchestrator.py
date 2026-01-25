# core/ai_orchestrator.py
"""
AI Model Orchestrator (Router)
The "Brain" that routes requests to the optimal AI model (Gemini vs ChatGPT).

Hybrid Architecture: "The Brain & The Librarian"
- Gemini: Intake Layer (OCR, large documents, real-time market data)
- ChatGPT: Reasoning Layer (strategy, complex math, tax optimization)

This orchestrator makes the app "model-agnostic" - allowing easy swapping
of components as technology improves.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

from .intent_classifier import IntentClassifier, IntentType
from .pii_scrubber import PIIScrubber
from .gemini_service import GeminiService
from .ai_service_async import AIServiceAsync
from .algorithm_service import AlgorithmService, get_algorithm_service
from .ai_tools import AITools, get_tool_runner
from .persona_translation import PersonaTranslator, UserPersona
from .audit_trail import AuditTrailLogger, DecisionType, get_audit_trail
from .compliance_guardrails import ActionType, get_compliance_guardrails
from .refined_ai_prompts import RefinedAIPrompts
from .tax_alpha_calculator import get_tax_alpha_calculator

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Orchestrates AI model routing based on intent classification.
    
    Features:
    - Intent-based routing (Gemini vs ChatGPT)
    - PII scrubbing before API calls
    - Stateless requests (no data training)
    - Fallback handling
    - Performance monitoring
    """
    
    _instance: Optional['AIOrchestrator'] = None
    _lock = asyncio.Lock()
    
    def __init__(self) -> None:
        """Initialize orchestrator with all services."""
        self.intent_classifier = IntentClassifier()
        self.pii_scrubber = PIIScrubber(enable_strict_mode=True)
        
        # Services will be initialized lazily
        self._gemini_service: Optional[GeminiService] = None
        self._chatgpt_service: Optional[AIServiceAsync] = None
        self._algorithm_service: Optional[AlgorithmService] = None
        self._compliance_guardrails = None
        self._tax_alpha_calculator = None
        
        # Configuration
        self.enable_pii_scrubbing = getattr(settings, "ENABLE_PII_SCRUBBING", True)
        self.enable_hybrid_routing = getattr(settings, "ENABLE_HYBRID_AI_ROUTING", True)
        self.enable_function_calling = getattr(settings, "ENABLE_AI_FUNCTION_CALLING", True)
        self.enable_audit_trail = getattr(settings, "ENABLE_AUDIT_TRAIL", True)
        self.default_model = getattr(settings, "DEFAULT_AI_MODEL", "chatgpt")  # fallback
        
        # Services
        self.persona_translator = PersonaTranslator()
        self.audit_trail = get_audit_trail() if self.enable_audit_trail else None
    
    @classmethod
    async def get_instance(cls) -> 'AIOrchestrator':
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    async def _get_gemini_service(self) -> Optional[GeminiService]:
        """Lazy initialization of Gemini service"""
        if self._gemini_service is None:
            self._gemini_service = await GeminiService.get_instance()
        return self._gemini_service
    
    async def _get_chatgpt_service(self) -> Optional[AIServiceAsync]:
        """Lazy initialization of ChatGPT service"""
        if self._chatgpt_service is None:
            self._chatgpt_service = await AIServiceAsync.get_instance()
        return self._chatgpt_service
    
    def _get_algorithm_service(self) -> AlgorithmService:
        """Get algorithm service instance"""
        if self._algorithm_service is None:
            self._algorithm_service = get_algorithm_service()
        return self._algorithm_service
    
    def _scrub_user_data(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Scrub PII from messages and user context.
        
        Returns:
            Tuple of (scrubbed_messages, scrubbed_context)
        """
        if not self.enable_pii_scrubbing:
            return messages, user_context
        
        try:
            # Scrub messages
            scrubbed_messages = []
            for msg in messages:
                scrubbed_msg = msg.copy()
                if "content" in scrubbed_msg:
                    scrubbed_msg["content"] = self.pii_scrubber.scrub_text(
                        str(scrubbed_msg["content"]),
                        preserve_structure=True
                    )
                scrubbed_messages.append(scrubbed_msg)
            
            # Scrub user context
            scrubbed_context = None
            if user_context:
                scrubbed_context = self.pii_scrubber.scrub_text(
                    user_context,
                    preserve_structure=True
                )
            
            # Log scrubbing stats if anything was scrubbed
            stats = self.pii_scrubber.get_scrubbing_stats()
            if stats['total_scrubbed'] > 0:
                logger.info(
                    "PII scrubbing: %s items scrubbed, types: %s",
                    stats['total_scrubbed'],
                    stats['types_scrubbed']
                )
            
            return scrubbed_messages, scrubbed_context
        
        except Exception as e:
            logger.exception("PII scrubbing failed, using original data: %s", str(e))
            return messages, user_context
    
    async def route_request(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None,
        has_attachments: bool = False,
        attachment_type: Optional[str] = None,
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route request to appropriate AI model based on intent.
        
        Args:
            messages: List of message dictionaries
            user_context: Optional user context
            has_attachments: Whether query includes attachments
            attachment_type: Type of attachment
            force_model: Force use of specific model ('gemini' or 'chatgpt')
            
        Returns:
            Response dictionary with routing metadata:
            {
                "content": str,
                "confidence": float,
                "tokens_used": int,
                "model_used": str,
                "routing_decision": dict,
                "pii_scrubbed": bool,
                "latency_ms": int,
                ...
            }
        """
        import time
        t0 = time.perf_counter()
        
        # Extract user query for intent classification
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and msg.get("content"):
                user_query = str(msg.get("content"))
                break
        
        # Step 1: Scrub PII before sending to any API
        scrubbed_messages, scrubbed_context = self._scrub_user_data(messages, user_context)
        
        # Step 2: Classify intent and make routing decision
        if force_model:
            # Force routing (for testing or specific use cases)
            routing_decision = {
                'intent': IntentType.GENERAL_QUERY,
                'use_gemini': force_model.lower() == 'gemini',
                'use_chatgpt': force_model.lower() == 'chatgpt',
                'model': force_model.lower(),
                'reason': f"Forced routing to {force_model}"
            }
        elif not self.enable_hybrid_routing:
            # Hybrid routing disabled, use default
            routing_decision = {
                'intent': IntentType.GENERAL_QUERY,
                'use_gemini': False,
                'use_chatgpt': True,
                'model': self.default_model,
                'reason': 'Hybrid routing disabled, using default model'
            }
        else:
            routing_decision = self.intent_classifier.get_routing_decision(
                user_query,
                scrubbed_context,
                has_attachments,
                attachment_type
            )
        
        logger.info(
            "AI routing decision: intent=%s, model=%s, reason=%s",
            routing_decision['intent'].value,
            routing_decision['model'],
            routing_decision['reason']
        )
        
        # Step 3: Route to appropriate model or algorithm
        try:
            # Check if quantitative algorithm is needed
            # BUT: Direct Indexing, TSPT, and Tax Alpha Dashboard use function calling instead
            intent = routing_decision.get('intent')
            if intent and self.intent_classifier.requires_quantitative_algorithm(intent):
                # These intents should use function calling, not the old algorithm path
              if intent in [
                  IntentType.DIRECT_INDEXING,
                  IntentType.TAX_SMART_TRANSITION,
                  IntentType.TAX_ALPHA_DASHBOARD,
                  IntentType.FSS_SCORING
              ]:
                    # Fall through to ChatGPT with function calling below
                    routing_decision['use_chatgpt'] = True
                    routing_decision['model'] = 'chatgpt'
                else:
                    return await self._handle_quantitative_algorithm(
                        intent,
                        user_query,
                        scrubbed_messages,
                        scrubbed_context,
                        routing_decision,
                        t0
                    )
            
            if routing_decision['use_gemini']:
                gemini_service = await self._get_gemini_service()
                if gemini_service:
                    response = await gemini_service.get_chat_response_async(
                        scrubbed_messages,
                        user_context=scrubbed_context
                    )
                    response['routing_decision'] = routing_decision
                    response['pii_scrubbed'] = self.enable_pii_scrubbing
                    response['orchestrator_latency_ms'] = int((time.perf_counter() - t0) * 1000)
                    return response
                else:
                    logger.warning("Gemini service unavailable, falling back to ChatGPT")
                    routing_decision['model'] = 'chatgpt'
                    routing_decision['reason'] += ' (Gemini unavailable, using ChatGPT fallback)'
            
            if routing_decision['use_chatgpt'] or routing_decision['model'] == 'default':
                chatgpt_service = await self._get_chatgpt_service()
                if chatgpt_service:
                    # Enable function calling if enabled
                    tools = None
                    if self.enable_function_calling:
                        tools = AITools.get_tool_definitions()
                    
                    response = await chatgpt_service.get_chat_response_async(
                        scrubbed_messages,
                        user_context=scrubbed_context,
                        tools=tools
                    )
                    
                    # Handle function calls if present
                    algorithm_result = None
                    tool_name = None
                    if response.get("tool_calls"):
                        result = await self._handle_function_calls(
                            response,
                            scrubbed_messages,
                            scrubbed_context,
                            chatgpt_service,
                            tools,
                            t0
                        )
                        if isinstance(result, tuple) and len(result) == 3:
                            response, algorithm_result, tool_name = result
                        else:
                            response = result
                    
                    # Apply persona translation and add disclosure
                    final_response = await self._apply_persona_translation_and_disclosure(
                        response,
                        algorithm_result,
                        tool_name,
                        user_query,
                        routing_decision,
                        t0
                    )
                    
                    # Log to audit trail
                    if self.audit_trail:
                        self.audit_trail.log_final_response(
                            user_query=user_query,
                            llm_response=response.get("content", ""),
                            final_response=final_response.get("content", ""),
                            disclosure_version=final_response.get("disclosure_version", "1.0"),
                            disclosure_type=final_response.get("disclosure_type", "standard"),
                            model_used=routing_decision.get("model", "unknown"),
                            tool_called=tool_name,
                            tool_output=algorithm_result,
                            latency_ms=int((time.perf_counter() - t0) * 1000),
                            tokens_used=response.get("tokens_used", 0)
                        )
                    
                    final_response['routing_decision'] = routing_decision
                    final_response['pii_scrubbed'] = self.enable_pii_scrubbing
                    final_response['orchestrator_latency_ms'] = int((time.perf_counter() - t0) * 1000)
                    return final_response
                else:
                    logger.error("ChatGPT service unavailable, no fallback")
                    return self._fallback_response(
                        "AI services are temporarily unavailable.",
                        routing_decision,
                        int((time.perf_counter() - t0) * 1000)
                    )
            
            # Should not reach here, but handle gracefully
            return self._fallback_response(
                "Unable to route request.",
                routing_decision,
                int((time.perf_counter() - t0) * 1000)
            )
        
        except Exception as e:
            logger.exception("AI orchestrator error")
            return self._fallback_response(
                f"Error processing request: {str(e)}",
                routing_decision,
                int((time.perf_counter() - t0) * 1000),
                error_type=type(e).__name__
            )
    
    async def stream_request(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None,
        has_attachments: bool = False,
        attachment_type: Optional[str] = None,
        force_model: Optional[str] = None
    ):
        """
        Stream response from appropriate AI model.
        
        Yields dicts: {"type": "token|done|error", "content": str, "model": str}
        """
        # Extract user query
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and msg.get("content"):
                user_query = str(msg.get("content"))
                break
        
        # Scrub PII
        scrubbed_messages, scrubbed_context = self._scrub_user_data(messages, user_context)
        
        # Get routing decision
        if force_model:
            routing_decision = {
                'model': force_model.lower(),
                'use_gemini': force_model.lower() == 'gemini',
                'use_chatgpt': force_model.lower() == 'chatgpt',
            }
        else:
            routing_decision = self.intent_classifier.get_routing_decision(
                user_query,
                scrubbed_context,
                has_attachments,
                attachment_type
            )
        
        try:
            if routing_decision.get('use_gemini'):
                gemini_service = await self._get_gemini_service()
                if gemini_service:
                    # Gemini doesn't support streaming in this implementation
                    # For now, get full response and stream it
                    response = await gemini_service.get_chat_response_async(
                        scrubbed_messages,
                        user_context=scrubbed_context
                    )
                    # Stream word by word (simulated)
                    words = response.get('content', '').split()
                    for word in words:
                        yield {"type": "token", "content": word + " ", "model": "gemini"}
                    yield {"type": "done", "content": "", "model": "gemini"}
                    return
                else:
                    routing_decision['model'] = 'chatgpt'
            
            # Use ChatGPT for streaming (better support)
            chatgpt_service = await self._get_chatgpt_service()
            if chatgpt_service:
                async for chunk in chatgpt_service.stream_chat_response_async(
                    scrubbed_messages,
                    user_context=scrubbed_context
                ):
                    chunk['model'] = routing_decision.get('model', 'chatgpt')
                    yield chunk
            else:
                yield {"type": "error", "content": "AI services unavailable", "model": "unknown"}
        
        except Exception as e:
            logger.exception("Stream orchestrator error")
            yield {"type": "error", "content": str(e), "model": routing_decision.get('model', 'unknown')}
    
    def _fallback_response(
        self,
        message: str,
        routing_decision: Dict[str, Any],
        latency_ms: int,
        error_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate fallback response when AI services fail"""
        return {
            "content": message,
            "confidence": 0.3,
            "tokens_used": 0,
            "model_used": "fallback",
            "routing_decision": routing_decision,
            "pii_scrubbed": self.enable_pii_scrubbing,
            "latency_ms": latency_ms,
            "orchestrator_latency_ms": latency_ms,
            "fallback_used": True,
            "error_type": error_type,
        }
    
    async def _handle_quantitative_algorithm(
        self,
        intent: IntentType,
        user_query: str,
        messages: List[Dict[str, Any]],
        user_context: Optional[str],
        routing_decision: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """
        Handle quantitative algorithm requests.
        
        Workflow:
        1. LLM extracts variables from user query
        2. Call appropriate algorithm
        3. LLM translates results to user-friendly language
        """
        import time
        import json
        import re
        
        algorithm_service = self._get_algorithm_service()
        chatgpt_service = await self._get_chatgpt_service()
        
        try:
            # Step 1: Use LLM to extract variables from query
            extraction_prompt = self._build_extraction_prompt(intent, user_query, user_context)
            
            extraction_messages = [
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": user_query}
            ]
            
            extraction_response = await chatgpt_service.get_chat_response_async(
                extraction_messages,
                user_context=user_context
            )
            
            # Parse extracted variables (LLM returns JSON)
            extracted_vars = self._parse_extracted_variables(extraction_response.get("content", ""))
            
            # Step 2: Call appropriate algorithm
            algorithm_result = None
            
            if intent == IntentType.GOAL_SIMULATION:
                algorithm_result = algorithm_service.run_goal_simulation(
                    goal_amount=extracted_vars.get("goal_amount", 0),
                    time_horizon_months=extracted_vars.get("time_horizon_months", 24),
                    current_savings=extracted_vars.get("current_savings", 0),
                    monthly_contribution=extracted_vars.get("monthly_contribution", 0),
                    risk_level=extracted_vars.get("risk_level", "moderate")
                )
            
            elif intent == IntentType.RETIREMENT_SIMULATION:
                algorithm_result = algorithm_service.run_retirement_simulation(
                    current_age=extracted_vars.get("current_age", 30),
                    retirement_age=extracted_vars.get("retirement_age", 65),
                    current_savings=extracted_vars.get("current_savings", 0),
                    monthly_contribution=extracted_vars.get("monthly_contribution", 0),
                    target_amount=extracted_vars.get("target_amount")
                )
            
            elif intent == IntentType.PORTFOLIO_OPTIMIZATION:
                # Would need asset data from user context
                algorithm_result = {
                    "error": "Portfolio optimization requires asset data",
                    "algorithm": "portfolio_optimization"
                }
            
            elif intent == IntentType.TAX_LOSS_HARVESTING:
                positions = extracted_vars.get("positions", [])
                algorithm_result = algorithm_service.find_tax_loss_harvesting(
                    positions=positions,
                    realized_gains=extracted_vars.get("realized_gains", 0)
                )
            
            elif intent == IntentType.REBALANCING_CHECK:
                algorithm_result = algorithm_service.check_rebalancing(
                    current_allocation=extracted_vars.get("current_allocation", {}),
                    target_allocation=extracted_vars.get("target_allocation", {}),
                    market_volatility=extracted_vars.get("market_volatility", 0.15)
                )
            
            # Step 3: Use LLM to translate algorithm results to user-friendly language
            translation_prompt = self._build_translation_prompt(intent, algorithm_result, user_query)
            
            translation_messages = [
                {"role": "system", "content": translation_prompt},
                {"role": "user", "content": f"User asked: {user_query}\n\nAlgorithm result: {json.dumps(algorithm_result, indent=2)}"}
            ]
            
            translation_response = await chatgpt_service.get_chat_response_async(
                translation_messages,
                user_context=user_context
            )
            
            # Combine results
            return {
                "content": translation_response.get("content", ""),
                "confidence": 0.95,  # High confidence for algorithm-based results
                "tokens_used": extraction_response.get("tokens_used", 0) + translation_response.get("tokens_used", 0),
                "model_used": "algorithm+chatgpt",
                "routing_decision": routing_decision,
                "algorithm_result": algorithm_result,
                "pii_scrubbed": self.enable_pii_scrubbing,
                "latency_ms": int((time.perf_counter() - start_time) * 1000),
                "orchestrator_latency_ms": int((time.perf_counter() - start_time) * 1000),
                "fallback_used": False,
                "error_type": None
            }
        
        except Exception as e:
            logger.exception("Quantitative algorithm handling failed")
            return self._fallback_response(
                f"Error processing algorithm request: {str(e)}",
                routing_decision,
                int((time.perf_counter() - start_time) * 1000),
                error_type=type(e).__name__
            )
    
    def _build_extraction_prompt(self, intent: IntentType, user_query: str, user_context: Optional[str]) -> str:
        """Build prompt for LLM to extract variables from user query"""
        prompts = {
            IntentType.GOAL_SIMULATION: """Extract variables from the user's goal question. Return JSON with:
{
  "goal_amount": number (e.g., 50000),
  "time_horizon_months": number (e.g., 24),
  "current_savings": number (default 0 if not mentioned),
  "monthly_contribution": number (default 0 if not mentioned),
  "risk_level": "conservative" | "moderate" | "aggressive" (default "moderate")
}""",
            IntentType.RETIREMENT_SIMULATION: """Extract variables from the user's retirement question. Return JSON with:
{
  "current_age": number,
  "retirement_age": number (default 65),
  "current_savings": number,
  "monthly_contribution": number,
  "target_amount": number (optional)
}""",
        }
        
        base_prompt = prompts.get(intent, "Extract relevant variables from the user query and return as JSON.")
        return f"You are a financial data extractor. {base_prompt} Return ONLY valid JSON, no other text."
    
    def _build_translation_prompt(self, intent: IntentType, algorithm_result: Dict[str, Any], user_query: str) -> str:
        """Build prompt for LLM to translate algorithm results"""
        return f"""You are a financial advisor translating quantitative algorithm results into user-friendly advice.

The user asked: "{user_query}"

The algorithm returned these results. Translate them into a clear, supportive message:
- If success probability is high (>85%), be encouraging
- If success probability is low (<70%), suggest actionable improvements
- Always include the key numbers (probability, amounts, etc.)
- Be concise and avoid jargon
- Include risk disclaimers

Return a natural, conversational response that answers the user's question."""
    
    def _parse_extracted_variables(self, content: str) -> Dict[str, Any]:
        """Parse extracted variables from LLM response"""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return empty dict
        return {}
    
    async def _handle_function_calls(
        self,
        initial_response: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_context: Optional[str],
        chatgpt_service: AIServiceAsync,
        tools: Optional[List[Dict[str, Any]]],
        start_time: float
    ) -> Dict[str, Any]:
        """
        Handle function calls from ChatGPT.
        
        This implements the "Tool Runner" pattern:
        1. LLM decides to call a tool
        2. Execute the tool
        3. Send results back to LLM
        4. LLM generates final response
        """
        import time
        import json
        
        tool_runner = get_tool_runner()
        tool_calls = initial_response.get("tool_calls", [])
        
        if not tool_calls:
            return initial_response
        
        # Add assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": initial_response.get("content", ""),
            "tool_calls": tool_calls
        })
        
        # Execute each tool call
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            arguments_str = tool_call.get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            # Check if action requires compliance review
            compliance = await self._get_compliance_guardrails()
            action_type = self._get_action_type_for_tool(tool_name)
            
            if action_type and compliance.requires_review(action_type, arguments):
                # Create review and return review prompt instead of executing
                review = compliance.create_review(action_type, arguments)
                review_summary = compliance.get_review_summary(review)
                
                # Use refined prompt for compliance review
                from .refined_ai_prompts import RefinedAIPrompts
                review_prompt = RefinedAIPrompts.get_compliance_review_prompt(review_summary)
                
                # Return review response instead of executing
                tool_result = {
                    "requires_review": True,
                    "review_id": review.action_type.value + "_" + str(review.created_at.timestamp()),
                    "review_summary": review_summary,
                    "review_prompt": review_prompt,
                    "action_type": action_type.value
                }
            else:
                # Execute tool normally
                tool_result = tool_runner.execute_tool(tool_name, arguments)
            
            # Add tool result to messages
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "content": json.dumps(tool_result)
            })
        
        # Add tool results to messages
        messages.extend(tool_results)
        
        # Get final response from LLM with tool results
        final_response = await chatgpt_service.get_chat_response_async(
            messages,
            user_context=user_context,
            tools=tools
        )
        
        # Include tool execution info
        final_response["tool_calls_executed"] = len(tool_calls)
        final_response["tools_used"] = [tc.get("name") for tc in tool_calls]
        algorithm_results = [json.loads(tr.get("content", "{}")) for tr in tool_results]
        final_response["algorithm_results"] = algorithm_results
        
        # Return first algorithm result for persona translation
        algorithm_result = algorithm_results[0] if algorithm_results else None
        tool_name = tool_calls[0].get("name") if tool_calls else None
        
        return final_response, algorithm_result, tool_name
    
    async def _apply_persona_translation_and_disclosure(
        self,
        response: Dict[str, Any],
        algorithm_result: Optional[Dict[str, Any]],
        tool_name: Optional[str],
        user_query: str,
        routing_decision: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """
        Apply persona translation and add appropriate disclosure.
        
        This implements the "Persona-Driven Translation" pattern:
        - Translates algorithm results into supportive coaching
        - Adds appropriate disclosure based on algorithm used
        """
        import time
        
        content = response.get("content", "")
        
        # If algorithm was used, enhance with persona translation
        if algorithm_result and tool_name:
            # Check if this requires review
            if algorithm_result.get("requires_review"):
                # Use compliance review prompt
                from .refined_ai_prompts import RefinedAIPrompts
                review_prompt = algorithm_result.get("review_prompt", "")
                enhanced_content = review_prompt
                disclosure_type = "compliance_review"
            else:
                # Use refined prompts for Direct Indexing and TSPT
                from .refined_ai_prompts import RefinedAIPrompts
                
                if tool_name == "create_direct_index":
                    enhanced_content = RefinedAIPrompts.get_direct_indexing_prompt(
                        algorithm_result,
                        excluded_stocks=algorithm_result.get("excluded_stocks"),
                        portfolio_value=algorithm_result.get("portfolio_value", 0)
                    )
                elif tool_name == "create_tax_smart_transition":
                    enhanced_content = RefinedAIPrompts.get_tspt_prompt(
                        algorithm_result,
                        concentrated_position=algorithm_result.get("concentrated_position", {})
                    )
                else:
                    # Use standard persona translation
                    enhanced_content = content
                
                # Determine algorithm name for disclosure
                algorithm_name = tool_name.replace("run_", "").replace("_", "_")
                
                # Get disclosure
                disclosure = PersonaTranslator.get_disclosure_for_algorithm(algorithm_name)
                disclosure_type = "algorithmic" if algorithm_result else "standard"
                
                # Add disclosure as footer
                enhanced_content += f"\n\n---\n\n{disclosure}"
            
            response["content"] = enhanced_content
            response["disclosure_version"] = "1.0"
            response["disclosure_type"] = disclosure_type
            response["algorithm_used"] = algorithm_name
        else:
            # Standard AI disclosure
            standard_disclosure = """AI Disclosure: This response was generated with the assistance of artificial intelligence (Gemini/GPT-4). While we strive for accuracy, AI can produce "hallucinations" or errors. This is for educational purposes and does not constitute personalized financial, legal, or tax advice."""
            
            response["content"] = content + f"\n\n---\n\n{standard_disclosure}"
            response["disclosure_version"] = "1.0"
            response["disclosure_type"] = "standard"
        
        return response
    
    def _get_action_type_for_tool(self, tool_name: str):
        """Map tool name to ActionType for compliance"""
        from .compliance_guardrails import ActionType
        
        tool_action_map = {
            "create_direct_index": ActionType.DIRECT_INDEX_CREATION,
            "create_tax_smart_transition": ActionType.TSPT_TRANSITION,
            "find_tax_loss_harvesting_opportunities": ActionType.LARGE_TAX_LOSS_HARVEST,
            "check_portfolio_rebalancing": ActionType.PORTFOLIO_REBALANCE
        }
        
        return tool_action_map.get(tool_name)
    
    async def _get_compliance_guardrails(self):
        """Get compliance guardrails instance"""
        if self._compliance_guardrails is None:
            self._compliance_guardrails = get_compliance_guardrails()
        return self._compliance_guardrails
    
    async def _get_tax_alpha_calculator(self):
        """Get tax alpha calculator instance"""
        if self._tax_alpha_calculator is None:
            self._tax_alpha_calculator = get_tax_alpha_calculator()
        return self._tax_alpha_calculator
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all AI services"""
        gemini_service = await self._get_gemini_service()
        chatgpt_service = await self._get_chatgpt_service()
        
        status = {
            "orchestrator": "healthy",
            "hybrid_routing_enabled": self.enable_hybrid_routing,
            "pii_scrubbing_enabled": self.enable_pii_scrubbing,
        }
        
        # Check Gemini
        if gemini_service:
            gemini_status = await gemini_service.ping()
            status["gemini"] = gemini_status
        else:
            status["gemini"] = {"available": False}
        
        # Check ChatGPT
        if chatgpt_service:
            chatgpt_status = await chatgpt_service.ping()
            status["chatgpt"] = chatgpt_status
        else:
            status["chatgpt"] = {"available": False}
        
        return status


# Convenience function for backward compatibility
async def wealth_app_orchestrator(
    user_query: str,
    user_data_context: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Main orchestrator function (matches the conceptual code from the user's request).
    
    Args:
        user_query: User's query text
        user_data_context: Optional user context
        messages: Optional message history
        
    Returns:
        Response from appropriate AI model
    """
    orchestrator = await AIOrchestrator.get_instance()
    
    # Build messages if not provided
    if not messages:
        messages = [{"role": "user", "content": user_query}]
    
    return await orchestrator.route_request(
        messages,
        user_context=user_data_context
    )

