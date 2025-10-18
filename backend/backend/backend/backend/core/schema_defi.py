"""
GraphQL Schema for DeFi Yield Farming
Production-grade schema for non-custodial yield farming
"""
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from .models_defi import Chain, Protocol, Pool, FarmPosition, FarmAction
from .services.defi_service import fetch_top_yields, verify_transaction, get_supported_chains
from .services.ai_yield_optimizer import ai_optimize_yields, get_risk_metrics
from .performance_utils import resolver_timer

User = get_user_model()

# GraphQL Types
class ChainType(DjangoObjectType):
    class Meta:
        model = Chain
        fields = "__all__"

class ProtocolType(DjangoObjectType):
    class Meta:
        model = Protocol
        fields = "__all__"

class PoolType(DjangoObjectType):
    total_apy = graphene.Float()
    risk_score = graphene.Float()
    
    def resolve_total_apy(self, info):
        return self.total_apy
    
    def resolve_risk_score(self, info):
        return self.risk_score

    class Meta:
        model = Pool
        fields = "__all__"

class FarmPositionType(DjangoObjectType):
    total_value_usd = graphene.Float()
    
    def resolve_total_value_usd(self, info):
        return float(self.total_value_usd)

    class Meta:
        model = FarmPosition
        fields = "__all__"

class FarmActionType(DjangoObjectType):
    class Meta:
        model = FarmAction
        fields = "__all__"

class DeFiYieldType(graphene.ObjectType):
    """DeFiLlama yield data"""
    id = graphene.String()
    protocol = graphene.String()
    chain = graphene.String()
    symbol = graphene.String()
    pool_address = graphene.String()
    apy = graphene.Float()
    apy_base = graphene.Float()
    apy_reward = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.Float()
    audits = graphene.List(graphene.String)
    url = graphene.String()

class OptimizedPoolType(graphene.ObjectType):
    """AI-optimized pool allocation"""
    id = graphene.String()
    protocol = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.Float()
    symbol = graphene.String()
    chain = graphene.String()
    weight = graphene.Float()

class OptimizeYieldResultType(graphene.ObjectType):
    """AI optimization result"""
    allocations = graphene.List(OptimizedPoolType)
    expected_apy = graphene.Float()
    total_risk = graphene.Float()
    explanation = graphene.String()
    optimization_status = graphene.String()
    risk_metrics = graphene.JSONString()

class SupportedChainType(graphene.ObjectType):
    """Supported blockchain network"""
    chain_id = graphene.Int()
    name = graphene.String()
    slug = graphene.String()

# Queries
class DeFiQuery(graphene.ObjectType):
    """DeFi-related queries"""
    
    # Yield farming opportunities
    top_yields = graphene.List(
        DeFiYieldType,
        chain=graphene.String(default_value="ethereum"),
        limit=graphene.Int(default_value=10)
    )
    
    # AI yield optimizer
    ai_yield_optimizer = graphene.Field(
        OptimizeYieldResultType,
        user_risk_tolerance=graphene.Float(required=True),
        chain=graphene.String(default_value="ethereum"),
        limit=graphene.Int(default_value=8),
        max_per_pool=graphene.Float(default_value=0.6),
        min_tvl=graphene.Float(default_value=5000000),
        allowlist=graphene.List(graphene.String),
        denylist=graphene.List(graphene.String)
    )
    
    # User's farming positions
    my_defi_positions = graphene.List(FarmPositionType)
    
    # Supported chains
    supported_chains = graphene.List(SupportedChainType)
    
    # Pool details
    pool = graphene.Field(PoolType, id=graphene.ID(required=True))
    
    @resolver_timer("topYields")
    def resolve_top_yields(self, info, chain, limit):
        """Fetch top yield farming opportunities"""
        yields = fetch_top_yields(chain, limit)
        return [DeFiYieldType(**yield_data) for yield_data in yields]
    
    @resolver_timer("aiYieldOptimizer")
    def resolve_ai_yield_optimizer(self, info, user_risk_tolerance, chain, limit, max_per_pool, min_tvl, allowlist=None, denylist=None):
        """AI yield optimization"""
        result = ai_optimize_yields(
            user_risk=user_risk_tolerance,
            chain=chain,
            limit=limit,
            max_per_pool=max_per_pool,
            min_tvl=min_tvl,
            allowlist=allowlist,
            denylist=denylist
        )
        
        if "error" in result:
            return OptimizeYieldResultType(
                allocations=[],
                expected_apy=0.0,
                total_risk=user_risk_tolerance,
                explanation=result["error"],
                optimization_status="failed",
                risk_metrics={}
            )
        
        # Calculate additional risk metrics
        risk_metrics = get_risk_metrics(result.get("pools", []))
        
        return OptimizeYieldResultType(
            allocations=[OptimizedPoolType(**pool) for pool in result["pools"]],
            expected_apy=result["expected_apy"],
            total_risk=result["total_risk"],
            explanation=result["explanation"],
            optimization_status=result.get("optimization_status", "optimal"),
            risk_metrics=risk_metrics
        )
    
    def resolve_my_defi_positions(self, info):
        """Get user's farming positions"""
        user = info.context.user
        if not user or not user.is_authenticated:
            return []
        
        return FarmPosition.objects.filter(user=user, is_active=True).select_related('pool', 'pool__protocol', 'pool__chain')
    
    def resolve_supported_chains(self, info):
        """Get supported blockchain networks"""
        chains = get_supported_chains()
        return [SupportedChainType(**chain) for chain in chains]
    
    def resolve_pool(self, info, id):
        """Get pool details by ID"""
        try:
            return Pool.objects.get(id=id, is_active=True)
        except Pool.DoesNotExist:
            return None

