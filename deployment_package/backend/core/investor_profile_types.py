"""
Investor Profile Types
======================
Type definitions for the Behavioral Identity System.
Based on Pompian's Behavioral Finance framework.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class InvestorArchetype(Enum):
    """The four behavioral investor archetypes."""
    CAUTIOUS_PROTECTOR = "cautious_protector"
    STEADY_BUILDER = "steady_builder"
    OPPORTUNITY_HUNTER = "opportunity_hunter"
    REACTIVE_TRADER = "reactive_trader"


class BiasType(Enum):
    """Behavioral biases that can be detected."""
    CONCENTRATION = "concentration"
    RECENCY = "recency"
    LOSS_AVERSION = "loss_aversion"
    FAMILIARITY = "familiarity"
    OVERCONFIDENCE = "overconfidence"
    HERD_BEHAVIOR = "herd_behavior"
    INERTIA = "inertia"


class CoachingTone(Enum):
    """AI coaching personas based on archetype."""
    THE_GUARDIAN = "the_guardian"      # For Cautious Protector
    THE_ARCHITECT = "the_architect"    # For Steady Builder
    THE_SCOUT = "the_scout"            # For Opportunity Hunter
    THE_STABILIZER = "the_stabilizer"  # For Reactive Trader


class UserMaturityStage(Enum):
    """User segmentation by financial maturity."""
    STARTER = "starter"        # < $5k assets
    BUILDER = "builder"        # > $5k + steady income
    OPTIMIZER = "optimizer"    # > $100k + diversified
    ADVANCED = "advanced"      # > $500k or options user


class DefaultStrategy(Enum):
    """Investment strategy buckets."""
    SIMPLE_PATH_CORE = "simple_path_core"      # Broad Market ETFs (VTI, VOO)
    INCOME_STABILITY = "income_stability"       # Dividend ETFs, Treasuries
    GROWTH_INNOVATION = "growth_innovation"     # Sector/Innovation ETFs
    HIGH_CONVICTION = "high_conviction"         # Individual stocks, thematic


@dataclass
class QuizAnswer:
    """A single quiz answer."""
    question_id: str
    answer_value: str  # A, B, C, D or numeric
    answer_index: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuizDimensions:
    """The four dimensions measured by the quiz."""
    risk_tolerance: float       # 0-100: Financial ability to handle volatility
    locus_of_control: float     # 0-100: Internal (high) vs External (low)
    loss_aversion: float        # 0-100: Emotional pain of losing money
    sophistication: float       # 0-100: Technical knowledge level

    def to_dict(self) -> Dict[str, float]:
        return {
            "risk_tolerance": self.risk_tolerance,
            "locus_of_control": self.locus_of_control,
            "loss_aversion": self.loss_aversion,
            "sophistication": self.sophistication,
        }


@dataclass
class BiasScore:
    """A detected behavioral bias with severity."""
    bias_type: BiasType
    score: float              # 0-100 severity
    signal_description: str   # What triggered this detection
    coaching_message: str     # Personalized coaching text
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bias_type": self.bias_type.value,
            "score": self.score,
            "signal_description": self.signal_description,
            "coaching_message": self.coaching_message,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class BiasMatrix:
    """The complete behavioral bias profile."""
    concentration_score: float = 0.0
    recency_score: float = 0.0
    loss_aversion_score: float = 0.0
    familiarity_score: float = 0.0
    overconfidence_score: float = 0.0
    
    # Composite score: weighted average
    overall_bias_score: float = 0.0
    
    # Detected bias flags
    active_biases: List[BiasScore] = field(default_factory=list)

    def calculate_overall(self) -> float:
        """Calculate the composite bias score using the Pompian formula."""
        self.overall_bias_score = (
            (self.concentration_score * 0.4) +
            (self.recency_score * 0.3) +
            (self.loss_aversion_score * 0.3)
        )
        return self.overall_bias_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concentration_score": self.concentration_score,
            "recency_score": self.recency_score,
            "loss_aversion_score": self.loss_aversion_score,
            "familiarity_score": self.familiarity_score,
            "overconfidence_score": self.overconfidence_score,
            "overall_bias_score": self.overall_bias_score,
            "active_biases": [b.to_dict() for b in self.active_biases],
        }


@dataclass
class InvestorProfile:
    """The complete investor identity profile."""
    user_id: str
    
    # Quiz results
    archetype: InvestorArchetype
    dimensions: QuizDimensions
    quiz_completed_at: Optional[datetime] = None
    
    # Derived attributes
    maturity_stage: UserMaturityStage = UserMaturityStage.STARTER
    coaching_tone: CoachingTone = CoachingTone.THE_ARCHITECT
    default_strategy: DefaultStrategy = DefaultStrategy.SIMPLE_PATH_CORE
    
    # Behavioral analysis
    bias_matrix: BiasMatrix = field(default_factory=BiasMatrix)
    
    # Archetype description
    archetype_title: str = ""
    archetype_description: str = ""
    archetype_focus: str = ""
    
    # Activity tracking for bias detection
    app_opens_last_7_days: int = 0
    trades_last_30_days: int = 0
    panic_sell_count: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "archetype": self.archetype.value,
            "archetype_title": self.archetype_title,
            "archetype_description": self.archetype_description,
            "archetype_focus": self.archetype_focus,
            "dimensions": self.dimensions.to_dict(),
            "maturity_stage": self.maturity_stage.value,
            "coaching_tone": self.coaching_tone.value,
            "default_strategy": self.default_strategy.value,
            "bias_matrix": self.bias_matrix.to_dict(),
            "quiz_completed_at": self.quiz_completed_at.isoformat() if self.quiz_completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Quiz Question Definitions ─────────────────────────────────────────────────

@dataclass
class QuizOption:
    """A single answer option for a quiz question."""
    id: str
    text: str
    # Weights for each dimension (can be negative)
    risk_tolerance_weight: float = 0.0
    locus_of_control_weight: float = 0.0
    loss_aversion_weight: float = 0.0
    sophistication_weight: float = 0.0


@dataclass
class QuizQuestion:
    """A behavioral quiz question."""
    id: str
    text: str
    subtext: Optional[str] = None
    question_type: str = "single_choice"  # single_choice, slider, multi_choice
    options: List[QuizOption] = field(default_factory=list)
    slider_min: int = 0
    slider_max: int = 10
    slider_labels: Optional[List[str]] = None


# ── Archetype Metadata ────────────────────────────────────────────────────────

ARCHETYPE_METADATA = {
    InvestorArchetype.CAUTIOUS_PROTECTOR: {
        "title": "The Cautious Protector",
        "description": "You prioritize security and steady progress over aggressive growth. "
                       "Your investing style focuses on protecting what you have while building wealth slowly.",
        "focus": "Security, risk mitigation, and 'hidden' wins",
        "coaching_tone": CoachingTone.THE_GUARDIAN,
        "default_strategy": DefaultStrategy.INCOME_STABILITY,
        "typical_allocation": "60/40 Stocks-Bonds or Dividend focus",
    },
    InvestorArchetype.STEADY_BUILDER: {
        "title": "The Steady Builder",
        "description": "You believe in systems and automation. You trust the power of compounding "
                       "and prefer a disciplined, low-maintenance approach to wealth building.",
        "focus": "Efficiency, systems, and the 'Math of Time'",
        "coaching_tone": CoachingTone.THE_ARCHITECT,
        "default_strategy": DefaultStrategy.SIMPLE_PATH_CORE,
        "typical_allocation": "Total Market Index Funds (The Simple Path)",
    },
    InvestorArchetype.OPPORTUNITY_HUNTER: {
        "title": "The Opportunity Hunter",
        "description": "You're energized by finding the next big opportunity. You're comfortable "
                       "with higher risk for potentially higher rewards and enjoy being active.",
        "focus": "Growth, edge, and strategic positioning",
        "coaching_tone": CoachingTone.THE_SCOUT,
        "default_strategy": DefaultStrategy.GROWTH_INNOVATION,
        "typical_allocation": "Satellite Core (Index + 20% Growth/Sector ETFs)",
    },
    InvestorArchetype.REACTIVE_TRADER: {
        "title": "The Reactive Trader",
        "description": "You're emotionally connected to your investments. Market movements affect you "
                       "deeply, and you benefit from guardrails that prevent impulsive decisions.",
        "focus": "Stability through structure and automation",
        "coaching_tone": CoachingTone.THE_STABILIZER,
        "default_strategy": DefaultStrategy.SIMPLE_PATH_CORE,
        "typical_allocation": "High-automation, low-visibility 'lockbox' funds",
    },
}


# ── Coaching Tone Prompts ─────────────────────────────────────────────────────

COACHING_PROMPTS = {
    CoachingTone.THE_GUARDIAN: {
        "system_prompt": """You are The Guardian, a protective wealth coach for RichesReach.
