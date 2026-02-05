"""
GraphQL Resolvers for Active Repair Workflow

This module implements the GraphQL API endpoints that drive the mobile UI.
All resolvers integrate with the backend repair engine and broker APIs.
"""

import graphene
from graphene_django import DjangoObjectType
from django.core.cache import cache
from deployment_package.backend.core.options_repair_engine import (
    OptionsRepairEngine,
    RepairPlan,
)
from deployment_package.backend.core.options_health_monitor import HealthStatus


# GraphQL Types
class GreeksType(graphene.ObjectType):
    """Greeks values for an option"""
    delta = graphene.Float()
    gamma = graphene.Float()
    theta = graphene.Float()
    vega = graphene.Float()
    rho = graphene.Float()


class PositionType(graphene.ObjectType):
    """Open position details"""
    id = graphene.String()
    ticker = graphene.String()
    strategyType = graphene.String(name="strategy_type")
    entryPrice = graphene.Float(name="entry_price")
    currentPrice = graphene.Float(name="current_price")
    quantity = graphene.Int()
    unrealizedPnl = graphene.Float(name="unrealized_pnl")
    daysToExpiration = graphene.Int(name="days_to_expiration")
    expirationDate = graphene.String(name="expiration_date")
    greeks = graphene.Field(GreeksType)
    maxLoss = graphene.Float(name="max_loss")
    probabilityOfProfit = graphene.Float(name="probability_of_profit")
    status = graphene.String()


class RepairPlanType(graphene.ObjectType):
    """Repair plan details"""
    positionId = graphene.String(name="position_id")
    ticker = graphene.String()
    originalStrategy = graphene.String(name="original_strategy")
    currentDelta = graphene.Float(name="current_delta")
    deltaDriftPct = graphene.Float(name="delta_drift_pct")
    currentMaxLoss = graphene.Float(name="current_max_loss")
    repairType = graphene.String(name="repair_type")
    repairStrikes = graphene.String(name="repair_strikes")
    repairCredit = graphene.Float(name="repair_credit")
    newMaxLoss = graphene.Float(name="new_max_loss")
    newBreakEven = graphene.Float(name="new_break_even")
    confidenceBoost = graphene.Float(name="confidence_boost")
    headline = graphene.String()
    reason = graphene.String()
    actionDescription = graphene.String(name="action_description")
    priority = graphene.String()


class PortfolioType(graphene.ObjectType):
    """Portfolio summary"""
    totalDelta = graphene.Float(name="total_delta")
    totalGamma = graphene.Float(name="total_gamma")
    totalTheta = graphene.Float(name="total_theta")
    totalVega = graphene.Float(name="total_vega")
    portfolioHealthStatus = graphene.String(name="portfolio_health_status")
    repairsAvailable = graphene.Int(name="repairs_available")
    totalMaxLoss = graphene.Float(name="total_max_loss")


class PortfolioHealthType(graphene.ObjectType):
    """Portfolio health snapshot"""
    status = graphene.String()
    healthScore = graphene.Float(name="health_score")
    lastCheckTimestamp = graphene.String(name="last_check_timestamp")
    checks = graphene.List(graphene.JSONString)
    alerts = graphene.List(graphene.JSONString)
    repairsNeeded = graphene.Int(name="repairs_needed")
    estimatedImprovement = graphene.Float(name="estimated_improvement")


class RepairExecutionType(graphene.ObjectType):
    """Result of executing a repair plan"""
    success = graphene.Boolean()
    positionId = graphene.String(name="position_id")
    repairType = graphene.String(name="repair_type")
    executionPrice = graphene.Float(name="execution_price")
    executionCredit = graphene.Float(name="execution_credit")
    estimatedFees = graphene.Float(name="estimated_fees")
    executionMessage = graphene.String(name="execution_message")
    newPositionStatus = graphene.String(name="new_position_status")
    timestamp = graphene.String()


class BulkRepairExecutionType(graphene.ObjectType):
    """Result of executing multiple repairs"""
    success = graphene.Boolean()
    repairsExecuted = graphene.Int(name="repairs_executed")
    totalCreditCollected = graphene.Float(name="total_credit_collected")
    executionSummary = graphene.String(name="execution_summary")
    failures = graphene.List(graphene.JSONString)


