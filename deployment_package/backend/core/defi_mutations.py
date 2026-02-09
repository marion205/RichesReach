"""
GraphQL Mutations for DeFi Operations (AAVE, etc.)
Wired to backend validation service and position tracking.
All mutations validate through defi_validation_service before returning approval.
"""
import graphene
import logging
from decimal import Decimal
try:
    from graphql_jwt.decorators import login_required
except ImportError:  # Optional dependency in dev
    def login_required(func):
        return func
from graphql import GraphQLError
from graphene.types import JSONString
from .autopilot_types import (
    AutopilotPolicyType,
    AutopilotPolicyInput,
    RepairActionType,
    RepairProofType,
    FinancialIntegrityType,
    TransactionReceiptType,
)

logger = logging.getLogger(__name__)


# ---- GraphQL Types (shared by queries + mutations) ----

class DefiPositionType(graphene.ObjectType):
    """DeFi position information"""
    quantity = graphene.Float()
    use_as_collateral = graphene.Boolean()


class YieldPoolType(graphene.ObjectType):
    """Yield pool information"""
    id = graphene.String()
    protocol = graphene.String()
    chain = graphene.String()
    symbol = graphene.String()
    poolAddress = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.Float()
    audit = JSONString()


class OptimizedPoolType(graphene.ObjectType):
    """Optimized pool allocation"""
    id = graphene.String()
    protocol = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.Float()
    symbol = graphene.String()
    chain = graphene.String()
    weight = graphene.Float()


class YieldOptimizerResultType(graphene.ObjectType):
    """AI yield optimizer result"""
    expectedApy = graphene.Float()
    totalRisk = graphene.Float()
    explanation = graphene.String()
    optimizationStatus = graphene.String()
    allocations = graphene.List(OptimizedPoolType)
    riskMetrics = JSONString()


class PoolAnalyticsPointType(graphene.ObjectType):
    """Pool analytics data point"""
    date = graphene.String()
    feeApy = graphene.Float()
    ilEstimate = graphene.Float()
    netApy = graphene.Float()


class ProtocolInfoType(graphene.ObjectType):
    """Protocol metadata for UI"""
    name = graphene.String()
    slug = graphene.String()


class ChainInfoType(graphene.ObjectType):
    """Chain metadata for UI"""
    name = graphene.String()
    chain_id = graphene.Int()


class PoolSummaryType(graphene.ObjectType):
    """Pool summary used by staking intent responses"""
    id = graphene.String()
    protocol = graphene.Field(ProtocolInfoType)
    chain = graphene.Field(ChainInfoType)
    symbol = graphene.String()
    total_apy = graphene.Float()
    risk_score = graphene.Float()


class ValidationResultType(graphene.ObjectType):
    """Result of backend transaction validation"""
    is_valid = graphene.Boolean()
    reason = graphene.String()
    warnings = graphene.List(graphene.String)
    transaction_id = graphene.String()


class PositionSummaryType(graphene.ObjectType):
    """Position summary for mutation responses"""
    id = graphene.String()
    staked_lp = graphene.Float()
    rewards_earned = graphene.Float()


class ActionSummaryType(graphene.ObjectType):
    """Action summary for mutation responses"""
    id = graphene.String()
    tx_hash = graphene.String()
    action = graphene.String()
    success = graphene.Boolean()


class UpdateAutopilotPolicy(graphene.Mutation):
    """Update the Auto-Pilot policy settings."""

    class Arguments:
        input = AutopilotPolicyInput(required=True)

    policy = graphene.Field(AutopilotPolicyType)

    @login_required
    def mutate(self, info, input):
        from .autopilot_service import set_autopilot_policy

        policy = set_autopilot_policy(info.context.user, dict(input))
        return UpdateAutopilotPolicy(
            policy=AutopilotPolicyType(
                target_apy=policy.get('target_apy'),
                max_drawdown=policy.get('max_drawdown'),
                risk_level=policy.get('risk_level'),
                level=policy.get('level'),
                spend_limit_24h=policy.get('spend_limit_24h'),
            )
        )


class ToggleAutopilot(graphene.Mutation):
    """Enable or disable Auto-Pilot."""

    class Arguments:
        enabled = graphene.Boolean(required=True)

    ok = graphene.Boolean()

    @login_required
    def mutate(self, info, enabled):
        from .autopilot_service import set_autopilot_enabled

        result = set_autopilot_enabled(info.context.user, enabled)
        return ToggleAutopilot(ok=bool(result))


