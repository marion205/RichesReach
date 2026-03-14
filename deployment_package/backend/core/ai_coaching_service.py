"""
AI Coaching Service
====================
Generates personalized AI prompts based on user's investor archetype.
Implements the "Wealth Strategist" reasoning chain from the product blueprint.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from .investor_profile_types import (
    InvestorProfile,
    InvestorArchetype,
    CoachingTone,
    BiasType,
    UserMaturityStage,
    COACHING_PROMPTS,
    ARCHETYPE_METADATA,
)


class CoachingContext(Enum):
    """Types of coaching scenarios."""
    LEAK_REDIRECT = "leak_redirect"
    PORTFOLIO_REVIEW = "portfolio_review"
    MARKET_VOLATILITY = "market_volatility"
    BIAS_INTERVENTION = "bias_intervention"
    GOAL_PROGRESS = "goal_progress"
    ONBOARDING = "onboarding"
    GENERAL = "general"


@dataclass
class CoachingMessage:
    """A personalized coaching message."""
    headline: str
    body: str
    tone: str
    cta_text: Optional[str] = None
    cta_action: Optional[str] = None


class AICoachingService:
    """
    Generates personalized AI coaching based on user archetype.
    
    The AI speaks in different "personas":
    - The Guardian (Cautious Protector): Empathetic, protective
    - The Architect (Steady Builder): Logical, systematic
    - The Scout (Opportunity Hunter): Energetic, visionary
    - The Stabilizer (Reactive Trader): Calm, reassuring
    """

    def __init__(self):
        pass

    def get_system_prompt(
        self,
        profile: InvestorProfile,
        context: CoachingContext = CoachingContext.GENERAL,
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Generate the complete system prompt for the AI.
        
        This is injected into the LLM context before user queries.
        """
        # Base prompt
        base_prompt = """You are the RichesReach Behavioral Coach. Your goal is to guide the user toward long-term wealth using the principles of 'The Simple Path to Wealth' and Pompian's Behavioral Finance.

CORE PRINCIPLES:
- Always acknowledge psychological wins
- Use 'Wealth Redirect' language rather than 'Budgeting' language  
- Frame actions as 'Building a Fortress' or 'Accelerating the Millionaire Path'
- Never give direct financial advice — focus on education and coaching
- Quantify the future value of today's decisions when possible
- Keep responses concise but impactful

USER CONTEXT:
- Archetype: {archetype}
- Coaching Style: {coaching_style}
- Maturity Stage: {maturity_stage}
- Risk Tolerance: {risk_tolerance:.0f}/100
- Sophistication: {sophistication:.0f}/100
"""

        # Get tone-specific guidance
        tone_data = COACHING_PROMPTS.get(profile.coaching_tone, {})
        tone_prompt = tone_data.get("system_prompt", "")

        # Build the full prompt
        prompt = base_prompt.format(
            archetype=profile.archetype_title,
            coaching_style=profile.coaching_tone.value.replace("_", " ").title(),
            maturity_stage=profile.maturity_stage.value.title(),
            risk_tolerance=profile.dimensions.risk_tolerance,
            sophistication=profile.dimensions.sophistication,
        )

        prompt += f"\n\nYOUR COACHING PERSONA:\n{tone_prompt}"

        # Add context-specific instructions
        context_instructions = self._get_context_instructions(context, profile)
        if context_instructions:
            prompt += f"\n\nCURRENT CONTEXT:\n{context_instructions}"

        # Add bias awareness
        if profile.bias_matrix.active_biases:
            bias_names = ", ".join(b.bias_type.value for b in profile.bias_matrix.active_biases)
            prompt += f"\n\nACTIVE BIASES DETECTED: {bias_names}"
            prompt += "\nGently address these biases when relevant without being preachy."

        # Add additional context
        if additional_context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{additional_context}"

        # Add reasoning chain instruction
        prompt += """

REASONING CHAIN:
When providing advice, follow this structure:
1. Acknowledge: Recognize what the user has done/found
2. Validate: Connect it to their archetype and goals
3. Quantify: Show the future value when possible
4. Simplify: Give one clear next action
5. Encourage: Reinforce their progress

Keep responses under 100 words unless the user asks for details."""

        return prompt

    def _get_context_instructions(
        self,
        context: CoachingContext,
        profile: InvestorProfile,
    ) -> str:
        """Get context-specific instructions for the AI."""
        
        instructions = {
            CoachingContext.LEAK_REDIRECT: """
The user is reviewing subscription leaks and deciding what to redirect.
- Celebrate each leak they choose to redirect
- Quantify the 20-year future value of savings
- Frame cancellation as "purchasing future freedom"
- Connect savings to their Millionaire Path timeline
""",
            CoachingContext.PORTFOLIO_REVIEW: """
The user is reviewing their portfolio composition.
- Focus on concentration and diversification
- Speak to their specific biases if detected
- Recommend the Simple Path (VTI/index funds) as default
- Acknowledge good decisions they've made
""",
            CoachingContext.MARKET_VOLATILITY: """
The market is experiencing volatility and the user may be anxious.
- Be extra calming and reassuring
- Remind them of their long-term goals
- Reference their quiz answers about volatility comfort
- Discourage reactive selling unless thesis has changed
""",
            CoachingContext.BIAS_INTERVENTION: """
You're helping the user recognize a behavioral bias.
- Be gentle and non-judgmental
- Use their archetype's language patterns
- Provide concrete alternatives to biased behavior
- Connect to their stated long-term goals
""",
            CoachingContext.GOAL_PROGRESS: """
The user is checking progress toward their financial goals.
- Celebrate milestones achieved
- Quantify time saved from recent actions
- Project forward to show compounding effects
- Suggest one small optimization if appropriate
""",
            CoachingContext.ONBOARDING: """
The user just completed the investor quiz.
- Welcome them warmly
- Explain their archetype in positive terms
- Set expectations for their coaching relationship
- Suggest their first action based on priority stack
""",
        }

        return instructions.get(context, "")

    def generate_leak_coaching(
        self,
        profile: InvestorProfile,
        leak_name: str,
        monthly_amount: float,
        future_value: float,
        time_impact_days: int,
    ) -> CoachingMessage:
        """
        Generate a coaching message for a leak redirect decision.
        """
        tone = profile.coaching_tone

        if tone == CoachingTone.THE_GUARDIAN:
            headline = f"${monthly_amount:.0f}/mo Protected"
            body = (
                f"By redirecting {leak_name}, you've strengthened your financial fortress. "
                f"This ${monthly_amount:.0f}/mo becomes ${future_value:,.0f} in 20 years — "
                f"that's {time_impact_days} days closer to total financial security."
            )
            cta_text = "Protect More"

        elif tone == CoachingTone.THE_ARCHITECT:
            headline = f"System Optimized: +${future_value:,.0f}"
            body = (
                f"Eliminating {leak_name} increases your system's efficiency by ${monthly_amount:.0f}/mo. "
                f"The math: at 7% annual return, this compounds to ${future_value:,.0f} over 20 years. "
                f"Your Millionaire Path just accelerated by {time_impact_days} days."
            )
            cta_text = "Optimize More"

        elif tone == CoachingTone.THE_SCOUT:
            headline = f"${future_value:,.0f} Opportunity Captured!"
            body = (
                f"You just turned {leak_name} into future wealth. "
                f"That ${monthly_amount:.0f}/mo will grow to ${future_value:,.0f} — "
                f"real money that can fund your next big move."
            )
            cta_text = "Find More"

        else:  # THE_STABILIZER
            headline = f"Smart Move: ${monthly_amount:.0f}/mo Secured"
            body = (
                f"Redirecting {leak_name} was a calm, strategic decision. "
                f"This ${monthly_amount:.0f}/mo grows to ${future_value:,.0f} without any market stress. "
                f"You're {time_impact_days} days closer to your goal."
            )
            cta_text = "Continue"

        return CoachingMessage(
            headline=headline,
            body=body,
            tone=tone.value,
            cta_text=cta_text,
            cta_action="LeakRedirect",
        )

    def generate_bias_coaching(
        self,
        profile: InvestorProfile,
        bias_type: BiasType,
        severity: float,
        context_data: Dict[str, Any],
    ) -> CoachingMessage:
        """
        Generate a gentle intervention message for detected bias.
        """
        tone = profile.coaching_tone

        # Get bias-specific messaging
        bias_messages = {
            BiasType.CONCENTRATION: {
                CoachingTone.THE_GUARDIAN: (
                    "Portfolio Protection Alert",
                    f"I noticed your top holdings make up {context_data.get('concentration', 0):.0f}% of your portfolio. "
                    "While these may be great companies, spreading your eggs across more baskets protects your fortress. "
                    "Consider directing future contributions to a Total Market fund."
                ),
                CoachingTone.THE_ARCHITECT: (
                    "Concentration Risk Detected",
                    f"Your portfolio shows {context_data.get('concentration', 0):.0f}% concentration — "
                    "above the optimal 30% threshold. This creates single-point-of-failure risk. "
                    "The math favors broader diversification for long-term compounding."
                ),
                CoachingTone.THE_SCOUT: (
                    "High-Conviction Position Alert",
                    f"You're running concentrated at {context_data.get('concentration', 0):.0f}%. "
                    "Bold plays can pay off, but even scouts need a base camp. "
                    "Consider balancing with broad market exposure for asymmetric upside."
                ),
                CoachingTone.THE_STABILIZER: (
                    "Gentle Portfolio Check",
                    f"Your portfolio is quite concentrated at {context_data.get('concentration', 0):.0f}%. "
                    "This can amplify both gains and losses — which may increase stress. "
                    "A more balanced approach helps you sleep better during market swings."
                ),
            },
            BiasType.RECENCY: {
                CoachingTone.THE_GUARDIAN: (
                    "Chasing Heat Alert",
                    "I've noticed recent buys in assets that were already up significantly. "
                    "While momentum can continue, 'buying high' increases risk to your fortress. "
                    "Consider steady contributions to broad funds instead."
                ),
                CoachingTone.THE_ARCHITECT: (
                    "Recency Bias Detected",
                    f"{context_data.get('chasing_percent', 0):.0f}% of recent buys were in assets already up >20%. "
                    "The data shows dollar-cost averaging into indices outperforms chasing recent winners. "
                    "Your system works better with steady, unemotional contributions."
                ),
                CoachingTone.THE_SCOUT: (
                    "Trend-Chasing Alert",
                    "You're buying what's hot — that can work, but history shows today's winners "
                    "often become tomorrow's laggards. True alpha comes from finding the NEXT winner, "
                    "not piling into the current one."
                ),
                CoachingTone.THE_STABILIZER: (
                    "FOMO Check",
                    "It feels safe to buy what's going up, but that's often recency bias talking. "
                    "Your long-term plan doesn't need to chase trends — it just needs time and consistency."
                ),
            },
        }

        messages = bias_messages.get(bias_type, {})
        tone_message = messages.get(tone, ("Bias Detected", "Consider reviewing this aspect of your portfolio."))

        return CoachingMessage(
            headline=tone_message[0],
            body=tone_message[1],
            tone=tone.value,
            cta_text="Review Portfolio",
            cta_action="PortfolioContext",
        )

    def generate_volatility_coaching(
        self,
        profile: InvestorProfile,
        market_change: float,
        portfolio_change: float,
    ) -> CoachingMessage:
        """
        Generate calming message during market volatility.
        """
        tone = profile.coaching_tone
        is_down = market_change < 0

        if not is_down:
            # Market is up — celebrate but don't encourage overconfidence
            return CoachingMessage(
                headline="Your Patience Is Paying Off",
                body=(
                    f"Markets are up {abs(market_change):.1f}% recently. "
                    "This is what staying the course looks like. "
                    "Your job: keep contributing, let compounding work."
                ),
                tone=tone.value,
            )

        # Market is down — be calming
        if tone == CoachingTone.THE_GUARDIAN:
            headline = "Your Fortress Stands Strong"
            body = (
                f"Markets are down {abs(market_change):.1f}%, but your emergency fund protects you. "
                "This is temporary noise, not a signal to change your plan. "
                "Your long-term fortress is built on patience, not panic."
            )

        elif tone == CoachingTone.THE_ARCHITECT:
            headline = "Volatility Is Part of the System"
            body = (
                f"Markets down {abs(market_change):.1f}% — within historical norms. "
                "The math hasn't changed: time in market beats timing the market. "
                "Your system doesn't require you to react to short-term noise."
            )

        elif tone == CoachingTone.THE_SCOUT:
            headline = "Opportunity in Volatility"
            body = (
                f"Markets down {abs(market_change):.1f}% — that's a discount on future growth. "
                "If you have excess cash, this is when patient capital gets rewarded. "
                "The crowd panics; scouts position."
            )

        else:  # THE_STABILIZER
            headline = "Stay Calm, Stay Course"
            body = (
                f"I know a {abs(market_change):.1f}% drop feels uncomfortable. "
                "But remember your quiz — you said you could handle this. "
                "Your plan was built for days like today. No action needed."
            )

        return CoachingMessage(
            headline=headline,
            body=body,
            tone=tone.value,
            cta_text="See 20-Year View",
            cta_action="WealthArrival",
        )

    def generate_milestone_coaching(
        self,
        profile: InvestorProfile,
        milestone_name: str,
        milestone_value: float,
        next_milestone: Optional[str] = None,
    ) -> CoachingMessage:
        """
        Generate celebration message when user hits a milestone.
        """
        tone = profile.coaching_tone

        if tone == CoachingTone.THE_GUARDIAN:
            headline = f"🛡️ {milestone_name} Achieved!"
            body = (
                f"Your fortress has grown to ${milestone_value:,.0f}. "
                "Every dollar here is a dollar protecting your future. "
                f"{f'Next target: {next_milestone}.' if next_milestone else 'Keep building.'}"
            )

        elif tone == CoachingTone.THE_ARCHITECT:
            headline = f"📐 Milestone: {milestone_name}"
            body = (
                f"${milestone_value:,.0f} — your system is working. "
                "This is the power of consistent, automated contributions. "
                f"{f'The path continues to {next_milestone}.' if next_milestone else 'Maintain the system.'}"
            )

        elif tone == CoachingTone.THE_SCOUT:
            headline = f"🎯 {milestone_name} Unlocked!"
            body = (
                f"${milestone_value:,.0f} — you've captured this level. "
                "Each milestone funds future opportunities. "
                f"{f'Eyes on the next target: {next_milestone}.' if next_milestone else 'Keep scouting.'}"
            )

        else:  # THE_STABILIZER
            headline = f"✓ {milestone_name} Reached"
            body = (
                f"${milestone_value:,.0f} — you did this without panic or stress. "
                "Slow and steady wins. Your approach is validated. "
                f"{f'Next: {next_milestone}.' if next_milestone else 'Stay the course.'}"
            )

        return CoachingMessage(
            headline=headline,
            body=body,
            tone=tone.value,
            cta_text="View Progress",
            cta_action="WealthArrival",
        )


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════════════════

ai_coaching_service = AICoachingService()