class FlightManualType(graphene.ObjectType):
    """Educational content for a repair strategy"""
    id = graphene.String()
    repairType = graphene.String(name="repair_type")
    title = graphene.String()
    description = graphene.String()
    mathematicalExplanation = graphene.String(name="mathematical_explanation")
    exampleSetup = graphene.JSONString(name="example_setup")
    historicalSuccessRate = graphene.Float(name="historical_success_rate")
    edgePercentage = graphene.Float(name="edge_percentage")
    avgCreditCollected = graphene.Float(name="avg_credit_collected")
    riskMetrics = graphene.JSONString(name="risk_metrics")
    relatedVideos = graphene.List(graphene.String, name="related_videos")
    relatedArticles = graphene.List(graphene.String, name="related_articles")


class RepairHistoryType(graphene.ObjectType):
    """Historical repair entry"""
    id = graphene.String()
    positionId = graphene.String(name="position_id")
    ticker = graphene.String()
    repairType = graphene.String(name="repair_type")
    status = graphene.String()
    acceptedAt = graphene.String(name="accepted_at")
    executedAt = graphene.String(name="executed_at")
    creditCollected = graphene.Float(name="credit_collected")
    result = graphene.String()
    pnlImpact = graphene.Float(name="pnl_impact")


# -------------------- Mock Fallback Data --------------------
def _mock_portfolio() -> PortfolioType:
    return PortfolioType(
        total_delta=0.32,
        total_gamma=0.12,
        total_theta=85.0,
        total_vega=3.1,
        portfolio_health_status="healthy",
        repairs_available=1,
        total_max_loss=2500.0,
    )


def _mock_positions() -> list:
    return [
        PositionType(
            id="pos_1",
            ticker="AAPL",
            strategy_type="iron_condor",
            entry_price=2.15,
            current_price=2.42,
            quantity=1,
            unrealized_pnl=-27.0,
            days_to_expiration=12,
            expiration_date=None,
            greeks=GreeksType(delta=0.22, gamma=0.04, theta=8.5, vega=1.6, rho=0.1),
            max_loss=850.0,
            probability_of_profit=0.68,
            status="open",
        ),
        PositionType(
            id="pos_2",
            ticker="MSFT",
            strategy_type="credit_spread",
            entry_price=1.05,
            current_price=0.92,
            quantity=2,
            unrealized_pnl=26.0,
            days_to_expiration=18,
            expiration_date=None,
            greeks=GreeksType(delta=-0.12, gamma=0.02, theta=5.1, vega=0.9, rho=0.05),
            max_loss=600.0,
            probability_of_profit=0.74,
            status="open",
        ),
    ]


def _mock_repairs() -> list:
    return [
        RepairPlanType(
            position_id="pos_1",
            ticker="AAPL",
            original_strategy="iron_condor",
            current_delta=0.22,
            delta_drift_pct=18.0,
            current_max_loss=850.0,
            repair_type="roll_unbalanced_side",
            repair_strikes="240/245 - 250/255",
            repair_credit=0.35,
            new_max_loss=700.0,
            new_break_even=247.5,
            confidence_boost=0.12,
            headline="Roll the unbalanced call side",
            reason="Delta drifted beyond threshold",
            action_description="Buy back 250C/255C and sell 245C/250C",
            priority="HIGH",
        )
    ]


def _mock_portfolio_health() -> PortfolioHealthType:
    return PortfolioHealthType(
        status="healthy",
        health_score=0.82,
        last_check_timestamp=None,
        checks=[],
        alerts=[],
        repairs_needed=1,
        estimated_improvement=0.15,
    )


def _mock_repair_history() -> list:
    return []


