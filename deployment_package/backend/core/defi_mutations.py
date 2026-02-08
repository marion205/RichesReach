"""
GraphQL Mutations for DeFi Operations (AAVE, etc.)
Wired to backend validation service and position tracking.
All mutations validate through defi_validation_service before returning approval.
"""
import graphene
import logging
from decimal import Decimal
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from graphene.types import JSONString

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


class ValidationResultType(graphene.ObjectType):
    """Result of backend transaction validation"""
    is_valid = graphene.Boolean()
    reason = graphene.String()
    warnings = graphene.List(graphene.String)
    transaction_id = graphene.String()


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
        wallet_address = graphene.String(required=True)
        pool_id = graphene.String()
        chain_id = graphene.Int(default_value=11155111)

    success = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(DefiPositionType)
    validation = graphene.Field(ValidationResultType)
    error = graphene.String()

    @login_required
    def mutate(self, info, symbol, quantity, wallet_address,
               use_as_collateral=False, pool_id=None, chain_id=11155111):
        user = info.context.user

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
        wallet_address = graphene.String(required=True)
        pool_id = graphene.String()
        chain_id = graphene.Int(default_value=11155111)

    success = graphene.Boolean()
    message = graphene.String()
    position = JSONString
    validation = graphene.Field(ValidationResultType)
    error = graphene.String()

    @login_required
    def mutate(self, info, symbol, amount, wallet_address,
               rate_mode='VARIABLE', pool_id=None, chain_id=11155111):
        user = info.context.user
        rate_mode_int = 1 if rate_mode == 'STABLE' else 2

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

            return DefiBorrow(
                success=True,
                message=f"Borrow of {amount} {symbol} approved. Send via WalletConnect.",
                position={
                    'amount': amount,
                    'rateMode': rate_mode,
                    'healthFactorWarnings': result.get('warnings', []),
                },
                validation=validation,
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
            result = validate_and_record_intent(
                user=user,
                tx_type='deposit',
                wallet_address=wallet,
                pool_id=poolId,
                chain_id=chainId,
                symbol=symbol,
                amount_human=str(amount),
            )

            if not result.get('isValid'):
                return StakeIntentResultType(
                    ok=False,
                    message=result.get('reason', 'Validation failed'),
                    poolId=poolId,
                    amount=amount,
                    warnings=result.get('warnings', []),
                )

            return StakeIntentResultType(
                ok=True,
                message=f"Stake intent approved for {amount}",
                poolId=poolId,
                amount=amount,
                warnings=result.get('warnings', []),
                transaction_id=result.get('transactionId'),
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
    success = graphene.Boolean()
    message = graphene.String()
    position_id = graphene.String()


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

            return RecordStakeTransactionResultType(
                success=result.get('success', False),
                message=result.get('message', 'Transaction recorded'),
                position_id=result.get('transactionId'),
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


class DefiMutations(graphene.ObjectType):
    """DeFi mutations — all wired to validation service"""
    defi_supply = DefiSupply.Field()
    defi_borrow = DefiBorrow.Field()
    stake_intent = StakeIntent.Field()
    record_stake_transaction = RecordStakeTransaction.Field()
    validate_defi_transaction = ValidateDefiTransaction.Field()
    # CamelCase aliases for GraphQL schema
    defiSupply = DefiSupply.Field()
    defiBorrow = DefiBorrow.Field()
    stakeIntent = StakeIntent.Field()
    recordStakeTransaction = RecordStakeTransaction.Field()
    validateDefiTransaction = ValidateDefiTransaction.Field()