# Mutations
class StakeIntentMutation(graphene.Mutation):
    """Create a staking intent (user signs transaction on frontend)"""
    
    class Arguments:
        pool_id = graphene.ID(required=True)
        wallet = graphene.String(required=True)
        amount = graphene.Float(required=True)
    
    ok = graphene.Boolean()
    message = graphene.String()
    pool = graphene.Field(PoolType)
    required_approvals = graphene.List(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, pool_id, wallet, amount):
        user = info.context.user
        if not user or not user.is_authenticated:
            return cls(ok=False, message="Authentication required")
        
        try:
            pool = Pool.objects.get(id=pool_id, is_active=True)
            
            # In a real implementation, you'd check if the user has sufficient balance
            # and return the required approval transactions
            
            return cls(
                ok=True,
                message="Sign the transaction in your wallet to complete staking",
                pool=pool,
                required_approvals=["approve", "stake"]  # Example approval steps
            )
            
        except Pool.DoesNotExist:
            return cls(ok=False, message="Pool not found")
        except Exception as e:
            return cls(ok=False, message=f"Error: {str(e)}")

class RecordStakeTransactionMutation(graphene.Mutation):
    """Record a completed staking transaction"""
    
    class Arguments:
        pool_id = graphene.ID(required=True)
        chain_id = graphene.Int(required=True)
        wallet = graphene.String(required=True)
        tx_hash = graphene.String(required=True)
        amount = graphene.Float(required=True)
    
    ok = graphene.Boolean()
    message = graphene.String()
    position = graphene.Field(FarmPositionType)
    action = graphene.Field(FarmActionType)
    
    @classmethod
    def mutate(cls, root, info, pool_id, chain_id, wallet, tx_hash, amount):
        user = info.context.user
        if not user or not user.is_authenticated:
            return cls(ok=False, message="Authentication required")
        
        try:
            pool = Pool.objects.get(id=pool_id, is_active=True)
            
            # Verify the transaction on-chain
            candidate_contracts = [
                pool.pool_address,
                pool.router_address,
                pool.gauge_address
            ]
            candidate_contracts = [c for c in candidate_contracts if c]  # Remove None values
            
            success, error, receipt = verify_transaction(
                chain_id, tx_hash, wallet, candidate_contracts
            )
            
            # Get or create position
            position, created = FarmPosition.objects.get_or_create(
                user=user,
                pool=pool,
                wallet=wallet,
                defaults={'staked_lp': 0}
            )
            
            # Create action record
            action = FarmAction.objects.create(
                position=position,
                tx_hash=tx_hash,
                action='STAKE',
                amount=amount,
                success=success,
                error=error or '',
                block_number=receipt.get('blockNumber') if receipt else None,
                gas_used=receipt.get('gasUsed') if receipt else None
            )
            
            if success:
                # Update position (in a real implementation, you'd decode the exact LP amount from logs)
                position.staked_lp += amount
                position.save()
                
                return cls(
                    ok=True,
                    message="Staking transaction recorded successfully",
                    position=position,
                    action=action
                )
            else:
                return cls(
                    ok=False,
                    message=f"Transaction verification failed: {error}",
                    position=position,
                    action=action
                )
                
        except Pool.DoesNotExist:
            return cls(ok=False, message="Pool not found")
        except Exception as e:
            return cls(ok=False, message=f"Error: {str(e)}")

class HarvestRewardsMutation(graphene.Mutation):
    """Harvest rewards from a farming position"""
    
    class Arguments:
        position_id = graphene.ID(required=True)
        tx_hash = graphene.String(required=True)
    
    ok = graphene.Boolean()
    message = graphene.String()
    action = graphene.Field(FarmActionType)
    
    @classmethod
    def mutate(cls, root, info, position_id, tx_hash):
        user = info.context.user
        if not user or not user.is_authenticated:
            return cls(ok=False, message="Authentication required")
        
        try:
            position = FarmPosition.objects.get(id=position_id, user=user, is_active=True)
            
            # Verify harvest transaction
            candidate_contracts = [
                position.pool.pool_address,
                position.pool.router_address,
                position.pool.gauge_address
            ]
            candidate_contracts = [c for c in candidate_contracts if c]
            
            success, error, receipt = verify_transaction(
                position.pool.chain.chain_id, tx_hash, position.wallet, candidate_contracts
            )
            
            # Create action record
            action = FarmAction.objects.create(
                position=position,
                tx_hash=tx_hash,
                action='HARVEST',
                success=success,
                error=error or '',
                block_number=receipt.get('blockNumber') if receipt else None
            )
            
            if success:
                # In a real implementation, you'd decode the exact reward amount from logs
                # For now, we'll just mark that rewards were harvested
                position.rewards_earned = 0  # Reset after harvest
                position.save()
                
                return cls(
                    ok=True,
                    message="Rewards harvested successfully",
                    action=action
                )
            else:
                return cls(
                    ok=False,
                    message=f"Harvest transaction verification failed: {error}",
                    action=action
                )
                
        except FarmPosition.DoesNotExist:
            return cls(ok=False, message="Position not found")
        except Exception as e:
            return cls(ok=False, message=f"Error: {str(e)}")

class DeFiMutation(graphene.ObjectType):
    """DeFi-related mutations"""
    stake_intent = StakeIntentMutation.Field()
    record_stake_transaction = RecordStakeTransactionMutation.Field()
    harvest_rewards = HarvestRewardsMutation.Field()