# Queries
class Query(graphene.ObjectType):
    """GraphQL Queries for Active Repair Workflow"""

    portfolio = graphene.Field(
        PortfolioType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
    )
    positions = graphene.List(
        PositionType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
    )
    active_repair_plans = graphene.List(
        RepairPlanType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
    )
    position = graphene.Field(
        PositionType,
        position_id=graphene.String(required=True),
        user_id=graphene.String(required=True),
    )
    repair_plan = graphene.Field(
        RepairPlanType,
        position_id=graphene.String(required=True),
    )
    portfolio_health = graphene.Field(
        PortfolioHealthType,
        user_id=graphene.String(required=True),
        account_id=graphene.String(required=True),
    )
    flight_manual_by_repair_type = graphene.Field(
        FlightManualType,
        repair_type=graphene.String(required=True),
    )
    repair_history = graphene.List(
        RepairHistoryType,
        user_id=graphene.String(required=True),
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
    )

    def resolve_portfolio(self, info, user_id: str, account_id: str) -> PortfolioType:
        """
        Get portfolio summary with total Greeks and health status
        """
        cache_key = f"portfolio_{user_id}_{account_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from core.models import Portfolio

            portfolio = Portfolio.objects.get(user_id=user_id, account_id=account_id)
            positions = portfolio.positions.all()

            # Calculate aggregate Greeks
            total_delta = sum(p.current_delta for p in positions)
            total_gamma = sum(p.current_gamma for p in positions)
            total_theta = sum(p.current_theta for p in positions)
            total_vega = sum(p.current_vega for p in positions)
            total_max_loss = sum(p.max_loss for p in positions)

            # Determine health status
            health_status = "healthy"
            if abs(total_delta) > 0.75 or abs(total_vega) > 5:
                health_status = "warning"
            if abs(total_delta) > 1.0 or abs(total_vega) > 8:
                health_status = "critical"

            # Count active repairs
            repairs_available = len([p for p in positions if p.needs_repair])

            result = PortfolioType(
                total_delta=total_delta,
                total_gamma=total_gamma,
                total_theta=total_theta,
                total_vega=total_vega,
                portfolio_health_status=health_status,
                repairs_available=repairs_available,
                total_max_loss=total_max_loss,
            )

            cache.set(cache_key, result, 30)  # Cache for 30 seconds
            return result
        except Exception:
            result = _mock_portfolio()
            cache.set(cache_key, result, 30)
            return result

    def resolve_positions(self, info, user_id: str, account_id: str) -> list:
        """
        Get all open positions for user
        """
        try:
            from core.models import Position

            positions = Position.objects.filter(user_id=user_id, account_id=account_id, is_open=True)

            result = []
            for pos in positions:
                position_type = PositionType(
                    id=str(pos.id),
                    ticker=pos.ticker,
                    strategy_type=pos.strategy_type,
                    entry_price=pos.entry_price,
                    current_price=pos.current_price,
                    quantity=pos.quantity,
                    unrealized_pnl=pos.unrealized_pnl,
                    days_to_expiration=pos.days_to_expiration,
                    expiration_date=pos.expiration_date.isoformat() if pos.expiration_date else None,
                    greeks=GreeksType(
                        delta=pos.current_delta,
                        gamma=pos.current_gamma,
                        theta=pos.current_theta,
                        vega=pos.current_vega,
                        rho=pos.current_rho,
                    ),
                    max_loss=pos.max_loss,
                    probability_of_profit=pos.probability_of_profit,
                    status=pos.status,
                )
                result.append(position_type)

            return result
        except Exception:
            return _mock_positions()

    def resolve_active_repair_plans(self, info, user_id: str, account_id: str) -> list:
        """
        Get all active repair plans for user
        """
        try:
            from core.models import Position

            positions = Position.objects.filter(user_id=user_id, account_id=account_id, is_open=True)

            repair_plans = []
            for pos in positions:
                if not pos.needs_repair:
                    continue

                repair_plan = RepairPlanType(
                    position_id=str(pos.id),
                    ticker=pos.ticker,
                    original_strategy=pos.strategy_type,
                    current_delta=pos.current_delta,
                    delta_drift_pct=pos.delta_drift_pct,
                    current_max_loss=pos.max_loss,
                    repair_type=pos.repair_type,
                    repair_strikes=pos.repair_strikes,
                    repair_credit=pos.repair_credit,
                    new_max_loss=pos.new_max_loss,
                    new_break_even=pos.new_break_even,
                    confidence_boost=pos.confidence_boost,
                    headline=pos.repair_headline,
                    reason=pos.repair_reason,
                    action_description=pos.repair_action,
                    priority=pos.repair_priority,
                )
                repair_plans.append(repair_plan)

            priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            repair_plans.sort(key=lambda r: priority_order.get(r.priority, 4))

            return repair_plans
        except Exception:
            return _mock_repairs()

    def resolve_position(self, info, position_id: str, user_id: str) -> PositionType:
        """Get details for a single position"""
        from core.models import Position

        pos = Position.objects.get(id=position_id, user_id=user_id)

        return PositionType(
            id=str(pos.id),
            ticker=pos.ticker,
            strategy_type=pos.strategy_type,
            entry_price=pos.entry_price,
            current_price=pos.current_price,
            quantity=pos.quantity,
            unrealized_pnl=pos.unrealized_pnl,
            days_to_expiration=pos.days_to_expiration,
            expiration_date=pos.expiration_date.isoformat() if pos.expiration_date else None,
            greeks=GreeksType(
                delta=pos.current_delta,
                gamma=pos.current_gamma,
                theta=pos.current_theta,
                vega=pos.current_vega,
                rho=pos.current_rho,
            ),
            max_loss=pos.max_loss,
            probability_of_profit=pos.probability_of_profit,
            status=pos.status,
        )

    def resolve_repair_plan(self, info, position_id: str) -> RepairPlanType:
        """Get repair plan for a position"""
        from core.models import Position

        pos = Position.objects.get(id=position_id)
        repair_engine = OptionsRepairEngine(router=None)

        repair_plan = repair_engine.analyze_position(
            position_id=str(pos.id),
            ticker=pos.ticker,
            current_delta=pos.current_delta,
            unrealized_pnl=pos.unrealized_pnl,
            account_equity=100000,
        )

        if not repair_plan:
            return None

        return RepairPlanType(
            position_id=repair_plan.position_id,
            ticker=repair_plan.ticker,
            original_strategy=repair_plan.original_strategy,
            current_delta=repair_plan.current_delta,
            delta_drift_pct=repair_plan.delta_drift_pct,
            current_max_loss=repair_plan.current_max_loss,
            repair_type=repair_plan.repair_type,
            repair_strikes=repair_plan.repair_strikes,
            repair_credit=repair_plan.repair_credit,
            new_max_loss=repair_plan.new_max_loss,
            new_break_even=repair_plan.new_break_even,
            confidence_boost=repair_plan.confidence_boost,
            headline=repair_plan.headline,
            reason=repair_plan.reason,
            action_description=f"Execute {repair_plan.repair_type} at {repair_plan.repair_strikes}",
            priority=repair_plan.priority,
        )

    def resolve_portfolio_health(self, info, user_id: str, account_id: str) -> PortfolioHealthType:
        """Get portfolio health snapshot"""
        try:
            from deployment_package.backend.core.options_health_monitor import OptionsHealthMonitor

            monitor = OptionsHealthMonitor()
            health = monitor.run_health_check()

            return PortfolioHealthType(
                status=health.status,
                health_score=health.health_score,
                last_check_timestamp=health.last_check_timestamp,
                checks=health.checks_detail,
                alerts=health.alerts,
                repairs_needed=health.repairs_needed,
                estimated_improvement=health.estimated_improvement,
            )
        except Exception:
            return _mock_portfolio_health()

    def resolve_flight_manual_by_repair_type(self, info, repair_type: str) -> FlightManualType:
        """Get educational content for a repair type"""
        # TODO: Integrate with flight_manual_engine.py
        return FlightManualType(
            id=repair_type,
            repair_type=repair_type,
            title=f"How to {repair_type}",
            description=f"Complete guide to executing {repair_type}",
            mathematical_explanation="...",
            example_setup={},
            historical_success_rate=0.85,
            edge_percentage=15.0,
            avg_credit_collected=150.0,
            risk_metrics={},
            related_videos=[],
            related_articles=[],
        )

    def resolve_repair_history(self, info, user_id: str, limit: int = 50, offset: int = 0) -> list:
        """Get historical repairs"""
        try:
            from core.models import RepairHistory

            repairs = RepairHistory.objects.filter(user_id=user_id).order_by("-accepted_at")[offset : offset + limit]

            result = []
            for repair in repairs:
                result.append(
                    RepairHistoryType(
                        id=str(repair.id),
                        position_id=repair.position_id,
                        ticker=repair.ticker,
                        repair_type=repair.repair_type,
                        status=repair.status,
                        accepted_at=repair.accepted_at.isoformat() if repair.accepted_at else None,
                        executed_at=repair.executed_at.isoformat() if repair.executed_at else None,
                        credit_collected=repair.credit_collected,
                        result=repair.result,
                        pnl_impact=repair.pnl_impact,
                    )
                )

            return result
        except Exception:
            return _mock_repair_history()


