"""
Investor Profile GraphQL Queries & Types
=========================================
GraphQL interface for the Behavioral Identity System.
"""

import graphene
from graphene import ObjectType, String, Float, Int, Boolean, List, Field, Enum
from typing import Any, Dict

from .investor_profile_service import investor_profile_service
from .investor_profile_types import (
    InvestorArchetype as ArchetypeEnum,
    CoachingTone as ToneEnum,
    UserMaturityStage as StageEnum,
    BiasType as BiasTypeEnum,
    DefaultStrategy as StrategyEnum,
)
from .next_best_action_service import (
    next_best_action_service,
    UserFinancialState,
    ActionPriority,
    ActionType,
)
from .behavioral_ranking_service import reorder as behavioral_reorder
from . import behavioral_events as behavioral_events_module
from .behavioral_consistency_service import get_consistency_result
from .behavioral_bias_signal import get_behavioral_bias_signal
from .ranking_config import get_shadow_mode, get_ml_traffic_fraction, should_serve_ml_order
from .tone_optimization_service import get_tone_variants_for_recs


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHQL ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class InvestorArchetypeEnum(Enum):
    """The four behavioral investor archetypes."""
    CAUTIOUS_PROTECTOR = "cautious_protector"
    STEADY_BUILDER = "steady_builder"
    OPPORTUNITY_HUNTER = "opportunity_hunter"
    REACTIVE_TRADER = "reactive_trader"


class CoachingToneEnum(Enum):
    """AI coaching personas."""
    THE_GUARDIAN = "the_guardian"
    THE_ARCHITECT = "the_architect"
    THE_SCOUT = "the_scout"
    THE_STABILIZER = "the_stabilizer"


class UserMaturityStageEnum(Enum):
    """User segmentation by financial maturity."""
    STARTER = "starter"
    BUILDER = "builder"
    OPTIMIZER = "optimizer"
    ADVANCED = "advanced"


class BiasTypeEnumGQL(Enum):
    """Behavioral biases."""
    CONCENTRATION = "concentration"
    RECENCY = "recency"
    LOSS_AVERSION = "loss_aversion"
    FAMILIARITY = "familiarity"
    OVERCONFIDENCE = "overconfidence"


class ActionPriorityEnum(Enum):
    """NBA priority levels."""
    CRITICAL = 1
    SAFETY_NET = 2
    DEBT_REDUCTION = 3
    FOUNDATION = 4
    GROWTH = 5
    OPTIMIZATION = 6
    ADVANCED = 7


class ActionTypeEnum(Enum):
    """Types of suggested actions."""
    CANCEL_LEAK = "cancel_leak"
    BUILD_EMERGENCY_FUND = "build_emergency_fund"
    PAY_DEBT = "pay_debt"
    CAPTURE_MATCH = "capture_match"
    START_INVESTING = "start_investing"
    INCREASE_CONTRIBUTION = "increase_contribution"
    REBALANCE = "rebalance"
    REDUCE_CONCENTRATION = "reduce_concentration"
    TAX_LOSS_HARVEST = "tax_loss_harvest"
    REDUCE_FEES = "reduce_fees"
    REDIRECT_SAVINGS = "redirect_savings"


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHQL TYPES
# ══════════════════════════════════════════════════════════════════════════════

class QuizOptionType(ObjectType):
    """A quiz answer option."""
    id = String(required=True)
    text = String(required=True)


class QuizQuestionType(ObjectType):
    """A behavioral quiz question."""
    id = String(required=True)
    text = String(required=True)
    subtext = String()
    question_type = String(required=True)  # single_choice, slider
    options = List(QuizOptionType)
    slider_min = Int()
    slider_max = Int()
    slider_labels = List(String)


class QuizDimensionsType(ObjectType):
    """Scored dimensions from the quiz."""
    risk_tolerance = Float(required=True)
    locus_of_control = Float(required=True)
    loss_aversion = Float(required=True)
    sophistication = Float(required=True)


class BiasScoreType(ObjectType):
    """A detected behavioral bias."""
    bias_type = String(required=True)
    score = Float(required=True)
    signal_description = String(required=True)
    coaching_message = String(required=True)


class BiasMatrixType(ObjectType):
    """Complete behavioral bias profile."""
    concentration_score = Float(required=True)
    recency_score = Float(required=True)
    loss_aversion_score = Float(required=True)
    familiarity_score = Float(required=True)
    overconfidence_score = Float(required=True)
    overall_bias_score = Float(required=True)
    active_biases = List(BiasScoreType)


