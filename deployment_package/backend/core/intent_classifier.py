# core/intent_classifier.py
"""
Intent Classification for AI Model Routing
Determines which AI model (Gemini vs ChatGPT) should handle a request.

Uses a fast, lightweight model (gpt-4o-mini or gemini-flash) for classification.
"""
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Intent types for routing decisions"""
    MARKET_DATA = "MARKET_DATA"
    LARGE_DOCUMENT_ANALYSIS = "LARGE_DOCUMENT_ANALYSIS"
    OCR_DOCUMENT = "OCR_DOCUMENT"
    STRATEGY_PLANNING = "STRATEGY_PLANNING"
    COMPLEX_MATH = "COMPLEX_MATH"
    TAX_OPTIMIZATION = "TAX_OPTIMIZATION"
    RETIREMENT_PLANNING = "RETIREMENT_PLANNING"
    GENERAL_QUERY = "GENERAL_QUERY"
    TRANSACTION_ANALYSIS = "TRANSACTION_ANALYSIS"
    # Quantitative algorithm intents
    GOAL_SIMULATION = "GOAL_SIMULATION"  # "Can I afford X in Y years?"
    RETIREMENT_SIMULATION = "RETIREMENT_SIMULATION"  # Retirement planning with Monte Carlo
    PORTFOLIO_OPTIMIZATION = "PORTFOLIO_OPTIMIZATION"  # MPT/Black-Litterman
    TAX_LOSS_HARVESTING = "TAX_LOSS_HARVESTING"  # TLH opportunities
    REBALANCING_CHECK = "REBALANCING_CHECK"  # Should I rebalance?


class IntentClassifier:
    """
    Classifies user queries to determine optimal AI model routing.
    
    Routing Rules:
    - Gemini: Market data, large documents, OCR, transaction history analysis
    - ChatGPT: Strategy planning, complex math, tax optimization, retirement planning
    """
    
    # Keywords that indicate Gemini should handle the request
    GEMINI_KEYWORDS = {
        IntentType.MARKET_DATA: [
            'market', 'stock price', 'quote', 'ticker', 'trading', 'real-time',
            'current price', 'live data', 'market data', 'stock market',
            's&p 500', 'nasdaq', 'dow jones', 'crypto', 'forex', 'currency'
        ],
        IntentType.LARGE_DOCUMENT_ANALYSIS: [
            'document', 'pdf', 'prospectus', 'annual report', 'filing',
            '10-k', '10-q', 'sec filing', 'financial statement',
            'balance sheet', 'income statement', 'cash flow'
        ],
        IntentType.OCR_DOCUMENT: [
            'receipt', 'tax form', 'w-2', '1099', 'invoice', 'bill',
            'scan', 'image', 'photo', 'upload', 'extract', 'read document'
        ],
        IntentType.TRANSACTION_ANALYSIS: [
            'transaction history', 'spending', 'expenses', '5 years',
            'monthly spending', 'yearly spending', 'financial history',
            'bank statement', 'credit card statement'
        ]
    }
    
    # Keywords that indicate ChatGPT should handle the request
    CHATGPT_KEYWORDS = {
        IntentType.STRATEGY_PLANNING: [
            'strategy', 'plan', 'goal', 'how to', 'should i', 'recommend',
            'investment strategy', 'portfolio', 'allocation', 'diversify',
            'buy a house', 'save for', 'retirement plan', 'college fund'
        ],
        IntentType.COMPLEX_MATH: [
            'calculate', 'compound interest', 'roi', 'return on investment',
            'present value', 'future value', 'annuity', 'mortgage',
            'loan payment', 'interest rate', 'yield', 'dividend'
        ],
        IntentType.TAX_OPTIMIZATION: [
            'tax', 'tax-loss', 'harvesting', 'capital gains', 'deduction',
            'tax bracket', 'irs', 'tax strategy', 'tax planning'
        ],
        IntentType.RETIREMENT_PLANNING: [
            'retirement', '401k', 'ira', 'roth', 'social security',
            'pension', 'retire', 'retirement age', 'nest egg'
        ]
    }
    
    # Keywords that indicate quantitative algorithms should be used
    ALGORITHM_KEYWORDS = {
        IntentType.GOAL_SIMULATION: [
            'can i afford', 'afford', 'goal', 'save for', 'reach',
            'wedding', 'house', 'car', 'vacation', 'in X years', 'in X months'
        ],
        IntentType.RETIREMENT_SIMULATION: [
            'retirement simulation', 'retirement safety', 'retirement probability',
            'will i have enough', 'retirement monte carlo', 'retirement forecast'
        ],
        IntentType.PORTFOLIO_OPTIMIZATION: [
            'optimize portfolio', 'best allocation', 'optimal mix', 'portfolio optimization',
            'efficient frontier', 'sharpe ratio', 'risk return'
        ],
        IntentType.TAX_LOSS_HARVESTING: [
            'tax loss', 'harvest losses', 'offset gains', 'tax savings',
            'losing positions', 'realized gains'
        ],
        IntentType.REBALANCING_CHECK: [
            'rebalance', 'rebalancing', 'portfolio drift', 'should i rebalance',
            'when to rebalance', 'rebalancing timing'
        ]
    }
    
    def __init__(self, use_ml_classifier: bool = False):
        """
        Initialize intent classifier.
        
        Args:
            use_ml_classifier: If True, uses ML model for classification (future enhancement)
        """
        self.use_ml_classifier = use_ml_classifier
    
    def classify_intent(
        self, 
        user_query: str, 
        user_context: Optional[str] = None,
        has_attachments: bool = False,
        attachment_type: Optional[str] = None
    ) -> IntentType:
        """
        Classify user intent from query text.
        
        Args:
            user_query: User's query text
            user_context: Optional context about user
            has_attachments: Whether query includes file attachments
            attachment_type: Type of attachment (pdf, image, etc.)
            
        Returns:
            IntentType enum value
        """
        if not user_query:
            return IntentType.GENERAL_QUERY
        
        query_lower = user_query.lower()
        
        # Check for document/attachment indicators (strong signal for Gemini)
        if has_attachments:
            if attachment_type in ['pdf', 'image', 'jpg', 'png', 'jpeg']:
                return IntentType.OCR_DOCUMENT
            elif attachment_type in ['txt', 'doc', 'docx']:
                return IntentType.LARGE_DOCUMENT_ANALYSIS
        
        # Check for large document keywords
        if any(keyword in query_lower for keyword in self.GEMINI_KEYWORDS[IntentType.LARGE_DOCUMENT_ANALYSIS]):
            return IntentType.LARGE_DOCUMENT_ANALYSIS
        
        # Check for OCR keywords
        if any(keyword in query_lower for keyword in self.GEMINI_KEYWORDS[IntentType.OCR_DOCUMENT]):
            return IntentType.OCR_DOCUMENT
        
        # Check for transaction analysis (large context needed)
        if any(keyword in query_lower for keyword in self.GEMINI_KEYWORDS[IntentType.TRANSACTION_ANALYSIS]):
            return IntentType.TRANSACTION_ANALYSIS
        
        # Check for market data (real-time, large context)
        if any(keyword in query_lower for keyword in self.GEMINI_KEYWORDS[IntentType.MARKET_DATA]):
            return IntentType.MARKET_DATA
        
        # Check for strategy planning (ChatGPT strength)
        if any(keyword in query_lower for keyword in self.CHATGPT_KEYWORDS[IntentType.STRATEGY_PLANNING]):
            return IntentType.STRATEGY_PLANNING
        
        # Check for complex math (ChatGPT strength)
        if any(keyword in query_lower for keyword in self.CHATGPT_KEYWORDS[IntentType.COMPLEX_MATH]):
            return IntentType.COMPLEX_MATH
        
        # Check for tax optimization (ChatGPT strength)
        if any(keyword in query_lower for keyword in self.CHATGPT_KEYWORDS[IntentType.TAX_OPTIMIZATION]):
            return IntentType.TAX_OPTIMIZATION
        
        # Check for retirement planning (ChatGPT strength)
        if any(keyword in query_lower for keyword in self.CHATGPT_KEYWORDS[IntentType.RETIREMENT_PLANNING]):
            return IntentType.RETIREMENT_PLANNING
        
        # Check for quantitative algorithm intents
        if any(keyword in query_lower for keyword in self.ALGORITHM_KEYWORDS[IntentType.GOAL_SIMULATION]):
            return IntentType.GOAL_SIMULATION
        
        if any(keyword in query_lower for keyword in self.ALGORITHM_KEYWORDS[IntentType.RETIREMENT_SIMULATION]):
            return IntentType.RETIREMENT_SIMULATION
        
        if any(keyword in query_lower for keyword in self.ALGORITHM_KEYWORDS[IntentType.PORTFOLIO_OPTIMIZATION]):
            return IntentType.PORTFOLIO_OPTIMIZATION
        
        if any(keyword in query_lower for keyword in self.ALGORITHM_KEYWORDS[IntentType.TAX_LOSS_HARVESTING]):
            return IntentType.TAX_LOSS_HARVESTING
        
        if any(keyword in query_lower for keyword in self.ALGORITHM_KEYWORDS[IntentType.REBALANCING_CHECK]):
            return IntentType.REBALANCING_CHECK
        
        # Default to general query (will use default model)
        return IntentType.GENERAL_QUERY
    
    def should_use_gemini(self, intent: IntentType) -> bool:
        """
        Determine if Gemini should handle this intent.
        
        Args:
            intent: Classified intent type
            
        Returns:
            True if Gemini should handle, False if ChatGPT should handle
        """
        gemini_intents = {
            IntentType.MARKET_DATA,
            IntentType.LARGE_DOCUMENT_ANALYSIS,
            IntentType.OCR_DOCUMENT,
            IntentType.TRANSACTION_ANALYSIS
        }
        return intent in gemini_intents
    
    def should_use_chatgpt(self, intent: IntentType) -> bool:
        """
        Determine if ChatGPT should handle this intent.
        
        Args:
            intent: Classified intent type
            
        Returns:
            True if ChatGPT should handle, False if Gemini should handle
        """
        chatgpt_intents = {
            IntentType.STRATEGY_PLANNING,
            IntentType.COMPLEX_MATH,
            IntentType.TAX_OPTIMIZATION,
            IntentType.RETIREMENT_PLANNING
        }
        return intent in chatgpt_intents
    
    def requires_quantitative_algorithm(self, intent: IntentType) -> bool:
        """
        Determine if this intent requires a quantitative algorithm.
        
        Args:
            intent: Classified intent type
            
        Returns:
            True if quantitative algorithm should be used
        """
        algorithm_intents = {
            IntentType.GOAL_SIMULATION,
            IntentType.RETIREMENT_SIMULATION,
            IntentType.PORTFOLIO_OPTIMIZATION,
            IntentType.TAX_LOSS_HARVESTING,
            IntentType.REBALANCING_CHECK
        }
        return intent in algorithm_intents
    
    def get_routing_decision(
        self,
        user_query: str,
        user_context: Optional[str] = None,
        has_attachments: bool = False,
        attachment_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete routing decision with metadata.
        
        Args:
            user_query: User's query text
            user_context: Optional context
            has_attachments: Whether attachments are present
            attachment_type: Type of attachment
            
        Returns:
            Dictionary with routing decision:
            {
                'intent': IntentType,
                'use_gemini': bool,
                'use_chatgpt': bool,
                'model': str,  # 'gemini' or 'chatgpt' or 'default'
                'reason': str  # Explanation of routing decision
            }
        """
        intent = self.classify_intent(user_query, user_context, has_attachments, attachment_type)
        
        use_gemini = self.should_use_gemini(intent)
        use_chatgpt = self.should_use_chatgpt(intent)
        
        if self.requires_quantitative_algorithm(intent):
            model = 'algorithm'
            reason = f"Using quantitative algorithm for {intent.value} (LLM will translate results)"
        elif use_gemini:
            model = 'gemini'
            reason = f"Routing to Gemini for {intent.value} (large context window, real-time data)"
        elif use_chatgpt:
            model = 'chatgpt'
            reason = f"Routing to ChatGPT for {intent.value} (systematic reasoning, complex logic)"
        else:
            model = 'default'
            reason = f"Using default model for {intent.value}"
        
        return {
            'intent': intent,
            'use_gemini': use_gemini,
            'use_chatgpt': use_chatgpt,
            'model': model,
            'reason': reason
        }


# Singleton instance
_default_classifier = IntentClassifier()


def classify_intent(user_query: str, **kwargs) -> IntentType:
    """Convenience function for intent classification."""
    return _default_classifier.classify_intent(user_query, **kwargs)

