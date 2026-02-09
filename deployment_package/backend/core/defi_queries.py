"""
GraphQL Queries for DeFi Operations
Serves live yield data from DefiLlama (cached in Redis/Postgres),
user positions, and AI-optimized portfolio allocations.
"""
import graphene
import logging
try:
    from graphql_jwt.decorators import login_required
except ImportError:  # Optional dependency in dev
    def login_required(func):
        return func
from graphql import GraphQLError
from graphene.types import JSONString
from .autopilot_types import (
    FinancialIntegrityType,
    AutopilotStatusType,
    AutopilotPolicyType,
    RepairActionType,
    RepairProofType,
    RepairOptionType,
    RepairOptionVariant,
    LastMoveType,
)

logger = logging.getLogger(__name__)


def _build_yield_audit(yield_item: dict):
    """Attempt to build a Risk Guardian audit payload for a yield item."""
    try:
        from .defi_models import DeFiPool
        from .risk_scoring_service import audit_vault, build_nav_from_apy_series

        pool = None
        pool_id = yield_item.get('id')
        pool_address = yield_item.get('poolAddress')

        if pool_id:
            pool = DeFiPool.objects.filter(defi_llama_pool_id=pool_id, is_active=True).first()
        if not pool and pool_address:
            pool = DeFiPool.objects.filter(pool_address=pool_address, is_active=True).first()

        if not pool:
            return None

        snapshots = list(pool.yield_snapshots.order_by('-timestamp')[:2000])
        if not snapshots:
            return None

        daily = {}
        for snap in snapshots:
            day = snap.timestamp.date()
            if day not in daily:
                daily[day] = snap

        if len(daily) < 7:
            return None

        ordered_days = sorted(daily.keys())
        apy_series = [float(daily[day].apy_total) for day in ordered_days]
        tvl_series = [float(daily[day].tvl_usd) for day in ordered_days]
        nav_history = build_nav_from_apy_series(apy_series)

        protocol_name = ''
        if pool.protocol:
            protocol_name = pool.protocol.slug or pool.protocol.name

        audit = audit_vault(
            vault_address=pool.pool_address or str(pool.id),
            protocol=protocol_name,
            symbol=pool.symbol,
            apy=apy_series[-1] if apy_series else 0.0,
            nav_history=nav_history,
            tvl_history=tvl_series,
            is_erc4626_compliant=pool.pool_type in ('vault', 'yield'),
        )

        return {
            'vaultAddress': audit.vault_address,
            'protocol': audit.protocol,
            'symbol': audit.symbol,
            'apy': audit.apy,
            'integrity': {
                'altmanZScore': audit.integrity.altman_z_score,
                'beneishMScore': audit.integrity.beneish_m_score,
                'isErc4626Compliant': audit.integrity.is_erc4626_compliant,
            },
            'risk': {
                'calmarRatio': audit.risk.calmar_ratio,
                'maxDrawdown': audit.risk.max_drawdown,
                'volatility': audit.risk.volatility,
                'tvlStability': audit.risk.tvl_stability,
            },
            'overallScore': audit.overall_score,
            'recommendation': audit.recommendation.value,
            'explanation': audit.explanation,
        }
    except Exception as e:
        logger.warning(f"Yield audit build error (non-blocking): {e}")
        return None


class AchievementType(graphene.ObjectType):
    """DeFi achievement/badge"""
    id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    icon = graphene.String()
    color = graphene.String()
    category = graphene.String()
    earned = graphene.Boolean()
    earned_at = graphene.String()
    progress = graphene.Float()


class PortfolioAnalyticsType(graphene.ObjectType):
    """DeFi portfolio analytics dashboard"""
    total_deposited_usd = graphene.Float()
    total_rewards_usd = graphene.Float()
    total_positions = graphene.Int()
    active_chains = graphene.List(graphene.String)
    active_protocols = graphene.List(graphene.String)
    realized_apy = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown_estimate = graphene.Float()
    portfolio_diversity_score = graphene.Float()


class GhostWhisperType(graphene.ObjectType):
    """Ghost Whisper DeFi — AI recommendation"""
    message = graphene.String()
    action = graphene.String()
    confidence = graphene.Float()
    reasoning = graphene.String()
    suggested_pool = JSONString()


class RiskMetricsType(graphene.ObjectType):
    """Risk metrics for a vault"""
    calmar_ratio = graphene.Float()
    max_drawdown = graphene.Float()
    volatility = graphene.Float()
    tvl_stability = graphene.Float()


class FortressAlternativeType(graphene.ObjectType):
    """Best Fortress-grade vault for an asset (getFortressAlternative query)."""
    id = graphene.String()
    protocol = graphene.String()
    chain = graphene.String()
    symbol = graphene.String()
    pool_address = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    overall_score = graphene.Float()
    recommendation = graphene.String()
    explanation = graphene.String()
    integrity = graphene.Field(FinancialIntegrityType)
    risk_metrics = graphene.Field(RiskMetricsType)


class VaultAuditType(graphene.ObjectType):
    """Risk Guardian audit for a vault"""
    vault_address = graphene.String()
    protocol = graphene.String()
    symbol = graphene.String()
    apy = graphene.Float()
    integrity = graphene.Field(FinancialIntegrityType)
    risk = graphene.Field(RiskMetricsType)
    overall_score = graphene.Float()
    recommendation = graphene.String()
    explanation = graphene.String()