class InvestorProfileType(ObjectType):
    """Complete investor profile."""
    user_id = String(required=True)
    
    # Archetype
    archetype = String(required=True)
    archetype_title = String(required=True)
    archetype_description = String(required=True)
    archetype_focus = String(required=True)
    
    # Dimensions
    dimensions = Field(QuizDimensionsType)
    
    # Derived attributes
    maturity_stage = String(required=True)
    coaching_tone = String(required=True)
    default_strategy = String(required=True)
    
    # Bias analysis
    bias_matrix = Field(BiasMatrixType)
    
    # Status
    quiz_completed = Boolean(required=True)


class NextBestActionType(ObjectType):
    """A recommended action for the user."""
    id = String(required=True)
    action_type = String(required=True)
    priority = Int(required=True)
    priority_score = Float(required=True)

    headline = String(required=True)
    description = String(required=True)
    impact_text = String(required=True)

    monthly_amount = Float()
    total_impact = Float()
    time_impact_days = Int()

    action_label = String(required=True)
    action_screen = String()
    reasoning = String()

    # Phase 1 Messenger: which tone variant the backend selected for this rec.
    # Values: "default" | "direct" | "encouraging" | "minimal"
    tone_variant = String()


class LeakRedirectSuggestionType(ObjectType):
    """Suggestion for where to redirect savings from a canceled leak."""
    action_type = String(required=True)
    headline = String(required=True)
    description = String(required=True)
    impact_text = String(required=True)
    monthly_amount = Float(required=True)
    total_impact = Float()
    time_impact_days = Int()
    suggested_etf = String()
    action_screen = String(required=True)
    reasoning = String(required=True)


class DriftSignalType(ObjectType):
    """Phase 2: Archetype drift signal (non-accusatory)."""
    suggested_archetype = String(required=True)
    confidence_match = Float(required=True)
    message_key = String(required=True)
    show_nudge = Boolean(required=True)


class BehavioralConsistencyType(ObjectType):
    """Phase 2: Consistency score and optional drift."""
    consistency_score = Float(required=True)
    drift = Field(DriftSignalType)


