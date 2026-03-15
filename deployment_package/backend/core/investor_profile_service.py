"""
Investor Profile Service
========================
Behavioral finance engine for RichesReach.
Implements the Pompian framework for investor psychology.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

from .investor_profile_types import (
    InvestorArchetype,
    InvestorProfile,
    QuizDimensions,
    BiasMatrix,
    BiasScore,
    BiasType,
    CoachingTone,
    UserMaturityStage,
    DefaultStrategy,
    QuizAnswer,
    QuizQuestion,
    QuizOption,
    ARCHETYPE_METADATA,
    COACHING_PROMPTS,
)


# ══════════════════════════════════════════════════════════════════════════════
# QUIZ DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_quiz_questions() -> List[Dict[str, Any]]:
    """Return the 10-question Behavioral Identity Quiz."""
    questions = [
        # Q1: Loss Aversion
        {
            "id": "q1_market_drop",
            "text": "A stock you own drops 15% in one week due to general market noise. What's your gut reaction?",
            "subtext": "Be honest — what would you actually do, not what you think is 'correct'.",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Sell immediately to protect what's left", "rt": -20, "lc": -10, "la": 30, "s": 0},
                {"id": "b", "text": "Do nothing and wait for recovery", "rt": 10, "lc": 10, "la": 0, "s": 10},
                {"id": "c", "text": "Buy more at the 'discount'", "rt": 25, "lc": 20, "la": -20, "s": 15},
                {"id": "d", "text": "Research why it dropped before deciding", "rt": 5, "lc": 15, "la": 5, "s": 20},
            ],
        },
        # Q2: Wealth Philosophy
        {
            "id": "q2_wealth_view",
            "text": "Which statement best describes your view on wealth?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "I want to ensure I never backslide into financial stress", "rt": -10, "lc": 5, "la": 20, "s": 0},
                {"id": "b", "text": "I want my money to work as hard as I do", "rt": 15, "lc": 20, "la": 0, "s": 10},
                {"id": "c", "text": "I want to find opportunities before others do", "rt": 25, "lc": 25, "la": -10, "s": 15},
                {"id": "d", "text": "I just want simple, automatic growth without thinking about it", "rt": 10, "lc": 10, "la": 5, "s": 5},
            ],
        },
        # Q3: Locus of Control (Slider)
        {
            "id": "q3_luck_vs_skill",
            "text": "How much of financial success do you attribute to your own decisions vs. luck/timing?",
            "subtext": "Slide toward which factor you believe matters more.",
            "question_type": "slider",
            "slider_min": 0,
            "slider_max": 10,
            "slider_labels": ["Mostly Luck", "50/50", "Mostly My Decisions"],
            "dimension": "locus_of_control",
            "weight": 10,
        },
        # Q4: Investment Horizon
        {
            "id": "q4_horizon",
            "text": "What's your primary investment time horizon?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Less than 2 years", "rt": -15, "lc": 0, "la": 10, "s": 5},
                {"id": "b", "text": "2-5 years", "rt": 5, "lc": 5, "la": 5, "s": 10},
                {"id": "c", "text": "5-15 years", "rt": 15, "lc": 10, "la": 0, "s": 15},
                {"id": "d", "text": "15+ years (retirement)", "rt": 25, "lc": 15, "la": -10, "s": 10},
            ],
        },
        # Q5: Volatility Comfort
        {
            "id": "q5_volatility",
            "text": "You check your portfolio and it's down 25% from last month. How do you feel?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Sick to my stomach — I'd lose sleep over this", "rt": -25, "lc": -10, "la": 30, "s": 0},
                {"id": "b", "text": "Uncomfortable, but I know it's part of investing", "rt": 5, "lc": 10, "la": 10, "s": 10},
                {"id": "c", "text": "Fine — I've seen this before and markets recover", "rt": 20, "lc": 15, "la": -5, "s": 15},
                {"id": "d", "text": "Excited — time to buy more at lower prices", "rt": 30, "lc": 20, "la": -20, "s": 20},
            ],
        },
        # Q6: Knowledge Check (Sophistication)
        {
            "id": "q6_knowledge",
            "text": "How would you describe your investment knowledge?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Beginner — I know basics like stocks and savings", "rt": 0, "lc": 0, "la": 0, "s": -10},
                {"id": "b", "text": "Intermediate — I understand ETFs, diversification, compounding", "rt": 0, "lc": 5, "la": 0, "s": 15},
                {"id": "c", "text": "Advanced — I know tax strategies, options, alternative assets", "rt": 5, "lc": 10, "la": -5, "s": 30},
                {"id": "d", "text": "Expert — I could teach a course on this", "rt": 10, "lc": 15, "la": -10, "s": 40},
            ],
        },
        # Q7: Decision Style
        {
            "id": "q7_decision_style",
            "text": "When making a big financial decision, you typically:",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Ask trusted friends/family for advice", "rt": -5, "lc": -10, "la": 10, "s": 0},
                {"id": "b", "text": "Research extensively before acting", "rt": 10, "lc": 15, "la": 5, "s": 20},
                {"id": "c", "text": "Trust your gut and move quickly", "rt": 15, "lc": 25, "la": -10, "s": 10},
                {"id": "d", "text": "Wait for someone else to go first, then follow", "rt": -10, "lc": -15, "la": 15, "s": 0},
            ],
        },
        # Q8: Concentration Preference
        {
            "id": "q8_concentration",
            "text": "If you had $100,000 to invest, you'd prefer to:",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "Put it all in one high-conviction stock", "rt": 30, "lc": 30, "la": -15, "s": 10},
                {"id": "b", "text": "Split between 3-5 stocks you know well", "rt": 15, "lc": 20, "la": 0, "s": 15},
                {"id": "c", "text": "Buy a diversified index fund covering thousands of stocks", "rt": 10, "lc": 10, "la": 5, "s": 15},
                {"id": "d", "text": "Keep most in cash/bonds with a small stock allocation", "rt": -15, "lc": 5, "la": 20, "s": 10},
            ],
        },
        # Q9: News Reaction
        {
            "id": "q9_news_reaction",
            "text": "When you see scary financial news (recession warnings, market crash headlines):",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "text": "I immediately want to check my portfolio and maybe sell", "rt": -20, "lc": -10, "la": 25, "s": 0},
                {"id": "b", "text": "I feel anxious but remind myself to stay the course", "rt": 5, "lc": 10, "la": 10, "s": 10},
                {"id": "c", "text": "I ignore it — news is mostly noise", "rt": 15, "lc": 20, "la": -5, "s": 15},
                {"id": "d", "text": "I see it as a potential buying opportunity", "rt": 25, "lc": 25, "la": -15, "s": 20},
            ],
        },
        # Q10: Risk Tolerance (Slider)
        {
            "id": "q10_risk_slider",
            "text": "How much short-term loss could you stomach for potential long-term gains?",
            "subtext": "If your portfolio dropped by this amount tomorrow, at what point would you panic?",
            "question_type": "slider",
            "slider_min": 5,
            "slider_max": 50,
            "slider_labels": ["5%", "25%", "50%"],
            "dimension": "risk_tolerance",
            "weight": 2,  # Multiply slider value by this
        },
    ]
    return questions


# ══════════════════════════════════════════════════════════════════════════════
# SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class InvestorProfileService:
    """Core service for investor profiling and bias detection."""

    def __init__(self):
        self.questions = get_quiz_questions()

    def score_quiz(self, answers: List[Dict[str, Any]]) -> QuizDimensions:
        """
        Score quiz answers and return dimension scores.
        
        Args:
            answers: List of {question_id, answer_value, answer_index}
        
        Returns:
            QuizDimensions with scores 0-100 for each dimension
        """
        # Initialize raw scores (can go negative)
        raw_scores = {
            "risk_tolerance": 50,  # Start at neutral
            "locus_of_control": 50,
            "loss_aversion": 50,
            "sophistication": 50,
        }

        for answer in answers:
            q_id = answer.get("question_id")
            question = next((q for q in self.questions if q["id"] == q_id), None)
            if not question:
                continue

            if question["question_type"] == "slider":
                # Slider questions
                slider_value = float(answer.get("answer_value", 5))
                dimension = question.get("dimension", "risk_tolerance")
                weight = question.get("weight", 1)
                
                if dimension == "locus_of_control":
                    # 0-10 slider: 0 = external, 10 = internal
                    raw_scores["locus_of_control"] += (slider_value - 5) * 10
                elif dimension == "risk_tolerance":
                    # 5-50 slider: higher = more risk tolerant
                    raw_scores["risk_tolerance"] += (slider_value - 25) * weight
            else:
                # Multiple choice questions
                answer_id = answer.get("answer_value")
                option = next(
                    (o for o in question.get("options", []) if o["id"] == answer_id),
                    None
                )
                if option:
                    raw_scores["risk_tolerance"] += option.get("rt", 0)
                    raw_scores["locus_of_control"] += option.get("lc", 0)
                    raw_scores["loss_aversion"] += option.get("la", 0)
                    raw_scores["sophistication"] += option.get("s", 0)

        # Normalize to 0-100 range
        def normalize(score: float) -> float:
            # Scores typically range from -50 to 150, normalize to 0-100
            normalized = (score + 50) / 2
            return max(0, min(100, normalized))

        return QuizDimensions(
            risk_tolerance=normalize(raw_scores["risk_tolerance"]),
            locus_of_control=normalize(raw_scores["locus_of_control"]),
            loss_aversion=normalize(raw_scores["loss_aversion"]),
            sophistication=normalize(raw_scores["sophistication"]),
        )

    def get_profile(self, user_id: str) -> Optional[InvestorProfile]:
        """
        Look up a user's stored investor profile (quiz result).
        MVP: returns None when profiles are not persisted.
        In production, replace with DB lookup (e.g. InvestorProfile.objects.get(user_id=user_id)).
        Used by learn_drift_centroids to group users by archetype.
        """
        return None

    def determine_archetype(self, dimensions: QuizDimensions) -> InvestorArchetype:
        """
        Determine the investor archetype from dimension scores.
        
        Uses a decision tree based on primary behavioral signals.
        """
        rt = dimensions.risk_tolerance
        lc = dimensions.locus_of_control
        la = dimensions.loss_aversion
        s = dimensions.sophistication

        # High loss aversion + Low risk tolerance → Cautious Protector
        if la > 60 and rt < 45:
            return InvestorArchetype.CAUTIOUS_PROTECTOR

        # High risk + High locus of control + Low loss aversion → Opportunity Hunter
        if rt > 60 and lc > 55 and la < 50:
            return InvestorArchetype.OPPORTUNITY_HUNTER

        # High loss aversion + High activity (locus) → Reactive Trader
        if la > 55 and lc > 50 and rt < 55:
            return InvestorArchetype.REACTIVE_TRADER

        # Default: Steady Builder (moderate across dimensions)
        return InvestorArchetype.STEADY_BUILDER

    def create_profile(
        self,
        user_id: str,
        answers: List[Dict[str, Any]],
        total_assets: float = 0,
        has_options_activity: bool = False,
    ) -> InvestorProfile:
        """
        Create a complete investor profile from quiz answers.
        """
        # Score the quiz
        dimensions = self.score_quiz(answers)
        
        # Determine archetype
        archetype = self.determine_archetype(dimensions)
        
        # Get archetype metadata
        metadata = ARCHETYPE_METADATA[archetype]
        
        # Determine maturity stage
        maturity_stage = self._determine_maturity_stage(
            total_assets, has_options_activity
        )
        
        # Create profile
        profile = InvestorProfile(
            user_id=user_id,
            archetype=archetype,
            dimensions=dimensions,
            quiz_completed_at=datetime.utcnow(),
            maturity_stage=maturity_stage,
            coaching_tone=metadata["coaching_tone"],
            default_strategy=metadata["default_strategy"],
            archetype_title=metadata["title"],
            archetype_description=metadata["description"],
            archetype_focus=metadata["focus"],
        )
        
        return profile

    def _determine_maturity_stage(
        self,
        total_assets: float,
        has_options_activity: bool,
    ) -> UserMaturityStage:
        """Determine user maturity stage based on assets and activity."""
        if total_assets >= 500_000 or has_options_activity:
            return UserMaturityStage.ADVANCED
        elif total_assets >= 100_000:
            return UserMaturityStage.OPTIMIZER
        elif total_assets >= 5_000:
            return UserMaturityStage.BUILDER
        else:
            return UserMaturityStage.STARTER

    # ══════════════════════════════════════════════════════════════════════════
    # BIAS DETECTION
    # ══════════════════════════════════════════════════════════════════════════

    def detect_biases(
        self,
        profile: InvestorProfile,
        holdings: List[Dict[str, Any]],
        recent_trades: List[Dict[str, Any]],
        app_activity: Dict[str, Any],
    ) -> BiasMatrix:
        """
        Analyze user behavior to detect active biases.
        
        Args:
            profile: The user's investor profile
            holdings: List of {symbol, value, percent, sector, cost_basis, current_price}
            recent_trades: List of {symbol, action, amount, date, price_change_since_buy}
            app_activity: {opens_last_7_days, trades_last_30_days, panic_sells}
        
        Returns:
            BiasMatrix with detected biases
        """
        matrix = BiasMatrix()
        
        # 1. Concentration Bias
        concentration = self._calculate_concentration_bias(holdings)
        matrix.concentration_score = concentration["score"]
        if concentration["detected"]:
            matrix.active_biases.append(BiasScore(
                bias_type=BiasType.CONCENTRATION,
                score=concentration["score"],
                signal_description=concentration["signal"],
                coaching_message=self._get_bias_coaching(
                    BiasType.CONCENTRATION,
                    profile.coaching_tone,
                    concentration
                ),
            ))
        
        # 2. Recency Bias
        recency = self._calculate_recency_bias(recent_trades)
        matrix.recency_score = recency["score"]
        if recency["detected"]:
            matrix.active_biases.append(BiasScore(
                bias_type=BiasType.RECENCY,
                score=recency["score"],
                signal_description=recency["signal"],
                coaching_message=self._get_bias_coaching(
                    BiasType.RECENCY,
                    profile.coaching_tone,
                    recency
                ),
            ))
        
        # 3. Loss Aversion
        loss_aversion = self._calculate_loss_aversion(holdings, recent_trades)
        matrix.loss_aversion_score = loss_aversion["score"]
        if loss_aversion["detected"]:
            matrix.active_biases.append(BiasScore(
                bias_type=BiasType.LOSS_AVERSION,
                score=loss_aversion["score"],
                signal_description=loss_aversion["signal"],
                coaching_message=self._get_bias_coaching(
                    BiasType.LOSS_AVERSION,
                    profile.coaching_tone,
                    loss_aversion
                ),
            ))
        
        # 4. Familiarity Bias (heavy in known sectors)
        familiarity = self._calculate_familiarity_bias(holdings)
        matrix.familiarity_score = familiarity["score"]
        if familiarity["detected"]:
            matrix.active_biases.append(BiasScore(
                bias_type=BiasType.FAMILIARITY,
                score=familiarity["score"],
                signal_description=familiarity["signal"],
                coaching_message=self._get_bias_coaching(
                    BiasType.FAMILIARITY,
                    profile.coaching_tone,
                    familiarity
                ),
            ))
        
        # 5. Overconfidence (excessive trading)
        overconfidence = self._calculate_overconfidence(app_activity, recent_trades)
        matrix.overconfidence_score = overconfidence["score"]
        if overconfidence["detected"]:
            matrix.active_biases.append(BiasScore(
                bias_type=BiasType.OVERCONFIDENCE,
                score=overconfidence["score"],
                signal_description=overconfidence["signal"],
                coaching_message=self._get_bias_coaching(
                    BiasType.OVERCONFIDENCE,
                    profile.coaching_tone,
                    overconfidence
                ),
            ))
        
        # Calculate overall score
        matrix.calculate_overall()
        
        return matrix

    def _calculate_concentration_bias(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect concentration bias.
        
        Formula: (% of Portfolio in top 3 holdings) / 0.30 (target: <30%)
        """
        if not holdings:
            return {"score": 0, "detected": False, "signal": ""}
        
        # Sort by value and get top 3
        sorted_holdings = sorted(holdings, key=lambda h: h.get("value", 0), reverse=True)
        total_value = sum(h.get("value", 0) for h in holdings)
        
        if total_value == 0:
            return {"score": 0, "detected": False, "signal": ""}
        
        top_3_value = sum(h.get("value", 0) for h in sorted_holdings[:3])
        top_3_percent = (top_3_value / total_value) * 100
        
        # Also check sector concentration
        sector_totals = {}
        for h in holdings:
            sector = h.get("sector", "Unknown")
            sector_totals[sector] = sector_totals.get(sector, 0) + h.get("value", 0)
        
        max_sector_percent = max(
            (v / total_value) * 100 for v in sector_totals.values()
        ) if sector_totals else 0
        
        # Score calculation
        concentration_factor = min(100, (top_3_percent / 30) * 100)
        sector_factor = min(100, (max_sector_percent / 35) * 100)
        score = (concentration_factor + sector_factor) / 2
        
        detected = top_3_percent > 50 or max_sector_percent > 40
        
        top_holding = sorted_holdings[0]["symbol"] if sorted_holdings else "N/A"
        max_sector = max(sector_totals.keys(), key=lambda k: sector_totals[k]) if sector_totals else "N/A"
        
        return {
            "score": score,
            "detected": detected,
            "signal": f"Top 3 holdings = {top_3_percent:.0f}% of portfolio. {max_sector} sector = {max_sector_percent:.0f}%",
            "top_holding": top_holding,
            "top_3_percent": top_3_percent,
            "max_sector": max_sector,
            "max_sector_percent": max_sector_percent,
        }

    def _calculate_recency_bias(
        self,
        recent_trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect recency bias.
        
        Formula: (Net buys in assets up >20% in 60 days) / Total Net Buys
        """
        if not recent_trades:
            return {"score": 0, "detected": False, "signal": ""}
        
        buys = [t for t in recent_trades if t.get("action") == "buy"]
        if not buys:
            return {"score": 0, "detected": False, "signal": ""}
        
        # Buys in assets that were already up significantly
        chasing_buys = [
            t for t in buys
            if t.get("price_change_60d_before_buy", 0) > 20
        ]
        
        total_buy_value = sum(t.get("amount", 0) for t in buys)
        chasing_value = sum(t.get("amount", 0) for t in chasing_buys)
        
        if total_buy_value == 0:
            return {"score": 0, "detected": False, "signal": ""}
        
        recency_ratio = (chasing_value / total_buy_value) * 100
        score = min(100, recency_ratio * 1.5)  # Scale up
        detected = recency_ratio > 40
        
        return {
            "score": score,
            "detected": detected,
            "signal": f"{recency_ratio:.0f}% of recent buys were in assets already up >20%",
            "chasing_ratio": recency_ratio,
        }

    def _calculate_loss_aversion(
        self,
        holdings: List[Dict[str, Any]],
        recent_trades: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Detect loss aversion.
        
        Signal: Holding losers too long, selling winners too early.
        """
        # Count positions held at a loss for too long
        underwater_holds = [
            h for h in holdings
            if h.get("current_price", 0) < h.get("cost_basis", 0) * 0.80
            and h.get("days_held", 0) > 180
        ]
        
        # Count sells of winners at small gains
        early_winner_sells = [
            t for t in recent_trades
            if t.get("action") == "sell"
            and 0 < t.get("gain_percent", 0) < 10
        ]
        
        # Score based on these patterns
        loser_score = min(50, len(underwater_holds) * 15)
        early_sell_score = min(50, len(early_winner_sells) * 10)
        score = loser_score + early_sell_score
        
        detected = len(underwater_holds) > 0 or len(early_winner_sells) > 2
        
        signals = []
        if underwater_holds:
            signals.append(f"{len(underwater_holds)} positions held at >20% loss for 6+ months")
        if early_winner_sells:
            signals.append(f"{len(early_winner_sells)} winners sold at <10% gain")
        
        return {
            "score": score,
            "detected": detected,
            "signal": ". ".join(signals) if signals else "No loss aversion signals detected",
            "underwater_count": len(underwater_holds),
            "early_sell_count": len(early_winner_sells),
        }

    def _calculate_familiarity_bias(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect familiarity bias.
        
        Signal: Heavy concentration in well-known consumer/tech names.
        """
        # Common "household name" stocks people over-concentrate in
        familiar_names = {
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NFLX",
            "NVDA", "DIS", "SBUX", "NKE", "COST", "WMT", "TGT", "HD",
        }
        
        total_value = sum(h.get("value", 0) for h in holdings)
        if total_value == 0:
            return {"score": 0, "detected": False, "signal": ""}
        
        familiar_value = sum(
            h.get("value", 0) for h in holdings
            if h.get("symbol", "").upper() in familiar_names
        )
        
        familiar_percent = (familiar_value / total_value) * 100
        score = min(100, familiar_percent * 1.5)
        detected = familiar_percent > 50
        
        return {
            "score": score,
            "detected": detected,
            "signal": f"{familiar_percent:.0f}% of portfolio in well-known consumer/tech names",
            "familiar_percent": familiar_percent,
        }

    def _calculate_overconfidence(
        self,
        app_activity: Dict[str, Any],
        recent_trades: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Detect overconfidence bias.
        
        Signal: Excessive trading, frequent portfolio checks.
        """
        opens_7d = app_activity.get("opens_last_7_days", 0)
        trades_30d = len(recent_trades)
        
        # Excessive checking (>5x/day = 35/week)
        checking_score = min(50, (opens_7d / 35) * 50)
        
        # Excessive trading (>10 trades/month is high for retail)
        trading_score = min(50, (trades_30d / 10) * 50)
        
        score = checking_score + trading_score
        detected = opens_7d > 21 or trades_30d > 8  # 3x/day or 8+ trades/month
        
        return {
            "score": score,
            "detected": detected,
            "signal": f"{opens_7d} app opens in 7 days, {trades_30d} trades in 30 days",
            "opens_7d": opens_7d,
            "trades_30d": trades_30d,
        }

    def _get_bias_coaching(
        self,
        bias_type: BiasType,
        tone: CoachingTone,
        bias_data: Dict[str, Any],
    ) -> str:
        """Generate personalized coaching message for a detected bias."""
        
        messages = {
            BiasType.CONCENTRATION: {
                CoachingTone.THE_GUARDIAN: (
                    f"Your 'Home Team' ({bias_data.get('max_sector', 'tech')}) is strong, "
                    "but your defense is thin. Adding a Total Market ETF brings your "
                    "concentration down to a safer level without giving up growth potential."
                ),
                CoachingTone.THE_ARCHITECT: (
                    f"Concentration at {bias_data.get('top_3_percent', 0):.0f}% introduces "
                    "single-point-of-failure risk. The Simple Path suggests broad diversification — "
                    "a small shift to VTI would optimize your system's resilience."
                ),
                CoachingTone.THE_SCOUT: (
                    f"You're betting big on {bias_data.get('max_sector', 'your top sector')}. "
                    "That's a bold play, but even scouts need a base camp. Consider balancing "
                    "with international or small-cap exposure for asymmetric upside elsewhere."
                ),
                CoachingTone.THE_STABILIZER: (
                    "Having most of your money in a few names can feel comforting, but it "
                    "amplifies both gains AND losses. A more balanced allocation helps you "
                    "sleep better when headlines get scary."
                ),
            },
            BiasType.RECENCY: {
                CoachingTone.THE_GUARDIAN: (
                    "I notice you've been buying things that recently went up. "
                    "That's natural, but 'buying high' can hurt long-term returns. "
                    "Your fortress grows faster when you buy consistency, not momentum."
                ),
                CoachingTone.THE_ARCHITECT: (
                    f"{bias_data.get('chasing_ratio', 0):.0f}% of your recent buys were in assets "
                    "already up >20%. The math favors dollar-cost averaging into broad indices "
                    "over chasing recent winners."
                ),
                CoachingTone.THE_SCOUT: (
                    "You're chasing what's hot. Sometimes that works, but history shows "
                    "today's winners often become tomorrow's laggards. True alpha comes from "
                    "finding the NEXT winner, not piling into the current one."
                ),
                CoachingTone.THE_STABILIZER: (
                    "It feels safe to buy what's going up, but that's recency bias talking. "
                    "Your long-term plan doesn't need to chase trends — it just needs time."
                ),
            },
            BiasType.LOSS_AVERSION: {
                CoachingTone.THE_GUARDIAN: (
                    "I see some positions you've held through significant losses. "
                    "That takes courage, but sometimes protecting your fortress means "
                    "letting go of what isn't working to redeploy elsewhere."
                ),
                CoachingTone.THE_ARCHITECT: (
                    "Loss aversion may be keeping capital trapped in underperformers. "
                    "The 'sunk cost' is already spent — the question is where that money "
                    "works hardest going forward."
                ),
                CoachingTone.THE_SCOUT: (
                    "Holding losers too long and selling winners too early is the opposite "
                    "of what works. Consider: would you buy these positions today at current prices?"
                ),
                CoachingTone.THE_STABILIZER: (
                    "I know it's hard to sell at a loss — it feels like admitting defeat. "
                    "But sometimes the healthiest move is redirecting that energy to something "
                    "with better odds."
                ),
            },
            BiasType.FAMILIARITY: {
                CoachingTone.THE_GUARDIAN: (
                    "It's natural to invest in companies you know. But your portfolio "
                    "is heavily weighted toward familiar names. A broader ETF adds protection "
                    "without requiring you to research thousands of companies."
                ),
                CoachingTone.THE_ARCHITECT: (
                    f"{bias_data.get('familiar_percent', 0):.0f}% of your portfolio is in "
                    "household-name stocks. The Simple Path works because it owns EVERYTHING — "
                    "consider VTI to capture the growth you're not seeing."
                ),
                CoachingTone.THE_SCOUT: (
                    "You're overweight in names everyone knows. That's where the crowds are. "
                    "Real opportunity often lives in places most people aren't looking."
                ),
                CoachingTone.THE_STABILIZER: (
                    "Familiar names feel safe, but they can all move together. "
                    "Adding some international or small-cap exposure smooths out the ride."
                ),
            },
            BiasType.OVERCONFIDENCE: {
                CoachingTone.THE_GUARDIAN: (
                    "I've noticed increased activity — more checking, more trading. "
                    "Remember: the fortress builds itself over time. Less activity often "
                    "means better outcomes."
                ),
                CoachingTone.THE_ARCHITECT: (
                    f"{bias_data.get('trades_30d', 0)} trades this month suggests high activity. "
                    "Research shows most retail traders underperform passive investors. "
                    "The system works best when you let it run."
                ),
                CoachingTone.THE_SCOUT: (
                    "Active trading can feel productive, but transaction costs and taxes "
                    "erode returns. Even scouts need patience — the best opportunities "
                    "don't require constant repositioning."
                ),
                CoachingTone.THE_STABILIZER: (
                    "Checking your portfolio frequently can increase anxiety and lead to "
                    "impulsive decisions. Try setting specific 'check-in' times instead of "
                    "reacting to every notification."
                ),
            },
        }
        
        return messages.get(bias_type, {}).get(
            tone,
            "Consider reviewing this aspect of your portfolio strategy."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # AI PROMPT GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def get_coaching_system_prompt(
        self,
        profile: InvestorProfile,
        context: Optional[str] = None,
    ) -> str:
        """
        Generate the system prompt for AI coaching based on user's archetype.
        """
        base_prompt = """You are the RichesReach Behavioral Coach. Your goal is to guide the user toward long-term wealth using the principles of 'The Simple Path to Wealth' and Pompian's Behavioral Finance.

CORE PRINCIPLES:
- Always acknowledge psychological wins
- Use 'Wealth Redirect' language rather than 'Budgeting' language
- Frame actions as 'Building a Fortress' or 'Accelerating the Millionaire Path'
- Never give direct financial advice — focus on education and coaching
- Quantify the future value of today's decisions when possible

USER CONTEXT:
- Archetype: {archetype}
- Maturity Stage: {maturity_stage}
- Risk Tolerance: {risk_tolerance:.0f}/100
- Investment Sophistication: {sophistication:.0f}/100
"""

        tone_prompt = COACHING_PROMPTS.get(profile.coaching_tone, {}).get(
            "system_prompt", ""
        )

        # Build the full prompt
        prompt = base_prompt.format(
            archetype=profile.archetype_title,
            maturity_stage=profile.maturity_stage.value,
            risk_tolerance=profile.dimensions.risk_tolerance,
            sophistication=profile.dimensions.sophistication,
        )
        
        prompt += f"\n\nTONE GUIDANCE:\n{tone_prompt}"
        
        if context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{context}"
        
        # Add bias awareness if any active
        if profile.bias_matrix.active_biases:
            bias_summary = ", ".join(
                b.bias_type.value for b in profile.bias_matrix.active_biases
            )
            prompt += f"\n\nACTIVE BIASES DETECTED: {bias_summary}"
            prompt += "\nGently address these biases when relevant, without being preachy."
        
        return prompt


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ══════════════════════════════════════════════════════════════════════════════

investor_profile_service = InvestorProfileService()