class DefiReserveType(graphene.ObjectType):
    """DeFi reserve information"""
    symbol = graphene.String()
    name = graphene.String()
    ltv = graphene.Float()  # Loan-to-value ratio
    liquidation_threshold = graphene.Float()
    can_be_collateral = graphene.Boolean()
    supply_apy = graphene.Float()
    variable_borrow_apy = graphene.Float()
    stable_borrow_apy = graphene.Float()


class SupplyPositionType(graphene.ObjectType):
    """Supply position summary"""
    symbol = graphene.String()
    quantity = graphene.Float()
    use_as_collateral = graphene.Boolean()


class BorrowPositionType(graphene.ObjectType):
    """Borrow position summary"""
    symbol = graphene.String()
    amount = graphene.Float()
    rate_mode = graphene.String()


class DeFiProtocolInfoType(graphene.ObjectType):
    """Protocol metadata"""
    name = graphene.String()
    slug = graphene.String()


class DeFiChainInfoType(graphene.ObjectType):
    """Chain metadata"""
    name = graphene.String()
    chain_id = graphene.Int()


class DeFiPoolSummaryType(graphene.ObjectType):
    """Pool summary for positions"""
    id = graphene.String()
    protocol = graphene.Field(DeFiProtocolInfoType)
    chain = graphene.Field(DeFiChainInfoType)
    symbol = graphene.String()
    total_apy = graphene.Float()
    risk_score = graphene.Float()


class DeFiPositionSummaryType(graphene.ObjectType):
    """Position summary for vault portfolio views"""
    id = graphene.String()
    pool_name = graphene.String()
    pool_symbol = graphene.String()
    protocol = graphene.String()
    chain = graphene.String()
    staked_amount = graphene.Float()
    staked_value_usd = graphene.Float()
    current_apy = graphene.Float()
    rewards_earned = graphene.Float()
    health_factor = graphene.Float()
    health_status = graphene.String(description='green | amber | red')
    health_reason = graphene.String()
    is_active = graphene.Boolean()


class DefiAccountType(graphene.ObjectType):
    """DeFi account information"""
    health_factor = graphene.Float()
    available_borrow_usd = graphene.Float()
    collateral_usd = graphene.Float()
    debt_usd = graphene.Float()
    ltv_weighted = graphene.Float()
    liq_threshold_weighted = graphene.Float()
    supplies = graphene.List(SupplyPositionType)
    borrows = graphene.List(BorrowPositionType)
    prices_usd = JSONString
    total_value_usd = graphene.Float()
    total_earnings_usd = graphene.Float()
    positions = graphene.List(DeFiPositionSummaryType)


class UserDeFiPositionType(graphene.ObjectType):
    """User DeFi position for MyDeFiPositions query"""
    id = graphene.String()
    staked_lp = graphene.Float()
    rewards_earned = graphene.Float()
    realized_apy = graphene.Float()
    total_value_usd = graphene.Float()
    is_active = graphene.Boolean()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    pool = graphene.Field(DeFiPoolSummaryType)


