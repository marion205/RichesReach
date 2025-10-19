"""
DeFi Yield Farming Models for RichesReach
Production-grade models for non-custodial yield farming
"""
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

class Chain(models.Model):
    """Supported blockchain networks"""
    chain_id = models.PositiveIntegerField(unique=True)   # 1=ETH, 8453=Base, etc.
    name = models.CharField(max_length=32)
    rpc_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Chain ID: {self.chain_id})"

    class Meta:
        ordering = ['chain_id']

class Protocol(models.Model):
    """DeFi protocols (Aave, Uniswap, Curve, etc.)"""
    slug = models.SlugField(unique=True)                  # 'uniswap', 'aave', 'curve'
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_audited = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Pool(models.Model):
    """DeFi liquidity pools and farming opportunities"""
    protocol = models.ForeignKey(Protocol, on_delete=models.PROTECT)
    chain = models.ForeignKey(Chain, on_delete=models.PROTECT)
    pool_address = models.CharField(max_length=66, db_index=True)  # 0x…
    router_address = models.CharField(max_length=66, blank=True, null=True)
    gauge_address = models.CharField(max_length=66, blank=True, null=True)
    token0 = models.CharField(max_length=64)             # e.g., 'USDC'
    token1 = models.CharField(max_length=64, blank=True)
    token0_decimals = models.PositiveIntegerField(default=6)
    token1_decimals = models.PositiveIntegerField(default=18)
    lp_decimals = models.PositiveIntegerField(default=18)
    symbol = models.CharField(max_length=64)             # 'USDC/ETH'
    tvl_usd = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    apy_base = models.FloatField(default=0)
    apy_reward = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_apy(self):
        return self.apy_base + self.apy_reward

    @property
    def risk_score(self):
        """Calculate risk score based on TVL, protocol, and APY"""
        # Simple risk calculation - can be enhanced
        tvl_risk = 0.25 if self.tvl_usd < Decimal('5000000') else (0.1 if self.tvl_usd < Decimal('20000000') else 0.0)
        apy_risk = min(0.45, (self.apy_base + self.apy_reward) / 80.0)
        protocol_risk = 0.0 if self.protocol.is_audited else 0.2
        il_risk = 0.2 if '/' in self.symbol else 0.05  # LP pairs riskier than single-asset
        
        return max(0.0, min(1.0, tvl_risk + apy_risk + protocol_risk + il_risk))

    def __str__(self):
        return f"{self.protocol.name} - {self.symbol} on {self.chain.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['chain', 'pool_address'], name='uniq_pool_per_chain')
        ]
        ordering = ['-tvl_usd']

class FarmPosition(models.Model):
    """User's farming positions"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE)
    pool = models.ForeignKey(Pool, on_delete=models.PROTECT)
    wallet = models.CharField(max_length=66, db_index=True)
    staked_lp = models.DecimalField(max_digits=38, decimal_places=18, default=Decimal('0'))
    rewards_earned = models.DecimalField(max_digits=38, decimal_places=18, default=Decimal('0'))
    realized_apy = models.FloatField(default=0)     # server-computed
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_value_usd(self):
        """Calculate total position value in USD"""
        if self.staked_lp and self.pool.tvl_usd:
            # This is a simplified calculation - in production you'd get real-time LP token value
            return self.staked_lp * (self.pool.tvl_usd / Decimal('1000000'))  # Rough estimate
        return Decimal('0')

    def __str__(self):
        return f"{self.user.username} - {self.pool.symbol} ({self.staked_lp} LP tokens)"

    class Meta:
        ordering = ['-created_at']

class FarmAction(models.Model):
    """Auditable on-chain action record with decoded result"""
    ACTION_CHOICES = [
        ('STAKE', 'Stake'),
        ('UNSTAKE', 'Unstake'),
        ('HARVEST', 'Harvest'),
        ('CLAIM', 'Claim Rewards'),
    ]
    
    position = models.ForeignKey(FarmPosition, on_delete=models.CASCADE, related_name="actions")
    tx_hash = models.CharField(max_length=66, unique=True)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=38, decimal_places=18, null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    confirmations = models.IntegerField(default=0)
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.tx_hash[:10]}... ({'Success' if self.success else 'Failed'})"

    class Meta:
        ordering = ['-created_at']