class ExecuteRepair(graphene.Mutation):
    """Execute a pending repair action."""

    class Arguments:
        repair_id = graphene.String(required=True)

    receipt = graphene.Field(TransactionReceiptType)

    @login_required
    def mutate(self, info, repair_id):
        from .autopilot_service import execute_repair

        result = execute_repair(info.context.user, repair_id)
        return ExecuteRepair(
            receipt=TransactionReceiptType(
                success=result.get('success', False),
                tx_hash=result.get('tx_hash'),
                message=result.get('message', ''),
            )
        )


class RevertAutopilotMove(graphene.Mutation):
    """Revert the most recent Auto-Pilot move within the allowed window."""

    receipt = graphene.Field(TransactionReceiptType)

    @login_required
    def mutate(self, info):
        from .autopilot_service import revert_last_move

        result = revert_last_move(info.context.user)
        return RevertAutopilotMove(
            receipt=TransactionReceiptType(
                success=result.get('success', False),
                tx_hash=result.get('tx_hash'),
                message=result.get('message', ''),
            )
        )


class SeedAutopilotDemo(graphene.Mutation):
    """Create a demo repair action for Auto-Pilot UI testing."""

    repair = graphene.Field(RepairActionType)

    @login_required
    def mutate(self, info):
        from .autopilot_service import seed_demo_repair

        demo = seed_demo_repair(info.context.user)
        proof = demo.get('proof', {})
        integrity = proof.get('integrity_check', {})

        return SeedAutopilotDemo(
            repair=RepairActionType(
                id=demo.get('id'),
                from_vault=demo.get('from_vault'),
                to_vault=demo.get('to_vault'),
                estimated_apy_delta=demo.get('estimated_apy_delta'),
                gas_estimate=demo.get('gas_estimate'),
                proof=RepairProofType(
                    calmar_improvement=proof.get('calmar_improvement'),
                    integrity_check=FinancialIntegrityType(
                        altman_z_score=integrity.get('altman_z_score'),
                        beneish_m_score=integrity.get('beneish_m_score'),
                        is_erc4626_compliant=integrity.get('is_erc4626_compliant'),
                    ),
                    tvl_stability_check=proof.get('tvl_stability_check'),
                    policy_alignment=proof.get('policy_alignment'),
                    explanation=proof.get('explanation'),
                    policy_version=proof.get('policy_version'),
                    guardrails=proof.get('guardrails'),
                ),
            )
        )


def _resolve_wallet(user, wallet_address: str = None) -> str:
    """Resolve wallet address for a user if not provided."""
    if wallet_address:
        return wallet_address
    try:
        from .defi_models import UserDeFiPosition

        last_position = UserDeFiPosition.objects.filter(user=user).order_by('-updated_at').first()
        if last_position:
            return last_position.wallet_address
    except Exception:
        pass
    return ''


def _build_pool_summary(pool):
    """Build a pool summary with latest APY/risk."""
    if not pool:
        return None

    latest = None
    try:
        latest = pool.yield_snapshots.order_by('-timestamp').first()
    except Exception:
        latest = None

    total_apy = float(latest.apy_total) if latest else 0.0
    risk_score = float(latest.risk_score) if latest else 0.0

    protocol = ProtocolInfoType(
        name=pool.protocol.name if pool.protocol else '',
        slug=pool.protocol.slug if pool.protocol else '',
    )
    chain = ChainInfoType(
        name=pool.chain,
        chain_id=pool.chain_id,
    )

    return PoolSummaryType(
        id=str(pool.id),
        protocol=protocol,
        chain=chain,
        symbol=pool.symbol,
        total_apy=total_apy,
        risk_score=risk_score,
    )


# ---- Mutations ----