class DefiQueries(graphene.ObjectType):
    """DeFi queries - powered by live DefiLlama data"""

    defi_reserves = graphene.List(DefiReserveType)
    defi_account = graphene.Field(DefiAccountType, walletAddress=graphene.String(required=False))
    my_de_fi_positions = graphene.List(UserDeFiPositionType)
    myDeFiPositions = graphene.List(UserDeFiPositionType)

    vault_audit = graphene.Field(
        VaultAuditType,
        poolId=graphene.String(required=True),
        description="Get Risk Guardian audit for a specific pool"
    )
    auditVault = graphene.Field(
        VaultAuditType,
        poolId=graphene.String(required=True),
        description="Get Risk Guardian audit for a pool (camelCase alias)"
    )

    fortress_alternative = graphene.List(
        FortressAlternativeType,
        asset=graphene.String(required=True),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Best Fortress-grade vault(s) for the given asset (e.g. USDC)"
    )
    fortressAlternative = graphene.List(
        FortressAlternativeType,
        asset=graphene.String(required=True),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Best Fortress-grade vault(s) (camelCase alias)"
    )

    spend_permission_typed_data = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        maxAmountWei=graphene.String(required=True),
        tokenAddress=graphene.String(required=True),
        validUntilSeconds=graphene.Int(required=True),
        nonce=graphene.String(required=True),
        description="EIP-712 typed data for signing spend permission (eth_signTypedData_v4)",
    )
    spendPermissionTypedData = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        maxAmountWei=graphene.String(required=True),
        tokenAddress=graphene.String(required=True),
        validUntilSeconds=graphene.Int(required=True),
        nonce=graphene.String(required=True),
        description="EIP-712 typed data (camelCase alias)",
    )

    repair_authorization_typed_data = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        fromVault=graphene.String(required=True),
        toVault=graphene.String(required=True),
        amountWei=graphene.String(required=True),
        deadline=graphene.Int(required=True),
        nonce=graphene.Int(required=True),
        description="EIP-712 typed data for RepairForwarder (relayer flow)",
    )
    repairAuthorizationTypedData = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        fromVault=graphene.String(required=True),
        toVault=graphene.String(required=True),
        amountWei=graphene.String(required=True),
        deadline=graphene.Int(required=True),
        nonce=graphene.Int(required=True),
        description="EIP-712 typed data (camelCase alias)",
    )

    session_authorization_typed_data = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        sessionId=graphene.String(required=True),
        walletAddress=graphene.String(required=True),
        maxAmountWei=graphene.String(required=True),
        validUntilSeconds=graphene.Int(required=True),
        nonce=graphene.String(required=True),
        description="EIP-712 typed data for session key (session can request repairs within bounds)",
    )
    sessionAuthorizationTypedData = graphene.Field(
        graphene.JSONString,
        chainId=graphene.Int(required=True),
        sessionId=graphene.String(required=True),
        walletAddress=graphene.String(required=True),
        maxAmountWei=graphene.String(required=True),
        validUntilSeconds=graphene.Int(required=True),
        nonce=graphene.String(required=True),
        description="EIP-712 typed data (camelCase alias)",
    )

    repair_forwarder_nonce = graphene.Field(
        graphene.Int,
        chainId=graphene.Int(required=True),
        userAddress=graphene.String(required=True),
        description="Current nonce for user on RepairForwarder (for relayer flow)",
    )
    repairForwarderNonce = graphene.Field(
        graphene.Int,
        chainId=graphene.Int(required=True),
        userAddress=graphene.String(required=True),
        description="Current nonce (camelCase alias)",
    )

    autopilot_status = graphene.Field(
        AutopilotStatusType,
        description="Get Auto-Pilot status and policy"
    )
    autopilotStatus = graphene.Field(
        AutopilotStatusType,
        description="Get Auto-Pilot status and policy (camelCase alias)"
    )

    pending_repairs = graphene.List(
        RepairActionType,
        description="Get pending Auto-Pilot repair actions"
    )
    pendingRepairs = graphene.List(
        RepairActionType,
        description="Get pending Auto-Pilot repair actions (camelCase alias)"
    )

    user_alerts = graphene.List(
        'core.autopilot_types.DeFiAlertType',
        limit=graphene.Int(default_value=20),
        description="Get user's DeFi alerts for notification center",
    )
    userAlerts = graphene.List(
        'core.autopilot_types.DeFiAlertType',
        limit=graphene.Int(default_value=20),
        description="Get user's DeFi alerts (camelCase alias)",
    )

    @login_required
    def resolve_defi_reserves(self, info):
        """Get available DeFi reserves (AAVE, etc.)"""
        # Fetch lending-specific reserves from cached yield data
        try:
            from .defi_data_service import get_cached_yields
            yields = get_cached_yields(chain='all', limit=50)

            reserves = []
            seen_symbols = set()
            for y in yields:
                symbol = y.get('symbol', '')
                # Only show simple lending assets (not LP pairs)
                if '/' in symbol or '-' in symbol:
                    continue
                if symbol in seen_symbols:
                    continue
                seen_symbols.add(symbol)

                reserves.append(DefiReserveType(
                    symbol=symbol,
                    name=symbol,
                    ltv=0.75 if symbol in ('USDC', 'USDT', 'DAI') else 0.70,
                    liquidation_threshold=0.82 if symbol in ('USDC', 'USDT', 'DAI') else 0.78,
                    can_be_collateral=True,
                    supply_apy=y.get('apy', 0) / 100,  # Convert % to decimal
                    variable_borrow_apy=(y.get('apy', 0) + 2.0) / 100,
                    stable_borrow_apy=(y.get('apy', 0) + 1.5) / 100,
                ))

            if reserves:
                return reserves
        except Exception as e:
            logger.warning(f"Could not fetch live reserves, using defaults: {e}")

        # Fallback if no live data available yet
        return [
            DefiReserveType(
                symbol='USDC', name='USD Coin', ltv=0.8,
                liquidation_threshold=0.85, can_be_collateral=True,
                supply_apy=0.02, variable_borrow_apy=0.04, stable_borrow_apy=0.03
            ),
            DefiReserveType(
                symbol='ETH', name='Ethereum', ltv=0.75,
                liquidation_threshold=0.80, can_be_collateral=True,
                supply_apy=0.01, variable_borrow_apy=0.05, stable_borrow_apy=0.04
            ),
        ]

    @login_required
    def resolve_defi_account(self, info, walletAddress=None):
        """Get user's DeFi account information"""
        user = info.context.user

        # Check for active positions in database
        try:
            from .defi_models import UserDeFiPosition
            from .defi_models import DeFiTransaction
            positions = UserDeFiPosition.objects.filter(
                user=user, is_active=True
            ).select_related('pool', 'pool__protocol')

            if walletAddress and walletAddress != 'not_connected':
                positions = positions.filter(wallet_address=walletAddress)

            if positions.exists():
                total_value = sum(float(p.staked_value_usd) for p in positions)
                total_rewards = sum(float(p.rewards_earned) for p in positions)

                borrows = DeFiTransaction.objects.filter(
                    user=user,
                    action='borrow',
                    status='confirmed',
                ).select_related('pool')
                repays = DeFiTransaction.objects.filter(
                    user=user,
                    action='repay',
                    status='confirmed',
                ).select_related('pool')

                total_borrowed = sum(float(b.amount_usd) for b in borrows)
                total_repaid = sum(float(r.amount_usd) for r in repays)
                debt_usd = max(0.0, total_borrowed - total_repaid)

                # Estimate health factor
                health_factor = 0.0
                if total_value > 0 and debt_usd > 0:
                    health_factor = (total_value * 0.80) / max(debt_usd, 0.01)
                elif total_value > 0 and debt_usd == 0:
                    health_factor = 999.0

                supplies = [
                    SupplyPositionType(
                        symbol=p.pool.symbol,
                        quantity=float(p.staked_amount),
                        use_as_collateral=True,
                    )
                    for p in positions
                ]

                borrow_map = {}
                for b in borrows:
                    symbol = b.pool.symbol if b.pool else 'UNKNOWN'
                    borrow_map[symbol] = borrow_map.get(symbol, 0) + float(b.amount_usd)
                for r in repays:
                    symbol = r.pool.symbol if r.pool else 'UNKNOWN'
                    borrow_map[symbol] = borrow_map.get(symbol, 0) - float(r.amount_usd)

                borrows_list = []
                for symbol, amt in borrow_map.items():
                    if amt <= 0:
                        continue
                    borrows_list.append(
                        BorrowPositionType(
                            symbol=symbol,
                            amount=amt,
                            rate_mode='VARIABLE',
                        )
                    )

                positions_summary = []
                try:
                    from .defi_data_service import get_position_health
                except ImportError:
                    get_position_health = None
                for p in positions:
                    latest = p.pool.yield_snapshots.order_by('-timestamp').first() if p.pool else None
                    pool_name = ''
                    if p.pool and p.pool.protocol:
                        pool_name = f"{p.pool.protocol.name} {p.pool.symbol}"
                    elif p.pool:
                        pool_name = p.pool.symbol
                    health_status = 'green'
                    health_reason = ''
                    if get_position_health and p.pool:
                        try:
                            health = get_position_health(p.pool.id)
                            health_status = health.get('status', 'green')
                            health_reason = health.get('reason', '') or ''
                        except Exception:
                            pass
                    positions_summary.append(
                        DeFiPositionSummaryType(
                            id=str(p.id),
                            pool_name=pool_name,
                            pool_symbol=p.pool.symbol if p.pool else '',
                            protocol=p.pool.protocol.name if p.pool and p.pool.protocol else '',
                            chain=p.pool.chain if p.pool else '',
                            staked_amount=float(p.staked_amount),
                            staked_value_usd=float(p.staked_value_usd),
                            current_apy=float(latest.apy_total) if latest else 0.0,
                            rewards_earned=float(p.rewards_earned),
                            health_factor=health_factor,
                            health_status=health_status,
                            health_reason=health_reason,
                            is_active=p.is_active,
                        )
                    )

                return DefiAccountType(
                    health_factor=health_factor,
                    available_borrow_usd=max(0.0, (total_value * 0.5) - debt_usd),
                    collateral_usd=total_value,
                    debt_usd=debt_usd,
                    ltv_weighted=0.50 if total_value > 0 else 0.0,
                    liq_threshold_weighted=0.80 if total_value > 0 else 0.0,
                    supplies=supplies,
                    borrows=borrows_list,
                    prices_usd={},
                    total_value_usd=total_value,
                    total_earnings_usd=total_rewards,
                    positions=positions_summary,
                )
        except Exception as e:
            logger.warning(f"Could not fetch user DeFi positions: {e}")

        # Default for users with no positions
        return DefiAccountType(
            health_factor=0, available_borrow_usd=0,
            collateral_usd=0, debt_usd=0,
            ltv_weighted=0, liq_threshold_weighted=0,
            supplies=[], borrows=[], prices_usd={},
            total_value_usd=0, total_earnings_usd=0, positions=[]
        )

    @login_required
    def resolve_my_de_fi_positions(self, info):
        user = info.context.user
        try:
            from .defi_models import UserDeFiPosition

            positions = UserDeFiPosition.objects.filter(user=user).select_related('pool', 'pool__protocol')
            results = []
            for p in positions:
                latest = p.pool.yield_snapshots.order_by('-timestamp').first() if p.pool else None
                protocol = DeFiProtocolInfoType(
                    name=p.pool.protocol.name if p.pool and p.pool.protocol else '',
                    slug=p.pool.protocol.slug if p.pool and p.pool.protocol else '',
                )
                chain = DeFiChainInfoType(
                    name=p.pool.chain if p.pool else '',
                    chain_id=p.pool.chain_id if p.pool else 0,
                )
                pool = DeFiPoolSummaryType(
                    id=str(p.pool.id) if p.pool else '',
                    protocol=protocol,
                    chain=chain,
                    symbol=p.pool.symbol if p.pool else '',
                    total_apy=float(latest.apy_total) if latest else 0.0,
                    risk_score=float(latest.risk_score) if latest else 0.0,
                )
                results.append(
                    UserDeFiPositionType(
                        id=str(p.id),
                        staked_lp=float(p.staked_amount),
                        rewards_earned=float(p.rewards_earned),
                        realized_apy=p.realized_apy,
                        total_value_usd=float(p.total_value_usd),
                        is_active=p.is_active,
                        created_at=p.created_at,
                        updated_at=p.updated_at,
                        pool=pool,
                    )
                )
            return results
        except Exception as e:
            logger.warning(f"Could not fetch MyDeFiPositions: {e}")
            return []

    def resolve_myDeFiPositions(self, info):
        return DefiQueries.resolve_my_de_fi_positions(self, info)

    @login_required
    def resolve_vault_audit(self, info, poolId):
        """Compute and return a Risk Guardian audit for a pool."""
        try:
            from .defi_models import DeFiPool
            from .risk_scoring_service import audit_vault, build_nav_from_apy_series

            pool = DeFiPool.objects.filter(id=poolId, is_active=True).first()
            if not pool:
                raise GraphQLError(f"Pool {poolId} not found or inactive.")

            snapshots = list(pool.yield_snapshots.order_by('-timestamp')[:2000])
            if not snapshots:
                raise GraphQLError("Insufficient historical data for audit.")

            daily = {}
            for snap in snapshots:
                day = snap.timestamp.date()
                if day not in daily:
                    daily[day] = snap

            if len(daily) < 7:
                raise GraphQLError("Insufficient historical data for audit.")

            ordered_days = sorted(daily.keys())
            apy_series = [float(daily[day].apy_total) for day in ordered_days]
            tvl_series = [float(daily[day].tvl_usd) for day in ordered_days]

            nav_history = build_nav_from_apy_series(apy_series)
            current_apy = apy_series[-1] if apy_series else 0.0

            protocol_name = ''
            if pool.protocol:
                protocol_name = pool.protocol.slug or pool.protocol.name

            audit = audit_vault(
                vault_address=pool.pool_address or str(pool.id),
                protocol=protocol_name,
                symbol=pool.symbol,
                apy=current_apy,
                nav_history=nav_history,
                tvl_history=tvl_series,
                is_erc4626_compliant=pool.pool_type in ('vault', 'yield'),
            )

            return VaultAuditType(
                vault_address=audit.vault_address,
                protocol=audit.protocol,
                symbol=audit.symbol,
                apy=audit.apy,
                integrity=FinancialIntegrityType(
                    altman_z_score=audit.integrity.altman_z_score,
                    beneish_m_score=audit.integrity.beneish_m_score,
                    is_erc4626_compliant=audit.integrity.is_erc4626_compliant,
                ),
                risk=RiskMetricsType(
                    calmar_ratio=audit.risk.calmar_ratio,
                    max_drawdown=audit.risk.max_drawdown,
                    volatility=audit.risk.volatility,
                    tvl_stability=audit.risk.tvl_stability,
                ),
                overall_score=audit.overall_score,
                recommendation=audit.recommendation.value,
                explanation=audit.explanation,
            )
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Vault audit error: {e}")
            raise GraphQLError("Unable to compute vault audit.")

    def resolve_auditVault(self, info, poolId):
        return DefiQueries.resolve_vault_audit(self, info, poolId)

    @login_required
    def resolve_fortress_alternative(self, info, asset, chain='all', limit=5):
        """Best Fortress-grade vault(s) for the given asset."""
        try:
            from .defi_data_service import get_fortress_alternative
            rows = get_fortress_alternative(asset=asset, chain=chain or 'all', limit=limit or 5)
            out = []
            for r in rows:
                integrity = r.get('integrity') or {}
                risk = r.get('riskMetrics') or {}
                out.append(FortressAlternativeType(
                    id=r.get('id', ''),
                    protocol=r.get('protocol', ''),
                    chain=r.get('chain', ''),
                    symbol=r.get('symbol', ''),
                    pool_address=r.get('poolAddress', ''),
                    apy=r.get('apy', 0),
                    tvl=r.get('tvl', 0),
                    overall_score=r.get('overallScore', 0),
                    recommendation=r.get('recommendation', ''),
                    explanation=r.get('explanation', ''),
                    integrity=FinancialIntegrityType(
                        altman_z_score=integrity.get('altmanZScore'),
                        beneish_m_score=integrity.get('beneishMScore'),
                        is_erc4626_compliant=integrity.get('isErc4626Compliant', False),
                    ),
                    risk_metrics=RiskMetricsType(
                        calmar_ratio=risk.get('calmarRatio'),
                        max_drawdown=risk.get('maxDrawdown'),
                        volatility=risk.get('volatility'),
                        tvl_stability=risk.get('tvlStability'),
                    ),
                ))
            return out
        except Exception as e:
            logger.warning(f"fortress_alternative error: {e}")
            return []

    def resolve_fortressAlternative(self, info, asset, chain='all', limit=5):
        return DefiQueries.resolve_fortress_alternative(self, info, asset, chain, limit)

    @login_required
    def resolve_spend_permission_typed_data(
        self, info, chainId, maxAmountWei, tokenAddress, validUntilSeconds, nonce
    ):
        """Return EIP-712 typed data for the client to sign (eth_signTypedData_v4)."""
        try:
            from .eip712_spend_permission import get_spend_permission_typed_data
            return get_spend_permission_typed_data(
                chain_id=chainId,
                max_amount_wei=maxAmountWei,
                token_address=tokenAddress,
                valid_until_seconds=validUntilSeconds,
                nonce=nonce,
            )
        except Exception as e:
            logger.warning(f"spend_permission_typed_data error: {e}")
            return None

    def resolve_spendPermissionTypedData(
        self, info, chainId, maxAmountWei, tokenAddress, validUntilSeconds, nonce
    ):
        return DefiQueries.resolve_spend_permission_typed_data(
            self, info, chainId, maxAmountWei, tokenAddress, validUntilSeconds, nonce
        )

    @login_required
    def resolve_repair_authorization_typed_data(
        self, info, chainId, fromVault, toVault, amountWei, deadline, nonce
    ):
        try:
            from .eip712_repair_authorization import get_repair_authorization_typed_data
            return get_repair_authorization_typed_data(
                from_vault=fromVault,
                to_vault=toVault,
                amount_wei=amountWei,
                deadline=deadline,
                nonce=nonce,
                chain_id=chainId,
            )
        except Exception as e:
            logger.warning(f"repair_authorization_typed_data error: {e}")
            return None

    def resolve_repairAuthorizationTypedData(
        self, info, chainId, fromVault, toVault, amountWei, deadline, nonce
    ):
        return DefiQueries.resolve_repair_authorization_typed_data(
            self, info, chainId, fromVault, toVault, amountWei, deadline, nonce
        )

    @login_required
    def resolve_session_authorization_typed_data(
        self, info, chainId, sessionId, walletAddress, maxAmountWei, validUntilSeconds, nonce
    ):
        try:
            from .eip712_session_authorization import get_session_authorization_typed_data
            return get_session_authorization_typed_data(
                session_id=sessionId,
                wallet_address=walletAddress,
                chain_id=chainId,
                max_amount_wei=maxAmountWei,
                valid_until=validUntilSeconds,
                nonce=nonce,
            )
        except Exception as e:
            logger.warning(f"session_authorization_typed_data error: {e}")
            return None

    def resolve_sessionAuthorizationTypedData(
        self, info, chainId, sessionId, walletAddress, maxAmountWei, validUntilSeconds, nonce
    ):
        return DefiQueries.resolve_session_authorization_typed_data(
            self, info, chainId, sessionId, walletAddress, maxAmountWei, validUntilSeconds, nonce
        )

    def resolve_repair_forwarder_nonce(self, info, chainId, userAddress):
        from .repair_relayer import get_forwarder_nonce
        return get_forwarder_nonce(chainId, userAddress)

    def resolve_repairForwarderNonce(self, info, chainId, userAddress):
        return DefiQueries.resolve_repair_forwarder_nonce(self, info, chainId, userAddress)

    @login_required
    def resolve_autopilot_status(self, info):
        from .autopilot_service import get_autopilot_status
        from .repair_relayer import is_relayer_configured

        status = get_autopilot_status(info.context.user)
        policy = status.get('policy') or {}
        last_move = status.get('last_move') or {}
        return AutopilotStatusType(
            enabled=bool(status.get('enabled')),
            last_evaluated_at=status.get('last_evaluated_at'),
            relayer_configured=is_relayer_configured(),
            policy=AutopilotPolicyType(
                target_apy=policy.get('target_apy'),
                max_drawdown=policy.get('max_drawdown'),
                risk_level=policy.get('risk_level'),
                level=policy.get('level'),
                spend_limit_24h=policy.get('spend_limit_24h'),
                spend_permission_enabled=policy.get('spend_permission_enabled'),
                spend_permission_expires_at=policy.get('spend_permission_expires_at'),
                orchestration_mode=policy.get('orchestration_mode'),
            ),
            last_move=LastMoveType(
                id=last_move.get('id'),
                from_vault=last_move.get('from_vault'),
                to_vault=last_move.get('to_vault'),
                executed_at=last_move.get('executed_at'),
                can_revert=last_move.get('can_revert'),
                revert_deadline=last_move.get('revert_deadline'),
            ) if last_move else None,
        )

    def resolve_autopilotStatus(self, info):
        return DefiQueries.resolve_autopilot_status(self, info)

    @login_required
    def resolve_pending_repairs(self, info):
        from .autopilot_service import get_pending_repairs

        repairs = get_pending_repairs(info.context.user)
        result = []
        for r in repairs:
            opt_list = r.get('options') or []
            options = [
                RepairOptionType(
                    variant=opt.get('variant', 'BALANCED'),
                    to_vault=opt.get('to_vault', ''),
                    to_pool_id=opt.get('to_pool_id', ''),
                    estimated_apy_delta=opt.get('estimated_apy_delta'),
                    proof=RepairProofType(
                        calmar_improvement=(opt.get('proof') or {}).get('calmar_improvement'),
                        integrity_check=FinancialIntegrityType(
                            altman_z_score=((opt.get('proof') or {}).get('integrity_check') or {}).get('altman_z_score'),
                            beneish_m_score=((opt.get('proof') or {}).get('integrity_check') or {}).get('beneish_m_score'),
                            is_erc4626_compliant=((opt.get('proof') or {}).get('integrity_check') or {}).get('is_erc4626_compliant'),
                        ),
                        tvl_stability_check=(opt.get('proof') or {}).get('tvl_stability_check'),
                        policy_alignment=(opt.get('proof') or {}).get('policy_alignment'),
                        explanation=(opt.get('proof') or {}).get('explanation'),
                        policy_version=(opt.get('proof') or {}).get('policy_version'),
                        guardrails=(opt.get('proof') or {}).get('guardrails'),
                    ),
                )
                for opt in opt_list
            ]
            result.append(RepairActionType(
                id=r['id'],
                from_vault=r['from_vault'],
                to_vault=r['to_vault'],
                estimated_apy_delta=r.get('estimated_apy_delta'),
                gas_estimate=r.get('gas_estimate'),
                source=r.get('source'),
                from_pool_id=r.get('from_pool_id'),
                to_pool_id=r.get('to_pool_id'),
                execution_plan=r.get('execution_plan'),
                agent_trace=r.get('agent_trace'),
                options=options,
                proof=RepairProofType(
                    calmar_improvement=r['proof'].get('calmar_improvement'),
                    integrity_check=FinancialIntegrityType(
                        altman_z_score=r['proof']['integrity_check'].get('altman_z_score'),
                        beneish_m_score=r['proof']['integrity_check'].get('beneish_m_score'),
                        is_erc4626_compliant=r['proof']['integrity_check'].get('is_erc4626_compliant'),
                    ),
                    tvl_stability_check=r['proof'].get('tvl_stability_check'),
                    policy_alignment=r['proof'].get('policy_alignment'),
                    explanation=r['proof'].get('explanation'),
                    policy_version=r['proof'].get('policy_version'),
                    guardrails=r['proof'].get('guardrails'),
                ),
            ))
        return result

    def resolve_pendingRepairs(self, info):
        return DefiQueries.resolve_pending_repairs(self, info)

    @login_required
    def resolve_user_alerts(self, info, limit=20):
        from .defi_alert_service import get_user_alerts
        from .autopilot_types import DeFiAlertType

        alerts = get_user_alerts(info.context.user, limit=limit)
        return [
            DeFiAlertType(
                id=a['id'],
                alert_type=a['alert_type'],
                severity=a['severity'],
                title=a['title'],
                message=a['message'],
                data=a['data'],
                repair_id=a.get('repair_id'),
                is_read=a['is_read'],
                is_dismissed=a['is_dismissed'],
                created_at=a['created_at'],
            )
            for a in alerts
        ]

    def resolve_userAlerts(self, info, limit=20):
        return DefiQueries.resolve_user_alerts(self, info, limit)

    # ---- Yield queries (powered by DefiLlama) ----

    top_yields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        chain=graphene.String(),
        limit=graphene.Int(),
        minCalmar=graphene.Float(),
        description="Get top yield opportunities from live DefiLlama data; optional minCalmar filters to Fortress-grade"
    )
    topYields = graphene.List(
        'core.defi_mutations.YieldPoolType',
        chain=graphene.String(),
        limit=graphene.Int(),
        minCalmar=graphene.Float(),
        description="Get top yield opportunities (camelCase alias)"
    )

    ai_yield_optimizer = graphene.Field(
        'core.defi_mutations.YieldOptimizerResultType',
        userRiskTolerance=graphene.Float(),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Get AI-optimized yield portfolio"
    )
    aiYieldOptimizer = graphene.Field(
        'core.defi_mutations.YieldOptimizerResultType',
        userRiskTolerance=graphene.Float(),
        chain=graphene.String(),
        limit=graphene.Int(),
        description="Get AI-optimized yield portfolio (camelCase alias)"
    )

    pool_analytics = graphene.List(
        'core.defi_mutations.PoolAnalyticsPointType',
        poolId=graphene.String(required=True),
        days=graphene.Int(),
        description="Get pool analytics data"
    )
    poolAnalytics = graphene.List(
        'core.defi_mutations.PoolAnalyticsPointType',
        poolId=graphene.String(required=True),
        days=graphene.Int(),
        description="Get pool analytics data (camelCase alias)"
    )

    @login_required
    def resolve_top_yields(self, info, chain='all', limit=20, minCalmar=None):
        """Get top yield opportunities from live DefiLlama data; optional minCalmar filters to Fortress-grade."""
        from .defi_mutations import YieldPoolType

        try:
            from .defi_data_service import get_cached_yields
            fetch_limit = limit * 3 if minCalmar is not None else limit
            yields = get_cached_yields(chain=chain or 'all', limit=fetch_limit)

            if yields:
                built = []
                for y in yields:
                    audit = _build_yield_audit(y)
                    if minCalmar is not None and audit is not None:
                        calmar = (audit.get('risk') or {}).get('calmarRatio')
                        if calmar is None or calmar < minCalmar:
                            continue
                    built.append(YieldPoolType(
                        id=y.get('id', ''),
                        protocol=y.get('protocol', ''),
                        chain=y.get('chain', ''),
                        symbol=y.get('symbol', ''),
                        poolAddress=y.get('poolAddress', ''),
                        apy=y.get('apy', 0),
                        tvl=y.get('tvl', 0),
                        risk=y.get('risk', 0.5),
                        audit=audit,
                    ))
                return built[:limit]
        except Exception as e:
            logger.warning(f"Could not fetch live yields, using fallback: {e}")

        # Fallback if DefiLlama data not yet loaded
        return [
            YieldPoolType(
                id="aave-v3-usdc", protocol="Aave V3", chain="ethereum",
                symbol="USDC", poolAddress="", apy=8.5, tvl=2500000000, risk=0.2,
                audit=None,
            )
        ][:limit]

    def resolve_topYields(self, info, chain='all', limit=20, minCalmar=None):
        """CamelCase alias for top_yields"""
        return DefiQueries.resolve_top_yields(self, info, chain, limit, minCalmar)

    @login_required
    def resolve_ai_yield_optimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """Get AI-optimized yield portfolio"""
        from .defi_mutations import YieldOptimizerResultType, OptimizedPoolType

        try:
            from .defi_data_service import get_ai_optimized_portfolio
            result = get_ai_optimized_portfolio(
                risk_tolerance=userRiskTolerance,
                chain=chain or 'ethereum',
                limit=limit,
            )

            allocations = [
                OptimizedPoolType(
                    id=a['id'],
                    protocol=a['protocol'],
                    apy=a['apy'],
                    tvl=a['tvl'],
                    risk=a['risk'],
                    symbol=a['symbol'],
                    chain=a['chain'],
                    weight=a['weight'],
                )
                for a in result.get('allocations', [])
            ]

            return YieldOptimizerResultType(
                expectedApy=result.get('expectedApy', 0),
                totalRisk=result.get('totalRisk', 0),
                explanation=result.get('explanation', ''),
                optimizationStatus=result.get('optimizationStatus', 'NO_DATA'),
                allocations=allocations,
            )
        except Exception as e:
            logger.warning(f"AI yield optimizer error, using fallback: {e}")

        # Fallback
        return YieldOptimizerResultType(
            expectedApy=0, totalRisk=0,
            explanation="Yield data is loading. Please try again in a moment.",
            optimizationStatus="LOADING", allocations=[]
        )

    def resolve_aiYieldOptimizer(self, info, userRiskTolerance=0.5, chain="ethereum", limit=8):
        """CamelCase alias for ai_yield_optimizer"""
        return DefiQueries.resolve_ai_yield_optimizer(self, info, userRiskTolerance, chain, limit)

    @login_required
    def resolve_pool_analytics(self, info, poolId, days=30):
        """Get pool analytics from historical yield snapshots"""
        from .defi_mutations import PoolAnalyticsPointType

        try:
            from .defi_data_service import get_pool_analytics
            analytics = get_pool_analytics(pool_id=poolId, days=days)

            if analytics:
                return [
                    PoolAnalyticsPointType(
                        date=a['date'],
                        feeApy=a['feeApy'],
                        ilEstimate=a['ilEstimate'],
                        netApy=a['netApy'],
                    )
                    for a in analytics
                ]
        except Exception as e:
            logger.warning(f"Pool analytics error: {e}")

        return []

    def resolve_poolAnalytics(self, info, poolId, days=30):
        """CamelCase alias for pool_analytics"""
        return DefiQueries.resolve_pool_analytics(self, info, poolId, days)

    # ---- Achievements ----

    defi_achievements = graphene.List(
        AchievementType,
        description="Get user's DeFi achievements and progress"
    )
    defiAchievements = graphene.List(
        AchievementType,
        description="Get user's DeFi achievements (camelCase alias)"
    )

    @login_required
    def resolve_defi_achievements(self, info):
        """Get user's DeFi achievement progress"""
        user = info.context.user
        try:
            from .defi_achievement_service import check_achievements
            achievements = check_achievements(user)
            return [
                AchievementType(
                    id=a['id'],
                    title=a['title'],
                    description=a['description'],
                    icon=a['icon'],
                    color=a['color'],
                    category=a.get('category', 'milestone'),
                    earned=a['earned'],
                    earned_at=str(a['earned_at']) if a.get('earned_at') else None,
                    progress=a['progress'],
                )
                for a in achievements
            ]
        except Exception as e:
            logger.warning(f"Could not fetch achievements: {e}")
            return []

    def resolve_defiAchievements(self, info):
        """CamelCase alias for defi_achievements"""
        return self.resolve_defi_achievements(info)

    # ---- Portfolio Analytics ----

    portfolio_analytics_summary = graphene.Field(
        PortfolioAnalyticsType,
        description="Get DeFi portfolio analytics (Sharpe ratio, diversity, drawdown)"
    )
    portfolioAnalytics = graphene.Field(
        PortfolioAnalyticsType,
        description="Get DeFi portfolio analytics (camelCase alias)"
    )

    @login_required
    def resolve_portfolio_analytics_summary(self, info):
        """Get comprehensive portfolio analytics"""
        user = info.context.user
        try:
            from .defi_achievement_service import get_portfolio_analytics
            analytics = get_portfolio_analytics(user)
            return PortfolioAnalyticsType(
                total_deposited_usd=analytics.get('total_deposited_usd', 0),
                total_rewards_usd=analytics.get('total_rewards_usd', 0),
                total_positions=analytics.get('total_positions', 0),
                active_chains=analytics.get('active_chains', []),
                active_protocols=analytics.get('active_protocols', []),
                realized_apy=analytics.get('realized_apy', 0),
                sharpe_ratio=analytics.get('sharpe_ratio', 0),
                max_drawdown_estimate=analytics.get('max_drawdown_estimate', 0),
                portfolio_diversity_score=analytics.get('portfolio_diversity_score', 0),
            )
        except Exception as e:
            logger.warning(f"Could not fetch portfolio analytics: {e}")
            return PortfolioAnalyticsType(
                total_deposited_usd=0, total_rewards_usd=0, total_positions=0,
                active_chains=[], active_protocols=[], realized_apy=0,
                sharpe_ratio=0, max_drawdown_estimate=0, portfolio_diversity_score=0,
            )

    def resolve_portfolioAnalytics(self, info):
        """CamelCase alias for portfolio_analytics_summary"""
        return self.resolve_portfolio_analytics_summary(info)

    # ---- Ghost Whisper DeFi (AI Recommendation) ----

    ghost_whisper = graphene.Field(
        GhostWhisperType,
        description="Get personalized Ghost Whisper DeFi recommendation"
    )
    ghostWhisper = graphene.Field(
        GhostWhisperType,
        description="Get Ghost Whisper recommendation (camelCase alias)"
    )

    @login_required
    def resolve_ghost_whisper(self, info):
        """Get personalized AI-driven DeFi recommendation"""
        user = info.context.user
        try:
            from .defi_achievement_service import get_ghost_whisper_recommendation
            rec = get_ghost_whisper_recommendation(user)
            return GhostWhisperType(
                message=rec.get('message', ''),
                action=rec.get('action', 'hold'),
                confidence=rec.get('confidence', 0),
                reasoning=rec.get('reasoning', ''),
                suggested_pool=rec.get('suggested_pool'),
            )
        except Exception as e:
            logger.warning(f"Ghost Whisper error: {e}")
            return GhostWhisperType(
                message="Your fortress awaits. Connect your wallet to begin.",
                action='deposit',
                confidence=0.5,
                reasoning='Unable to load personalized recommendation.',
                suggested_pool=None,
            )