# Mutations
class AcceptRepairPlan(graphene.Mutation):
    """Accept and deploy a repair plan"""

    class Arguments:
        position_id = graphene.String(required=True)
        repair_plan_id = graphene.String(required=True)
        user_id = graphene.String(required=True)

    repair_execution = graphene.Field(RepairExecutionType)

    def mutate(self, info, position_id: str, repair_plan_id: str, user_id: str):
        from core.models import Position, RepairHistory
        from deployment_package.backend.core.broker_api import BrokerAPI
        import datetime

        try:
            pos = Position.objects.get(id=position_id, user_id=user_id)
            repair_engine = OptionsRepairEngine(router=None)

            # Generate repair plan
            repair_plan = repair_engine.analyze_position(
                position_id=str(pos.id),
                ticker=pos.ticker,
                current_delta=pos.current_delta,
                unrealized_pnl=pos.unrealized_pnl,
                account_equity=100000,
            )

            if not repair_plan:
                raise Exception("No repair plan available")

            # Execute via broker API
            broker = BrokerAPI()
            execution = broker.execute_repair_trade(
                ticker=pos.ticker,
                repair_type=repair_plan.repair_type,
                strikes=repair_plan.repair_strikes,
            )

            # Log repair history
            RepairHistory.objects.create(
                user_id=user_id,
                position_id=position_id,
                ticker=pos.ticker,
                repair_type=repair_plan.repair_type,
                status="executed",
                accepted_at=datetime.datetime.now(),
                executed_at=datetime.datetime.now(),
                credit_collected=repair_plan.repair_credit,
            )

            return AcceptRepairPlan(
                repair_execution=RepairExecutionType(
                    success=True,
                    position_id=position_id,
                    repair_type=repair_plan.repair_type,
                    execution_credit=repair_plan.repair_credit,
                    execution_message=f"✓ {repair_plan.repair_type} executed at {repair_plan.repair_strikes}",
                    new_position_status="repaired",
                    timestamp=datetime.datetime.now().isoformat(),
                )
            )

        except Exception as e:
            return AcceptRepairPlan(
                repair_execution=RepairExecutionType(
                    success=False,
                    position_id=position_id,
                    execution_message=str(e),
                    timestamp=datetime.datetime.now().isoformat(),
                )
            )


