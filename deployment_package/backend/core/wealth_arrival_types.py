"""
Wealth Arrival — GraphQL Types & Query Mixin
============================================
Exposes WealthArrivalService projections via GraphQL.
Registered in schema.py as WealthArrivalQueries.

Queries
-------
  wealthArrival(targetNetWorth: Float)  →  WealthArrivalType
  wealth_arrival(targetNetWorth: Float) →  WealthArrivalType  (snake_case alias)
"""
import graphene
import logging

logger = logging.getLogger(__name__)


# ── GraphQL Types ─────────────────────────────────────────────────────────────

class WealthYearPointType(graphene.ObjectType):
    """Net worth snapshot at the end of a single projection year."""
    year = graphene.Int(required=True)
    net_worth = graphene.Float(required=True)
    portfolio_value = graphene.Float(required=True)
    savings_balance = graphene.Float(required=True)
    annual_contribution = graphene.Float(required=True)
    cumulative_contributions = graphene.Float(required=True)


class WealthMilestoneType(graphene.ObjectType):
    """A specific net-worth milestone and when it will be reached."""
    target_amount = graphene.Float(required=True)
    years_away = graphene.Int()          # -1 means beyond projection horizon
    arrival_year = graphene.Int()        # calendar year; -1 = beyond horizon
    already_achieved = graphene.Boolean(required=True)
    label = graphene.String(required=True)  # e.g. "$1M"


class WealthScenarioType(graphene.ObjectType):
    """Full projection for one scenario (conservative / moderate / aggressive)."""
    scenario = graphene.String(required=True)
    annual_return = graphene.Float(required=True)
    year_by_year = graphene.List(graphene.NonNull(WealthYearPointType))
    milestones = graphene.List(graphene.NonNull(WealthMilestoneType))
    wealth_arrival_years = graphene.Int()   # null = not reached within horizon
    final_net_worth = graphene.Float()
    total_contributions = graphene.Float()
    total_growth = graphene.Float()


class WealthArrivalType(graphene.ObjectType):
    """Full Wealth Arrival projection for the authenticated user."""
    user_id = graphene.Int(required=True)

    # Current financial snapshot
    current_net_worth = graphene.Float()
    current_portfolio_value = graphene.Float()
    current_savings_balance = graphene.Float()
    current_debt = graphene.Float()
    estimated_monthly_income = graphene.Float()
    investable_surplus_monthly = graphene.Float()
    annual_contribution = graphene.Float()
    savings_rate_pct = graphene.Float()

    # Projection inputs
    projection_years = graphene.Int()
    risk_tolerance = graphene.String()
    target_net_worth = graphene.Float()
    current_age = graphene.Int()

    # Primary scenario (matches user's risk tolerance)
    primary = graphene.Field(WealthScenarioType)

    # All three scenarios
    scenarios = graphene.List(graphene.NonNull(WealthScenarioType))

    headline_sentence = graphene.String()
    data_quality = graphene.String()   # "actual" | "estimated" | "insufficient"


# ── Query Mixin ───────────────────────────────────────────────────────────────

class WealthArrivalQueries(graphene.ObjectType):
    """
    GraphQL query mixin: exposes Wealth Arrival projections.
    Added to ExtendedQuery in schema.py.
    """

    wealth_arrival = graphene.Field(
        WealthArrivalType,
        target_net_worth=graphene.Float(
            default_value=1_000_000.0,
            description="The net-worth milestone the user wants to reach (default $1M)",
        ),
        description="Multi-year wealth arrival projection for the authenticated user",
    )
    wealthArrival = graphene.Field(
        WealthArrivalType,
        target_net_worth=graphene.Float(
            default_value=1_000_000.0,
            description="The net-worth milestone the user wants to reach (default $1M)",
        ),
        description="Wealth arrival projection (camelCase alias)",
    )

    def resolve_wealth_arrival(self, info, target_net_worth=1_000_000.0):
        return _resolve_wealth_arrival(info, target_net_worth)

    def resolve_wealthArrival(self, info, target_net_worth=1_000_000.0):
        return _resolve_wealth_arrival(info, target_net_worth)


# ── Shared resolver logic ─────────────────────────────────────────────────────

def _resolve_wealth_arrival(info, target_net_worth: float) -> WealthArrivalType | None:
    try:
        from .graphql_utils import get_user_from_context
        from .wealth_arrival_service import WealthArrivalService

        user = get_user_from_context(info.context)
        if not user or getattr(user, 'is_anonymous', True):
            return None

        result = WealthArrivalService().project_safe(
            user, target_net_worth=target_net_worth
        )

        return WealthArrivalType(
            user_id=result.user_id,
            current_net_worth=result.current_net_worth,
            current_portfolio_value=result.current_portfolio_value,
            current_savings_balance=result.current_savings_balance,
            current_debt=result.current_debt,
            estimated_monthly_income=result.estimated_monthly_income,
            investable_surplus_monthly=result.investable_surplus_monthly,
            annual_contribution=result.annual_contribution,
            savings_rate_pct=result.savings_rate_pct,
            projection_years=result.projection_years,
            risk_tolerance=result.risk_tolerance,
            target_net_worth=result.target_net_worth,
            current_age=result.current_age,
            primary=_scenario_to_gql(result.primary) if result.primary else None,
            scenarios=[_scenario_to_gql(s) for s in result.scenarios],
            headline_sentence=result.headline_sentence,
            data_quality=result.data_quality,
        )
    except Exception as exc:
        logger.warning("WealthArrivalQueries resolver error: %s", exc)
        return None


def _scenario_to_gql(scenario) -> WealthScenarioType:
    return WealthScenarioType(
        scenario=scenario.scenario,
        annual_return=scenario.annual_return,
        year_by_year=[
            WealthYearPointType(
                year=p.year,
                net_worth=p.net_worth,
                portfolio_value=p.portfolio_value,
                savings_balance=p.savings_balance,
                annual_contribution=p.annual_contribution,
                cumulative_contributions=p.cumulative_contributions,
            )
            for p in scenario.year_by_year
        ],
        milestones=[
            WealthMilestoneType(
                target_amount=m.target_amount,
                years_away=m.years_away,
                arrival_year=m.arrival_year,
                already_achieved=m.already_achieved,
                label=m.label,
            )
            for m in scenario.milestones
        ],
        wealth_arrival_years=scenario.wealth_arrival_years,
        final_net_worth=scenario.final_net_worth,
        total_contributions=scenario.total_contributions,
        total_growth=scenario.total_growth,
    )