class DefiSupply(graphene.Mutation):
    """
    Supply/deposit assets to DeFi protocol.
    Validates through risk engine before approving.
    """

    class Arguments:
        symbol = graphene.String(required=True)
        quantity = graphene.Float(required=True)
        use_as_collateral = graphene.Boolean(default_value=False)
        wallet_address = graphene.String(required=False)
        pool_id = graphene.String()
        chain_id = graphene.Int(default_value=11155111)

    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(DefiPositionType)
    validation = graphene.Field(ValidationResultType)
    error = graphene.String()

    @login_required
    def mutate(self, info, symbol, quantity, wallet_address=None,
               use_as_collateral=False, pool_id=None, chain_id=11155111):
        user = info.context.user

        wallet_address = _resolve_wallet(user, wallet_address)
        if not wallet_address:
            return DefiSupply(
                success=False,
                message='Wallet address is required to validate this transaction.',
                error='wallet_required',
            )

        try:
            from .defi_validation_service import validate_and_record_intent
            result = validate_and_record_intent(
                user=user,
                tx_type='deposit',
                wallet_address=wallet_address,
                pool_id=pool_id or '',
                chain_id=chain_id,
                symbol=symbol,
                amount_human=str(quantity),
            )

            validation = ValidationResultType(
                is_valid=result.get('isValid', False),
                reason=result.get('reason', ''),
                warnings=result.get('warnings', []),
                transaction_id=result.get('transactionId'),
            )

            if not result.get('isValid'):
                return DefiSupply(
                    success=False,
                    message=result.get('reason', 'Validation failed'),
                    validation=validation,
                    error=result.get('reason'),
                )

            return DefiSupply(
                success=True,
                message=f"Deposit of {quantity} {symbol} approved. Send via WalletConnect.",
                position=DefiPositionType(
                    quantity=quantity,
                    use_as_collateral=use_as_collateral
                ),
                validation=validation,
            )

        except Exception as e:
            logger.error(f"DefiSupply error: {e}")
            return DefiSupply(
                success=False,
                message=str(e),
                error=str(e),
            )


class DefiBorrow(graphene.Mutation):
    """
    Borrow assets from DeFi protocol.
    Validates health factor before approving.
    """

    class Arguments:
        symbol = graphene.String(required=True)
        amount = graphene.Float(required=True)
        rate_mode = graphene.String(default_value='VARIABLE')
        wallet_address = graphene.String(required=False)
        pool_id = graphene.String()
        chain_id = graphene.Int(default_value=11155111)

    success = graphene.Boolean()
    message = graphene.String()
    position = JSONString
    validation = graphene.Field(ValidationResultType)
    health_factor_after = graphene.Float()
    error = graphene.String()

    @login_required
    def mutate(self, info, symbol, amount, wallet_address=None,
               rate_mode='VARIABLE', pool_id=None, chain_id=11155111):
        user = info.context.user
        rate_mode_int = 1 if rate_mode == 'STABLE' else 2

        wallet_address = _resolve_wallet(user, wallet_address)
        if not wallet_address:
            return DefiBorrow(
                success=False,
                message='Wallet address is required to validate this transaction.',
                error='wallet_required',
            )

        try:
            from .defi_validation_service import validate_and_record_intent
            result = validate_and_record_intent(
                user=user,
                tx_type='borrow',
                wallet_address=wallet_address,
                pool_id=pool_id or '',
                chain_id=chain_id,
                symbol=symbol,
                amount_human=str(amount),
                rate_mode=rate_mode_int,
            )

            validation = ValidationResultType(
                is_valid=result.get('isValid', False),
                reason=result.get('reason', ''),
                warnings=result.get('warnings', []),
                transaction_id=result.get('transactionId'),
            )

            if not result.get('isValid'):
                return DefiBorrow(
                    success=False,
                    message=result.get('reason', 'Validation failed'),
                    validation=validation,
                    error=result.get('reason'),
                )

            # Estimate post-borrow health factor (simple heuristic)
            health_factor_after = None
            try:
                from .defi_models import UserDeFiPosition, DeFiTransaction

                positions = UserDeFiPosition.objects.filter(
                    user=user,
                    wallet_address=wallet_address,
                    is_active=True,
                )
                total_collateral = sum(float(p.staked_value_usd) for p in positions)

                total_borrowed = 0.0
                borrows = DeFiTransaction.objects.filter(
                    user=user,
                    action='borrow',
                    status='confirmed',
                )
                repays = DeFiTransaction.objects.filter(
                    user=user,
                    action='repay',
                    status='confirmed',
                )
                total_borrowed += sum(float(b.amount_usd) for b in borrows)
                total_borrowed -= sum(float(r.amount_usd) for r in repays)
                total_borrowed = max(0.0, total_borrowed + float(amount))

                if total_borrowed > 0 and total_collateral > 0:
                    health_factor_after = (total_collateral * 0.80) / total_borrowed
            except Exception:
                health_factor_after = None

            return DefiBorrow(
                success=True,
                message=f"Borrow of {amount} {symbol} approved. Send via WalletConnect.",
                position={
                    'amount': amount,
                    'rateMode': rate_mode,
                    'healthFactorWarnings': result.get('warnings', []),
                },
                validation=validation,
                health_factor_after=health_factor_after,
            )

        except Exception as e:
            logger.error(f"DefiBorrow error: {e}")
            return DefiBorrow(
                success=False,
                message=str(e),
                error=str(e),
            )