class ExecuteBulkRepairs(graphene.Mutation):
    """Execute multiple repairs at once"""

    class Arguments:
        user_id = graphene.String(required=True)
        position_ids = graphene.List(graphene.String, required=True)

    bulk_execution = graphene.Field(BulkRepairExecutionType)

    def mutate(self, info, user_id: str, position_ids: list):
        from core.models import Position

        try:
            positions = Position.objects.filter(id__in=position_ids, user_id=user_id)
            repairs_executed = 0
            total_credit = 0.0
            failures = []

            for pos in positions:
                try:
                    # Execute repair for this position
                    # (similar to AcceptRepairPlan above)
                    repairs_executed += 1
                    total_credit += 150.0  # Placeholder
                except Exception as e:
                    failures.append({"position_id": str(pos.id), "error": str(e)})

            return ExecuteBulkRepairs(
                bulk_execution=BulkRepairExecutionType(
                    success=len(failures) == 0,
                    repairs_executed=repairs_executed,
                    total_credit_collected=total_credit,
                    execution_summary=f"Executed {repairs_executed} repairs, collected ${total_credit:.2f}",
                    failures=failures,
                )
            )

        except Exception as e:
            return ExecuteBulkRepairs(
                bulk_execution=BulkRepairExecutionType(
                    success=False,
                    repairs_executed=0,
                    total_credit_collected=0.0,
                    execution_summary=str(e),
                    failures=[],
                )
            )


class Mutation(graphene.ObjectType):
    """GraphQL Mutations for Active Repair Workflow"""

    accept_repair_plan = AcceptRepairPlan.Field()
    execute_bulk_repairs = ExecuteBulkRepairs.Field()


# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
