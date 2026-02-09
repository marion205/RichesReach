"""Autopilot GraphQL types shared by queries and mutations."""
import graphene


AutonomyLevel = graphene.Enum('AutonomyLevel', [
    'NOTIFY_ONLY',
    'APPROVE_REPAIRS',
    'AUTO_BOUNDED',
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


class AutopilotPolicyInput(graphene.InputObjectType):
    target_apy = graphene.Float()
    max_drawdown = graphene.Float()
    risk_level = RiskLevel()
    level = AutonomyLevel()
    spend_limit_24h = graphene.Float()


class RepairProofType(graphene.ObjectType):
    calmar_improvement = graphene.Float()
    integrity_check = graphene.Field(FinancialIntegrityType)
    tvl_stability_check = graphene.Boolean()
    policy_alignment = graphene.Boolean()
    explanation = graphene.String()


class RepairActionType(graphene.ObjectType):
    id = graphene.String()
    from_vault = graphene.String()
    to_vault = graphene.String()
    estimated_apy_delta = graphene.Float()
    gas_estimate = graphene.Float()
    proof = graphene.Field(RepairProofType)


class LastMoveType(graphene.ObjectType):
    id = graphene.String()
    from_vault = graphene.String()
    to_vault = graphene.String()
    executed_at = graphene.String()
    can_revert = graphene.Boolean()
    revert_deadline = graphene.String()


class AutopilotStatusType(graphene.ObjectType):
    enabled = graphene.Boolean()
    last_evaluated_at = graphene.String()
    policy = graphene.Field(AutopilotPolicyType)
    last_move = graphene.Field(LastMoveType)


class TransactionReceiptType(graphene.ObjectType):
    success = graphene.Boolean()
    tx_hash = graphene.String()
    message = graphene.String()