class StakeIntentResultType(graphene.ObjectType):
    """Stake intent result"""
    ok = graphene.Boolean()
    message = graphene.String()
    poolId = graphene.String()
    amount = graphene.Float()
    warnings = graphene.List(graphene.String)
    transaction_id = graphene.String()
    pool = graphene.Field(PoolSummaryType)
    required_approvals = graphene.List(graphene.String)


class StakeIntent(graphene.Mutation):
    """
    Create a stake intent — validate the deposit before user signs on-chain.
    """
    class Arguments:
        poolId = graphene.String(required=True)
        wallet = graphene.String(required=True)
        amount = graphene.Float(required=True)
        chainId = graphene.Int(default_value=11155111)
        symbol = graphene.String(default_value='')

    Output = StakeIntentResultType

    @login_required
    def mutate(self, info, poolId, wallet, amount, chainId=11155111, symbol=''):
        user = info.context.user

        try:
            from .defi_validation_service import validate_and_record_intent
            from .defi_models import DeFiPool

            pool = DeFiPool.objects.filter(id=poolId).select_related('protocol').first()
            result = validate_and_record_intent(
                user=user,
                tx_type='deposit',
                wallet_address=wallet,
                pool_id=poolId,
                chain_id=chainId,
                symbol=symbol,
                amount_human=str(amount),
            )

            pool_summary = _build_pool_summary(pool)
            required_approvals = []
            if pool and pool.pool_address:
                required_approvals = [pool.pool_address]

            if not result.get('isValid'):
                return StakeIntentResultType(
                    ok=False,
                    message=result.get('reason', 'Validation failed'),
                    poolId=poolId,
                    amount=amount,
                    warnings=result.get('warnings', []),
                    pool=pool_summary,
                    required_approvals=required_approvals,
                )

            return StakeIntentResultType(
                ok=True,
                message=f"Stake intent approved for {amount}",
                poolId=poolId,
                amount=amount,
                warnings=result.get('warnings', []),
                transaction_id=result.get('transactionId'),
                pool=pool_summary,
                required_approvals=required_approvals,
            )

        except Exception as e:
            logger.error(f"StakeIntent error: {e}")
            return StakeIntentResultType(
                ok=False,
                message=str(e),
                poolId=poolId,
                amount=amount,
            )


class RecordStakeTransactionResultType(graphene.ObjectType):
    """Record stake transaction result"""
    ok = graphene.Boolean()
    success = graphene.Boolean()
    message = graphene.String()
    position_id = graphene.String()
    position = graphene.Field(PositionSummaryType)
    action = graphene.Field(ActionSummaryType)


class RecordStakeTransaction(graphene.Mutation):
    """
    Record a confirmed on-chain transaction.
    Creates/updates the user's DeFi position in the database.
    """
    class Arguments:
        poolId = graphene.String(required=True)
        chainId = graphene.Int(required=True)
        wallet = graphene.String(required=True)
        txHash = graphene.String(required=True)
        amount = graphene.Float(required=True)
        action = graphene.String(default_value='deposit')
        gasUsed = graphene.Int()

    Output = RecordStakeTransactionResultType

    @login_required
    def mutate(self, info, poolId, chainId, wallet, txHash, amount,
               action='deposit', gasUsed=None):
        user = info.context.user

        try:
            from .defi_validation_service import confirm_transaction
            from .defi_models import DeFiTransaction
            result = confirm_transaction(
                tx_hash=txHash,
                pool_id=poolId,
                user=user,
                wallet_address=wallet,
                chain_id=chainId,
                amount_human=str(amount),
                action=action,
                gas_used=gasUsed,
            )

            tx_record = DeFiTransaction.objects.filter(tx_hash=txHash).first()
            position_summary = None
            action_summary = None

            if tx_record:
                if tx_record.position:
                    position_summary = PositionSummaryType(
                        id=str(tx_record.position.id),
                        staked_lp=float(tx_record.position.staked_amount),
                        rewards_earned=float(tx_record.position.rewards_earned),
                    )
                action_summary = ActionSummaryType(
                    id=str(tx_record.id),
                    tx_hash=tx_record.tx_hash,
                    action=tx_record.action,
                    success=tx_record.status == 'confirmed',
                )

            return RecordStakeTransactionResultType(
                ok=result.get('success', False),
                success=result.get('success', False),
                message=result.get('message', 'Transaction recorded'),
                position_id=result.get('transactionId'),
                position=position_summary,
                action=action_summary,
            )

        except Exception as e:
            logger.error(f"RecordStakeTransaction error: {e}")
            return RecordStakeTransactionResultType(
                success=False,
                message=f"Error recording transaction: {str(e)}",
            )


