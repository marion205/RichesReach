# core/persona_translation.py
"""
Persona-Driven Translation System
Translates cold, hard algorithmic data into supportive, jargon-free behavioral coaching.

In 2026, the best financial apps use "Persona-Driven Translation" - the AI doesn't just
report numbers; it frames them within the user's emotional context while strictly
adhering to compliance.
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class UserPersona(str, Enum):
    """User persona types for personalized communication"""
    NOVICE_INVESTOR = "Novice Investor"
    FIRE_ENTHUSIAST = "FIRE Enthusiast"
    CONSERVATIVE_RETIREE = "Conservative Retiree"
    AGGRESSIVE_SAVER = "Aggressive Saver"
    BALANCED_BUILDER = "Balanced Builder"
    INCOME_FOCUSED = "Income Focused"


class PersonaTranslator:
    """
    Translates algorithmic results into persona-filtered, supportive messages.
    
    Uses the "Sandwich Method" for tough news:
    [Empathy] + [The Data/Fact] + [Actionable Next Step]
    """
    
    PERSONA_SYSTEM_PROMPT = """You are an "Empathetic Wealth Strategist." Your goal is to translate cold, hard data from our financial engines into supportive, jargon-free coaching.

### ROLE
You are a behavioral coach, not a calculator. You help users understand complex financial data in a way that feels supportive and actionable.

### COMMUNICATION PRINCIPLES

1. NEVER guess math. Use the exact numbers provided by the 'Tool Output'.

2. Use the "Sandwich Method" for tough news: [Empathy] + [The Data/Fact] + [Actionable Next Step].

3. Avoid "You should." Use "Based on the simulation, a potential path is..." (Regulatory compliance).

4. Use Analogies: Compare volatility to "airplane turbulence" or compound interest to "planting a forest."

5. Frame numbers in context: "64% success rate" becomes "We're seeing some headwinds, but you're still moving forward."

### HANDLING ALGORITHM OUTPUTS

- If Monte Carlo < 70%: Don't say "You will fail." Say "The current path has some headwinds. To get back on track, we can look at [Variable X]."

- If Portfolio is Unbalanced: Focus on "Risk Protection" rather than "Missed Gains."

- If Tax-Loss Harvesting available: Frame as "An opportunity to optimize your tax position."

- If Rebalancing needed: Explain timing: "Market volatility suggests waiting" or "This is an optimal window."

### REGULATORY GUARDRAILS

- You MUST NOT use the phrase "I guarantee" or "This will happen."

- Use "The simulation suggests..." or "Historically, this pattern indicates..."

- If the user asks for a specific stock "buy" or "sell" recommendation, you MUST state: "As an AI, I cannot provide specific trade executions or investment mandates. I can, however, analyze the risk profile of $TICKER for you."

- Always include appropriate risk disclaimers based on the algorithm used.

### PERSONA ADAPTATION

Adapt your tone based on the user's persona:
- **Novice Investor**: Use simple analogies, avoid jargon, focus on education
- **FIRE Enthusiast**: Use efficiency language, focus on optimization
- **Conservative Retiree**: Emphasize safety, stability, risk protection
- **Aggressive Saver**: Focus on growth potential, opportunity
- **Balanced Builder**: Emphasize steady progress, diversification
- **Income Focused**: Focus on cash flow, stability, yield

### CONTEXT INJECTION

When translating algorithm results, consider:
- User Sentiment: (e.g., "User is anxious about the market")
- User Persona: (e.g., "Novice Investor", "FIRE Enthusiast")
- The "Why": (e.g., "The goal is a house, which is a high-priority 'Need'")
- Goal Priority: "Need" vs "Want" vs "Dream"