Speak with empathy about market volatility. Emphasize how saving money creates a safety net.
Use phrases like 'Protecting your downside', 'Guaranteed wins', and 'Strengthening your fortress'.
Focus on security, risk mitigation, and celebrating small wins. Never push aggressive strategies.""",
        "example_tone": "By moving this to a High-Yield account, we're strengthening your financial fortress without touching your daily budget.",
    },
    CoachingTone.THE_ARCHITECT: {
        "system_prompt": """You are The Architect, a systematic wealth strategist for RichesReach.
Speak with logic and precision. Focus on compounding and automation.
Use phrases like 'Optimizing the system', 'Time-in-market vs timing-the-market', and 'High-leverage move'.
Frame everything as building an efficient wealth machine. Trust the math.""",
        "example_tone": "Redirecting this into VTI increases your system's efficiency. Over 20 years, this one change adds $18k to your terminal wealth.",
    },
    CoachingTone.THE_SCOUT: {
        "system_prompt": """You are The Scout, a forward-looking growth strategist for RichesReach.
Speak with energy and vision. Focus on 'alpha' and sector exposure.
Use phrases like 'Capturing growth', 'Strategic allocation', and 'Positioning for the future'.
Help the user find opportunities while maintaining a stable core.""",
        "example_tone": "Based on your interest in tech growth, we can allocate this to your 'Satellite' fund to increase innovation exposure without risking your core.",
    },
    CoachingTone.THE_STABILIZER: {
        "system_prompt": """You are The Stabilizer, a calming wealth coach for RichesReach.
Your user tends to be emotionally reactive to market movements. Speak with calm reassurance.
Use phrases like 'Staying the course', 'Your long-term plan is working', and 'Market noise vs signal'.
Help them avoid impulsive decisions by reminding them of their past goals.""",
        "example_tone": "Your quiz profile said you're building for the long term. This dip is noise, not signal. Want to see your 20-year projection again?",
    },
}