class ValidateDefiTransaction(graphene.Mutation):
    """
    Standalone validation endpoint.
    Called by the mobile app's HybridTransactionService before sending on-chain tx.
    """
    class Arguments:
        type = graphene.String(required=True)
        wallet_address = graphene.String(required=True)
        symbol = graphene.String(default_value='')
        amount = graphene.String(default_value='0')
        chain_id = graphene.Int(default_value=11155111)
        pool_id = graphene.String(default_value='')
        rate_mode = graphene.Int(default_value=2)

    Output = ValidationResultType

    @login_required
    def mutate(self, info, type, wallet_address, symbol='', amount='0',
               chain_id=11155111, pool_id='', rate_mode=2):
        user = info.context.user

        try:
            from .defi_validation_service import validate_transaction
            result = validate_transaction(
                user=user,
                tx_type=type,
                wallet_address=wallet_address,
                symbol=symbol,
                amount_human=amount,
                chain_id=chain_id,
                pool_id=pool_id,
                rate_mode=rate_mode,
            )

            return ValidationResultType(
                is_valid=result.is_valid,
                reason=result.reason,
                warnings=result.warnings,
            )

        except Exception as e:
            logger.error(f"ValidateDefiTransaction error: {e}")
            return ValidationResultType(
                is_valid=False,
                reason=str(e),
                warnings=[],
            )


class HarvestRewards(graphene.Mutation):
    """Record a harvest rewards transaction for a position."""

    class Arguments:
        positionId = graphene.String(required=True)
        txHash = graphene.String(required=True)

    ok = graphene.Boolean()
    message = graphene.String()
    action = graphene.Field(ActionSummaryType)

    @login_required
    def mutate(self, info, positionId, txHash):
        user = info.context.user
        try:
            from .defi_models import UserDeFiPosition, DeFiTransaction
            from .defi_validation_service import confirm_transaction

            position = UserDeFiPosition.objects.filter(id=positionId, user=user).select_related('pool').first()
            if not position:
                return HarvestRewards(ok=False, message='Position not found')

            amount = float(position.rewards_earned)
            result = confirm_transaction(
                tx_hash=txHash,
                pool_id=str(position.pool.id),
                user=user,
                wallet_address=position.wallet_address,
                chain_id=position.pool.chain_id,
                amount_human=str(amount),
                action='harvest',
            )

            tx_record = DeFiTransaction.objects.filter(tx_hash=txHash).first()
            action_summary = None
            if tx_record:
                action_summary = ActionSummaryType(
                    id=str(tx_record.id),
                    tx_hash=tx_record.tx_hash,
                    action=tx_record.action,
                    success=tx_record.status == 'confirmed',
                )

            return HarvestRewards(
                ok=result.get('success', False),
                message=result.get('message', 'Harvest recorded'),
                action=action_summary,
            )

        except Exception as e:
            logger.error(f"HarvestRewards error: {e}")
            return HarvestRewards(ok=False, message=str(e))


class DefiMutations(graphene.ObjectType):
    """DeFi mutations — all wired to validation service"""
    defi_supply = DefiSupply.Field()
    defi_borrow = DefiBorrow.Field()
    stake_intent = StakeIntent.Field()
    record_stake_transaction = RecordStakeTransaction.Field()
    validate_defi_transaction = ValidateDefiTransaction.Field()
    harvest_rewards = HarvestRewards.Field()
    update_autopilot_policy = UpdateAutopilotPolicy.Field()
    toggle_autopilot = ToggleAutopilot.Field()
    execute_repair = ExecuteRepair.Field()
    seed_autopilot_demo = SeedAutopilotDemo.Field()
    revert_autopilot_move = RevertAutopilotMove.Field()
    # CamelCase aliases for GraphQL schema
    defiSupply = DefiSupply.Field()
    defiBorrow = DefiBorrow.Field()
    stakeIntent = StakeIntent.Field()
    recordStakeTransaction = RecordStakeTransaction.Field()
    validateDefiTransaction = ValidateDefiTransaction.Field()
    harvestRewards = HarvestRewards.Field()
    updateAutopilotPolicy = UpdateAutopilotPolicy.Field()
    toggleAutopilot = ToggleAutopilot.Field()
    executeRepair = ExecuteRepair.Field()
    seedAutopilotDemo = SeedAutopilotDemo.Field()
    revertAutopilotMove = RevertAutopilotMove.Field()