class BehavioralBiasSignalType(ObjectType):
    """Phase 3: Bias-from-behavior signal (feeds into rule-based bias; rules own final flag)."""
    suggested_bias_types = List(String, required=True)
    confidence = Float(required=True)
    show_in_ui = Boolean(required=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHQL INPUT TYPES
# ══════════════════════════════════════════════════════════════════════════════

class QuizAnswerInput(graphene.InputObjectType):
    """Input for a single quiz answer."""
    question_id = String(required=True)
    answer_value = String(required=True)
    answer_index = Int()


class FinancialStateInput(graphene.InputObjectType):
    """Input for user's financial state (for NBA calculations)."""
    total_assets = Float()
    liquid_cash = Float()
    invested_assets = Float()
    monthly_income = Float()
    monthly_expenses = Float()
    monthly_savings = Float()
    total_debt = Float()
    high_interest_debt = Float()
    highest_debt_apr = Float()
    emergency_fund_months = Float()
    has_401k_match = Boolean()
    match_percent = Float()
    current_401k_contribution_percent = Float()
    annual_match_left_on_table = Float()
    total_monthly_leaks = Float()
    leak_count = Int()
    portfolio_concentration_score = Float()
    portfolio_fee_drag = Float()


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHQL QUERIES
# ══════════════════════════════════════════════════════════════════════════════

class InvestorProfileQueries(ObjectType):
    """Queries for the Investor Profile system."""
    
    # Get quiz questions
    investor_quiz_questions = List(
        QuizQuestionType,
        description="Get the 10-question Behavioral Identity Quiz"
    )
    
    # Get user's profile
    investor_profile = Field(
        InvestorProfileType,
        user_id=String(required=True),
        description="Get a user's investor profile"
    )
    
    # Get next best actions
    next_best_actions = List(
        NextBestActionType,
        user_id=String(required=True),
        max_actions=Int(default_value=3),
        description="Get prioritized action recommendations"
    )
    
    # Get leak redirect suggestion
    leak_redirect_suggestion = Field(
        LeakRedirectSuggestionType,
        user_id=String(required=True),
        leak_amount=Float(required=True),
        description="Get suggestion for where to redirect savings from a canceled leak"
    )
    
    # Phase 2: Behavioral consistency + drift
    behavioral_consistency = Field(
        BehavioralConsistencyType,
        user_id=String(required=True),
        description="Consistency score (quiz vs behavior) and optional drift signal"
    )
    
    # Phase 3: Bias-from-behavior (input to rule-based bias; rules own final flag)
    behavioral_bias_signal = Field(
        BehavioralBiasSignalType,
        user_id=String(required=True),
        description="Suggested bias types from engagement; for display and future rule input"
    )
    
    def resolve_investor_quiz_questions(self, info):
        """Return the quiz questions."""
        questions = investor_profile_service.questions
        result = []
        
        for q in questions:
            options = []
            for opt in q.get("options", []):
                options.append(QuizOptionType(
                    id=opt["id"],
                    text=opt["text"],
                ))
            
            result.append(QuizQuestionType(
                id=q["id"],
                text=q["text"],
                subtext=q.get("subtext"),
                question_type=q["question_type"],
                options=options if options else None,
                slider_min=q.get("slider_min"),
                slider_max=q.get("slider_max"),
                slider_labels=q.get("slider_labels"),
            ))
        
        return result
    
    def resolve_investor_profile(self, info, user_id: str):
        """Get or create a user's investor profile."""
        # In production, this would load from database
        # For now, return a demo profile
        from .investor_profile_types import QuizDimensions, BiasMatrix
        
        # Demo profile for development
        dimensions = QuizDimensions(
            risk_tolerance=65,
            locus_of_control=70,
            loss_aversion=40,
            sophistication=55,
        )
        
        archetype = investor_profile_service.determine_archetype(dimensions)
        from .investor_profile_types import ARCHETYPE_METADATA
        metadata = ARCHETYPE_METADATA[archetype]
        
        bias_matrix = BiasMatrix(
            concentration_score=45,
            recency_score=30,
            loss_aversion_score=25,
            familiarity_score=55,
            overconfidence_score=20,
            overall_bias_score=35,
            active_biases=[],
        )
        
        return InvestorProfileType(
            user_id=user_id,
            archetype=archetype.value,
            archetype_title=metadata["title"],
            archetype_description=metadata["description"],
            archetype_focus=metadata["focus"],
            dimensions=QuizDimensionsType(
                risk_tolerance=dimensions.risk_tolerance,
                locus_of_control=dimensions.locus_of_control,
                loss_aversion=dimensions.loss_aversion,
                sophistication=dimensions.sophistication,
            ),
            maturity_stage="builder",
            coaching_tone=metadata["coaching_tone"].value,
            default_strategy=metadata["default_strategy"].value,
            bias_matrix=BiasMatrixType(
                concentration_score=bias_matrix.concentration_score,
                recency_score=bias_matrix.recency_score,
                loss_aversion_score=bias_matrix.loss_aversion_score,
                familiarity_score=bias_matrix.familiarity_score,
                overconfidence_score=bias_matrix.overconfidence_score,
                overall_bias_score=bias_matrix.overall_bias_score,
                active_biases=[],
            ),
            quiz_completed=True,
        )
    
    def resolve_next_best_actions(self, info, user_id: str, max_actions: int = 3):
        """Get prioritized action recommendations."""
        # In production, this would load real user data
        # For demo, use sample financial state
        
        # First get the user's profile
        from .investor_profile_types import (
            InvestorProfile, QuizDimensions, BiasMatrix,
            InvestorArchetype as ArchEnum, CoachingTone, DefaultStrategy,
            UserMaturityStage
        )
        
        dimensions = QuizDimensions(
            risk_tolerance=65,
            locus_of_control=70,
            loss_aversion=40,
            sophistication=55,
        )
        
        archetype = investor_profile_service.determine_archetype(dimensions)
        metadata = ARCHETYPE_METADATA[archetype]
        
        profile = InvestorProfile(
            user_id=user_id,
            archetype=archetype,
            dimensions=dimensions,
            coaching_tone=metadata["coaching_tone"],
            default_strategy=metadata["default_strategy"],
        )
        
        # Demo financial state
        state = UserFinancialState(
            total_assets=45000,
            liquid_cash=8000,
            invested_assets=35000,
            monthly_income=6500,
            monthly_expenses=4200,
            monthly_savings=1800,
            total_debt=3500,
            high_interest_debt=2000,
            highest_debt_apr=19.9,
            emergency_fund_months=1.9,
            has_401k_match=True,
            match_percent=4.0,
            current_401k_contribution_percent=2.0,
            annual_match_left_on_table=1300,
            total_monthly_leaks=127,
            leak_count=4,
            portfolio_concentration_score=55,
            portfolio_fee_drag=0.35,
        )
        
        actions = next_best_action_service.get_next_best_actions(
            profile, state, max_actions
        )
        ranked = behavioral_reorder(
            actions, user_id, profile.archetype.value,
            segment=profile.archetype.value,
        )
        rule_ids = [a.id for a in actions]
        ml_ids = [a.id for a in ranked]
        rec_types = [a.action_type.value for a in actions]
        rec_types_ml = [a.action_type.value for a in ranked]
        variants_rule = get_tone_variants_for_recs(user_id, rule_ids, rec_types)
        variants_ml = get_tone_variants_for_recs(user_id, ml_ids, rec_types_ml)

        shadow_mode = get_shadow_mode()
        ml_frac = get_ml_traffic_fraction()

        if shadow_mode:
            behavioral_events_module.log_impression_with_shadow(
                user_id, rule_ids, ml_ids, rec_types=rec_types, variants=variants_rule
            )
            to_return = actions
            serving_variants = dict(zip(rule_ids, variants_rule))
        elif ml_frac >= 1.0:
            behavioral_events_module.log_impression(
                user_id, ml_ids, rec_types=rec_types_ml, variants=variants_ml
            )
            to_return = ranked
            serving_variants = dict(zip(ml_ids, variants_ml))
        elif ml_frac > 0:
            behavioral_events_module.log_impression_with_shadow(
                user_id, rule_ids, ml_ids, rec_types=rec_types, variants=variants_rule
            )
            to_return = ranked if should_serve_ml_order(user_id) else actions
            serving_variants = dict(zip(ml_ids, variants_ml)) if to_return is ranked else dict(zip(rule_ids, variants_rule))
        else:
            behavioral_events_module.log_impression_with_shadow(
                user_id, rule_ids, ml_ids, rec_types=rec_types, variants=variants_rule
            )
            to_return = actions
            serving_variants = dict(zip(rule_ids, variants_rule))

        return [
            NextBestActionType(
                id=a.id,
                action_type=a.action_type.value,
                priority=a.priority.value,
                priority_score=a.priority_score,
                headline=a.headline,
                description=a.description,
                impact_text=a.impact_text,
                monthly_amount=a.monthly_amount,
                total_impact=a.total_impact,
                time_impact_days=a.time_impact_days,
                action_label=a.action_label,
                action_screen=a.action_screen,
                reasoning=a.reasoning,
                tone_variant=serving_variants.get(a.id, "default"),
            )
            for a in to_return
        ]
    
    def resolve_behavioral_consistency(self, info, user_id: str):
        """Phase 2: Consistency score and optional drift signal."""
        from .investor_profile_types import QuizDimensions, ARCHETYPE_METADATA
        dimensions = QuizDimensions(
            risk_tolerance=65,
            locus_of_control=70,
            loss_aversion=40,
            sophistication=55,
        )
        archetype = investor_profile_service.determine_archetype(dimensions)
        result = get_consistency_result(user_id, archetype.value)
        drift_type = None
        if result.drift:
            d = result.drift
            drift_type = DriftSignalType(
                suggested_archetype=d.suggested_archetype,
                confidence_match=d.confidence_match,
                message_key=d.message_key,
                show_nudge=d.show_nudge,
            )
        return BehavioralConsistencyType(
            consistency_score=result.consistency_score,
            drift=drift_type,
        )

    def resolve_behavioral_bias_signal(self, info, user_id: str):
        """Phase 3: Bias-from-behavior signal."""
        result = get_behavioral_bias_signal(user_id)
        return BehavioralBiasSignalType(
            suggested_bias_types=result.suggested_bias_types,
            confidence=result.confidence,
            show_in_ui=result.show_in_ui,
        )

    def resolve_leak_redirect_suggestion(
        self, info, user_id: str, leak_amount: float
    ):
        """Get suggestion for where to redirect savings."""
        from .investor_profile_types import (
            InvestorProfile, QuizDimensions,
            ARCHETYPE_METADATA
        )
        
        # Get profile (demo)
        dimensions = QuizDimensions(
            risk_tolerance=65,
            locus_of_control=70,
            loss_aversion=40,
            sophistication=55,
        )
        archetype = investor_profile_service.determine_archetype(dimensions)
        metadata = ARCHETYPE_METADATA[archetype]
        
        profile = InvestorProfile(
            user_id=user_id,
            archetype=archetype,
            dimensions=dimensions,
            coaching_tone=metadata["coaching_tone"],
            default_strategy=metadata["default_strategy"],
        )
        
        # Demo state
        state = UserFinancialState(
            monthly_savings=1800,
            invested_assets=35000,
            emergency_fund_months=3.5,
            monthly_expenses=4200,
            high_interest_debt=0,
            highest_debt_apr=0,
        )
        
        suggestion = next_best_action_service.get_leak_redirect_suggestion(
            profile, leak_amount, state
        )
        
        return LeakRedirectSuggestionType(
            action_type=suggestion.action_type.value,
            headline=suggestion.headline,
            description=suggestion.description,
            impact_text=suggestion.impact_text,
            monthly_amount=suggestion.monthly_amount,
            total_impact=suggestion.total_impact or 0,
            time_impact_days=suggestion.time_impact_days,
            suggested_etf=suggestion.action_params.get("suggested_etf"),
            action_screen=suggestion.action_screen,
            reasoning=suggestion.reasoning,
        )


# ══════════════════════════════════════════════════════════════════════════════
# GRAPHQL MUTATIONS
# ══════════════════════════════════════════════════════════════════════════════

class SubmitInvestorQuiz(graphene.Mutation):
    """Submit quiz answers and get investor profile."""
    
    class Arguments:
        user_id = String(required=True)
        answers = List(QuizAnswerInput, required=True)
        total_assets = Float()
        has_options_activity = Boolean()
    
    # Return fields
    success = Boolean(required=True)
    profile = Field(InvestorProfileType)
    error = String()
    
    def mutate(
        self,
        info,
        user_id: str,
        answers: list,
        total_assets: float = 0,
        has_options_activity: bool = False,
    ):
        try:
            # Convert input to dict format
            answer_dicts = [
                {
                    "question_id": a.question_id,
                    "answer_value": a.answer_value,
                    "answer_index": a.answer_index or 0,
                }
                for a in answers
            ]
            
            # Create profile
            profile = investor_profile_service.create_profile(
                user_id=user_id,
                answers=answer_dicts,
                total_assets=total_assets,
                has_options_activity=has_options_activity,
            )
            
            # In production, save to database here
            
            return SubmitInvestorQuiz(
                success=True,
                profile=InvestorProfileType(
                    user_id=profile.user_id,
                    archetype=profile.archetype.value,
                    archetype_title=profile.archetype_title,
                    archetype_description=profile.archetype_description,
                    archetype_focus=profile.archetype_focus,
                    dimensions=QuizDimensionsType(
                        risk_tolerance=profile.dimensions.risk_tolerance,
                        locus_of_control=profile.dimensions.locus_of_control,
                        loss_aversion=profile.dimensions.loss_aversion,
                        sophistication=profile.dimensions.sophistication,
                    ),
                    maturity_stage=profile.maturity_stage.value,
                    coaching_tone=profile.coaching_tone.value,
                    default_strategy=profile.default_strategy.value,
                    bias_matrix=BiasMatrixType(
                        concentration_score=0,
                        recency_score=0,
                        loss_aversion_score=0,
                        familiarity_score=0,
                        overconfidence_score=0,
                        overall_bias_score=0,
                        active_biases=[],
                    ),
                    quiz_completed=True,
                ),
            )
        except Exception as e:
            return SubmitInvestorQuiz(
                success=False,
                error=str(e),
            )


class LogBehavioralEvent(graphene.Mutation):
    """Log a behavioral event (impression or interaction) for NBA ranking refinement."""

    class Arguments:
        user_id = String(required=True)
        rec_id = String(required=True)
        event_type = String(required=True)  # "impression" | "interaction"
        action = String()  # "click" | "dismiss" | "save" (for interaction)
        time_to_interact_ms = Int()
        rec_type = String()

    success = Boolean(required=True)
    error = String()

    def mutate(
        self,
        info,
        user_id: str,
        rec_id: str,
        event_type: str,
        action: str = None,
        time_to_interact_ms: int = None,
        rec_type: str = None,
    ):
        try:
            if event_type == "impression":
                behavioral_events_module.log_impression(
                    user_id, [rec_id], rec_types=[rec_type] if rec_type else None
                )
            elif event_type == "interaction":
                behavioral_events_module.log_interaction(
                    user_id,
                    rec_id,
                    action=action or "click",
                    time_to_interact_ms=time_to_interact_ms,
                    rec_type=rec_type,
                )
            else:
                return LogBehavioralEvent(success=False, error="event_type must be impression or interaction")
            return LogBehavioralEvent(success=True)
        except Exception as e:
            return LogBehavioralEvent(success=False, error=str(e))


class InvestorProfileMutations(ObjectType):
    """Mutations for the Investor Profile system."""
    submit_investor_quiz = SubmitInvestorQuiz.Field()
    log_behavioral_event = LogBehavioralEvent.Field()


# Import for schema registration
from .investor_profile_types import ARCHETYPE_METADATA
