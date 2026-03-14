"""
Life Decision Simulator — GraphQL Types & Query Mixin
======================================================
Exposes LifeDecisionService results via GraphQL.
Registered in schema.py as LifeDecisionQueries.

Queries
-------
  simulateDecision(
      decisionType: String,
      amount: Float!,
      description: String,
      monthlyCost: Float,
      downPayment: Float,
      loanRate: Float,
      loanTermMonths: Int,
      appreciationRate: Float,
      horizonYears: Int,
  )  →  LifeDecisionType

  simulate_decision(...)  →  LifeDecisionType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class DecisionYearType(graphene.ObjectType):
    """Net-worth comparison for one projection year."""
    year               = graphene.Int(required=True)
    net_worth_with     = graphene.Float(required=True)   # if decision is made
    net_worth_without  = graphene.Float(required=True)   # if decision is skipped
    delta              = graphene.Float(required=True)   # with − without


class LifeDecisionType(graphene.ObjectType):
    """Full simulation output for a proposed financial decision."""
    user_id            = graphene.Int(required=True)
    decision_type      = graphene.String(required=True)
    description        = graphene.String()
    amount             = graphene.Float(required=True)
    monthly_cost       = graphene.Float()

    # Key impact metrics
    opportunity_cost_10yr   = graphene.Float()   # what it costs invested instead
    net_worth_delta_10yr    = graphene.Float()   # NW difference at end of horizon
    monthly_surplus_impact  = graphene.Float()   # change in monthly investable surplus
    break_even_years        = graphene.Int()     # for appreciating assets
    total_interest_paid     = graphene.Float()   # for debt decisions

    # Context
    current_net_worth          = graphene.Float()
    investable_surplus_monthly = graphene.Float()
    return_rate                = graphene.Float()
    projection_years           = graphene.Int()

    # Trajectory
    year_by_year = graphene.List(graphene.NonNull(DecisionYearType))

    # Narrative
    headline_sentence = graphene.String()
    recommendation    = graphene.String()
    data_quality      = graphene.String()


# ── Query Mixin ───────────────────────────────────────────────────────────────

# Shared argument definitions
_DECISION_ARGS = dict(
    decision_type=graphene.String(
        default_value='purchase',
        description="purchase | monthly | debt | investment",
    ),
    amount=graphene.Float(
        required=True,
        description="Total cost of the decision (purchase price or total subscription cost)",
    ),
    description=graphene.String(
        default_value='',
        description="Human-readable label for this decision (echoed back)",
    ),
    monthly_cost=graphene.Float(
        default_value=0.0,
        description="Recurring monthly cost (lease payment, subscription, etc.)",
    ),
    down_payment=graphene.Float(
        default_value=0.0,
        description="Cash paid upfront for debt or investment decisions",
    ),
    loan_rate=graphene.Float(
        default_value=0.0,
        description="Annual loan interest rate as a decimal (e.g. 0.065 for 6.5%)",
    ),
    loan_term_months=graphene.Int(
        default_value=0,
        description="Loan repayment term in months",
    ),
    appreciation_rate=graphene.Float(
        default_value=0.0,
        description="Annual asset appreciation rate for investment decisions (e.g. 0.03)",
    ),
    horizon_years=graphene.Int(
        default_value=10,
        description="Projection window in years (default 10)",
    ),
)


class LifeDecisionQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes the Life Decision Simulator.
    Added to ExtendedQuery in schema.py.
    """

    simulate_decision = graphene.Field(
        LifeDecisionType,
        description="Simulate the long-term wealth impact of a financial decision",
        **_DECISION_ARGS,
    )
    simulateDecision = graphene.Field(
        LifeDecisionType,
        description="Life Decision Simulator (camelCase alias)",
        **_DECISION_ARGS,
    )

    def resolve_simulate_decision(self, info, **kwargs):
        return _resolve_simulate(info, **kwargs)

    def resolve_simulateDecision(self, info, **kwargs):
        return _resolve_simulate(info, **kwargs)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_simulate(info, **kwargs) -> LifeDecisionType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .life_decision_service import LifeDecisionService

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        result = LifeDecisionService().simulate_safe(user, **kwargs)

        return LifeDecisionType(
            user_id=result.user_id,
            decision_type=result.decision_type,
            description=result.description,
            amount=result.amount,
            monthly_cost=result.monthly_cost,
            opportunity_cost_10yr=result.opportunity_cost_10yr,
            net_worth_delta_10yr=result.net_worth_delta_10yr,
            monthly_surplus_impact=result.monthly_surplus_impact,
            break_even_years=result.break_even_years,
            total_interest_paid=result.total_interest_paid,
            current_net_worth=result.current_net_worth,
            investable_surplus_monthly=result.investable_surplus_monthly,
            return_rate=result.return_rate,
            projection_years=result.projection_years,
            year_by_year=[
                DecisionYearType(
                    year=y.year,
                    net_worth_with=y.net_worth_with,
                    net_worth_without=y.net_worth_without,
                    delta=y.delta,
                )
                for y in result.year_by_year
            ],
            headline_sentence=result.headline_sentence,
            recommendation=result.recommendation,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning("LifeDecisionQueries resolver error: %s", exc)
        return None