Translate the algorithm output into a supportive, persona-filtered message that helps the user understand and act on the results."""
    
    @staticmethod
    def build_translation_prompt(
        algorithm_result: Dict[str, Any],
        algorithm_name: str,
        user_persona: Optional[UserPersona] = None,
        user_sentiment: Optional[str] = None,
        goal_context: Optional[str] = None
    ) -> str:
        """
        Build a prompt for translating algorithm results into persona-filtered messages.
        
        Args:
            algorithm_result: Raw algorithm output
            algorithm_name: Name of the algorithm used
            user_persona: User's financial persona
            user_sentiment: User's emotional state
            goal_context: Context about the goal (e.g., "high-priority need")
            
        Returns:
            System prompt for translation
        """
        prompt = PersonaTranslator.PERSONA_SYSTEM_PROMPT
        
        # Add persona context
        if user_persona:
            prompt += f"\n\n### USER PERSONA\nUser persona: {user_persona.value}. Adapt your communication style accordingly."
        
        # Add sentiment context
        if user_sentiment:
            prompt += f"\n\n### USER SENTIMENT\nUser sentiment: {user_sentiment}. Adjust your tone to be supportive and empathetic."
        
        # Add goal context
        if goal_context:
            prompt += f"\n\n### GOAL CONTEXT\n{goal_context}"
        
        # Add algorithm result
        import json
        prompt += f"\n\n### ALGORITHM OUTPUT\nAlgorithm: {algorithm_name}\nResult: {json.dumps(algorithm_result, indent=2)}"
        
        prompt += "\n\nTranslate this algorithm output into a supportive, persona-filtered message. Use the Sandwich Method for any challenging results. Include appropriate risk disclaimers."
        
        return prompt
    
    @staticmethod
    def translate_monte_carlo_result(
        result: Dict[str, Any],
        user_persona: Optional[UserPersona] = None,
        goal_context: Optional[str] = None
    ) -> str:
        """
        Translate Monte Carlo result into persona-filtered message.
        
        Example translation:
        Raw: {"success_probability": 0.64, "median_outcome": 42000, "shortfall": 8000}
        Translated: "I've run 10,000 different market scenarios... Currently, we're seeing a 64% success rate. Think of this like a flight with a bit of unexpected headwind..."
        """
        success_prob = result.get("success_probability", 0)
        median_outcome = result.get("median_outcome", 0)
        required_savings = result.get("required_monthly_savings")
        
        # Determine tone based on probability
        if success_prob < 0.70:
            tone = "supportive_improvement"
        elif success_prob < 0.85:
            tone = "cautious_optimism"
        else:
            tone = "confident"
        
        # Build message based on tone
        if tone == "supportive_improvement":
            message = f"I've run 10,000 different market scenarios for your goal. Currently, we're seeing a {success_prob:.0%} success rate.\n\n"
            message += "Think of this like a flight with a bit of unexpected headwind—you're still moving forward, but we might arrive a little later than planned.\n\n"
            if required_savings:
                message += f"To get your confidence score back up to 90%, the most effective lever we can pull is increasing your monthly savings by about ${required_savings:.0f}.\n\n"
            message += "Would you like to see how that small change shifts your timeline?"
        
        elif tone == "cautious_optimism":
            message = f"Based on 10,000 market simulations, you have a {success_prob:.0%} chance of reaching your goal.\n\n"
            message += "You're on a solid path, but there's room to strengthen your position. "
            if required_savings:
                message += f"Increasing your monthly savings by ${required_savings:.0f} would boost your success probability to over 90%.\n\n"
            message += "This gives you a stronger buffer against market volatility."
        
        else:  # confident
            message = f"Excellent news! Based on 10,000 market simulations, you have a {success_prob:.0%} chance of reaching your goal.\n\n"
            message += "You're on track, but remember: these are projections based on historical patterns. "
            message += "Staying consistent with your savings plan is key to maintaining this trajectory."
        
        return message
    
    @staticmethod
    def get_disclosure_for_algorithm(algorithm_name: str) -> str:
        """
        Get appropriate disclosure for algorithm used.
        
        Returns:
            Disclosure text based on algorithm type
        """
        disclosures = {
            "monte_carlo": """Model Transparency: This projection is based on a Monte Carlo simulation using historical market data. Past performance is not indicative of future results. All simulations are mathematical estimates and do not guarantee specific outcomes. Our AI acts as a translator for these deterministic models; however, market volatility, geopolitical events, and legislative changes may render these projections inaccurate.""",
            
            "portfolio_optimization": """Portfolio Optimization Disclosure: This allocation recommendation is based on Modern Portfolio Theory (MPT) and historical return/risk data. Optimal allocations may change with market conditions. This is not personalized investment advice. Consult a licensed financial advisor before making investment decisions.""",
            
            "tax_loss_harvesting": """Tax-Loss Harvesting Disclosure: Tax-loss harvesting strategies should be reviewed with a qualified tax professional. Tax laws vary by jurisdiction and may change. This analysis is for educational purposes and does not constitute tax advice.""",
            
            "rebalancing": """Rebalancing Analysis Disclosure: Rebalancing recommendations are based on portfolio drift and market volatility analysis. Transaction costs and tax implications should be considered. This is not a recommendation to trade.""",
            
            "default": """AI Disclosure: This response was generated with the assistance of artificial intelligence (Gemini/GPT-4). While we strive for accuracy, AI can produce "hallucinations" or errors. This is for educational purposes and does not constitute personalized financial, legal, or tax advice."""
        }
        
        return disclosures.get(algorithm_name.lower(), disclosures["default"])


# Singleton instance
_persona_translator = PersonaTranslator()


def translate_algorithm_result(
    algorithm_result: Dict[str, Any],
    algorithm_name: str,
    user_persona: Optional[UserPersona] = None,
    user_sentiment: Optional[str] = None,
    goal_context: Optional[str] = None
) -> str:
    """Convenience function for persona translation"""
    return _persona_translator.build_translation_prompt(
        algorithm_result,
        algorithm_name,
        user_persona,
        user_sentiment,
        goal_context
    )

