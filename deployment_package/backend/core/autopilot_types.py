"""Autopilot GraphQL types shared by queries and mutations."""
import graphene
from graphene.types import JSONString


AutonomyLevel = graphene.Enum('AutonomyLevel', [
    'NOTIFY_ONLY',
    'APPROVE_REPAIRS',
    'AUTO_BOUNDED',
    'AUTO_SPEND',
])

RiskLevel = graphene.Enum('RiskLevel', [
    'FORTRESS',
    'BALANCED',
    'SPECULATIVE',
])


class FinancialIntegrityType(graphene.ObjectType):
    """Financial integrity metrics for a vault"""
    altman_z_score = graphene.Float()
    beneish_m_score = graphene.Float()
    is_erc4626_compliant = graphene.Boolean()


class AutopilotPolicyType(graphene.ObjectType):
    target_apy = graphene.Float()
    max_drawdown = graphene.Float()
    risk_level = RiskLevel()
    level = AutonomyLevel()
    spend_limit_24h = graphene.Float()
    spend_permission_enabled = graphene.Boolean()
    spend_permission_expires_at = graphene.String()
    orchestration_mode = graphene.String()


class AutopilotPolicyInput(graphene.InputObjectType):
    target_apy = graphene.Float()
    max_drawdown = graphene.Float()
    risk_level = RiskLevel()
    level = AutonomyLevel()
    spend_limit_24h = graphene.Float()
    spend_permission_enabled = graphene.Boolean()
    spend_permission_expires_at = graphene.String()
    orchestration_mode = graphene.String()


class RepairProofType(graphene.ObjectType):
    calmar_improvement = graphene.Float()
    integrity_check = graphene.Field(FinancialIntegrityType)
    tvl_stability_check = graphene.Boolean()
    policy_alignment = graphene.Boolean()
    explanation = graphene.String()
    if_then = graphene.String(description='Plain-English IF/THEN explanation')
    plain_summary = graphene.String(description='Short plain-English summary')
    before_after = JSONString(description='Current vs target: calmar, max_drawdown, tvl_stability, apy')
    policy_version = graphene.String()
    guardrails = JSONString()


class RepairOptionVariant(graphene.Enum):
    FORTRESS = 'FORTRESS'
    BALANCED = 'BALANCED'
    YIELD_MAX = 'YIELD_MAX'


class RepairOptionType(graphene.ObjectType):
    """One of three repair options per position: Fortress (safest), Balanced (best Calmar), Yield-max (highest APY within policy)."""
    variant = graphene.Field(RepairOptionVariant)
    to_vault = graphene.String()
    to_pool_id = graphene.String()
    estimated_apy_delta = graphene.Float()
    proof = graphene.Field(RepairProofType)


class RepairActionType(graphene.ObjectType):
    id = graphene.String()
    from_vault = graphene.String()
    to_vault = graphene.String()
    estimated_apy_delta = graphene.Float()
    gas_estimate = graphene.Float()
    proof = graphene.Field(RepairProofType)
    source = graphene.String()
    from_pool_id = graphene.String()
    to_pool_id = graphene.String()
    execution_plan = JSONString()
    agent_trace = JSONString()
    options = graphene.List(RepairOptionType, description='Three alternatives: Fortress, Balanced, Yield-max')


class LastMoveType(graphene.ObjectType):
    id = graphene.String()
    from_vault = graphene.String()
    to_vault = graphene.String()
    executed_at = graphene.String()
    can_revert = graphene.Boolean()
    revert_deadline = graphene.String()


class CircuitBreakerStatusType(graphene.ObjectType):
    """Circuit breaker state for crisis explainer UI."""
    state = graphene.String(description='CLOSED | OPEN | HALF_OPEN')
    reason = graphene.String()
    triggered_at = graphene.String()
    triggered_by = graphene.String()
    chain_id = graphene.Int()
    auto_resume_at = graphene.String()


class AutopilotStatusType(graphene.ObjectType):
    enabled = graphene.Boolean()
    last_evaluated_at = graphene.String()
    policy = graphene.Field(AutopilotPolicyType)
    last_move = graphene.Field(LastMoveType)
    relayer_configured = graphene.Boolean(description="True if relayer can submit repairs (user signs once)")
    relayer_paused_chain_ids = graphene.List(graphene.Int, description="Chain IDs where relayer is paused (e.g. gas spike)")
    circuit_breaker = graphene.Field(CircuitBreakerStatusType, description="DeFi halt status for crisis banner")


class TransactionReceiptType(graphene.ObjectType):
    success = graphene.Boolean()
    tx_hash = graphene.String()
    message = graphene.String()


class DeFiAlertType(graphene.ObjectType):
    """GraphQL type for DeFi alerts displayed in the notification center."""
    id = graphene.String()
    alert_type = graphene.String()
    severity = graphene.String()
    title = graphene.String()
    message = graphene.String()
    data = JSONString()
    repair_id = graphene.String()
    is_read = graphene.Boolean()
    is_dismissed = graphene.Boolean()
    created_at = graphene.String()
