"""
GraphQL Types for AI Scans and Playbooks
"""
import graphene
from graphene import ObjectType, String, List, Boolean, Float, Int, Field, JSONString
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ===================
# Input Types
# ===================

class AIScanFilters(graphene.InputObjectType):
    """Filters for AI Scans query"""
    category = String()
    riskLevel = String()
    timeHorizon = String()
    isActive = Boolean()
    tags = List(String)

# ===================
# Performance Types
# ===================

class PerformanceType(graphene.ObjectType):
    """Performance metrics for scans and playbooks"""
    successRate = Float()
    averageReturn = Float()
    maxDrawdown = Float()
    sharpeRatio = Float()
    winRate = Float()
    totalRuns = Int()
    avgHoldTime = Int()
    lastUpdated = String()
    
    def __init__(self, **kwargs):
        # Ensure all numeric fields are valid numbers, never None or NaN
        kwargs['successRate'] = float(kwargs.get('successRate', 0.0)) if kwargs.get('successRate') is not None else 0.0
        kwargs['averageReturn'] = float(kwargs.get('averageReturn', 0.0)) if kwargs.get('averageReturn') is not None else 0.0
        kwargs['maxDrawdown'] = float(kwargs.get('maxDrawdown', 0.0)) if kwargs.get('maxDrawdown') is not None else 0.0
        kwargs['sharpeRatio'] = float(kwargs.get('sharpeRatio', 0.0)) if kwargs.get('sharpeRatio') is not None else 0.0
        kwargs['winRate'] = float(kwargs.get('winRate', 0.0)) if kwargs.get('winRate') is not None else 0.0
        kwargs['totalRuns'] = int(kwargs.get('totalRuns', 0)) if kwargs.get('totalRuns') is not None else 0
        kwargs['avgHoldTime'] = int(kwargs.get('avgHoldTime', 0)) if kwargs.get('avgHoldTime') is not None else 0
        kwargs['lastUpdated'] = kwargs.get('lastUpdated', '')
        
        # Validate no NaN
        for key in ['successRate', 'averageReturn', 'maxDrawdown', 'sharpeRatio', 'winRate']:
            if key in kwargs and (kwargs[key] != kwargs[key]):  # NaN check
                kwargs[key] = 0.0
        
        super().__init__(**kwargs)

# ===================
# Scan Result Types
# ===================

class ScanResultType(graphene.ObjectType):
    """Individual result from an AI scan"""
    id = String()
    symbol = String()
    name = String()
    currentPrice = Float()
    change = Float()
    changePercent = Float()
    volume = Int()
    marketCap = Float()
    score = Float()
    confidence = Float()
    reasoning = String()
    riskFactors = List(String)
    opportunityFactors = List(String)
    
    def __init__(self, **kwargs):
        # Ensure all numeric fields are valid numbers, never None or NaN
        kwargs['currentPrice'] = float(kwargs.get('currentPrice', 0.0)) if kwargs.get('currentPrice') is not None else 0.0
        kwargs['change'] = float(kwargs.get('change', 0.0)) if kwargs.get('change') is not None else 0.0
        kwargs['changePercent'] = float(kwargs.get('changePercent', 0.0)) if kwargs.get('changePercent') is not None else 0.0
        kwargs['volume'] = int(kwargs.get('volume', 0)) if kwargs.get('volume') is not None else 0
        kwargs['marketCap'] = float(kwargs.get('marketCap', 0.0)) if kwargs.get('marketCap') is not None else 0.0
        kwargs['score'] = float(kwargs.get('score', 0.0)) if kwargs.get('score') is not None else 0.0
        kwargs['confidence'] = float(kwargs.get('confidence', 0.0)) if kwargs.get('confidence') is not None else 0.0
        kwargs['id'] = kwargs.get('id', '')
        kwargs['symbol'] = kwargs.get('symbol', '')
        kwargs['name'] = kwargs.get('name', '')
        kwargs['reasoning'] = kwargs.get('reasoning', '')
        kwargs['riskFactors'] = kwargs.get('riskFactors', []) or []
        kwargs['opportunityFactors'] = kwargs.get('opportunityFactors', []) or []
        
        # Validate no NaN
        for key in ['currentPrice', 'change', 'changePercent', 'marketCap', 'score', 'confidence']:
            if key in kwargs and (kwargs[key] != kwargs[key]):  # NaN check
                kwargs[key] = 0.0
        
        super().__init__(**kwargs)

# ===================
# Playbook Types
# ===================

class PlaybookType(graphene.ObjectType):
    """Playbook definition for institutional strategies"""
    id = String()
    name = String()
    description = String()
    author = String()
    category = String()
    riskLevel = String()
    isPublic = Boolean()
    isClonable = Boolean()
    tags = List(String)
    performance = Field(PerformanceType)
    version = String()

# ===================
# AI Scan Types
# ===================

class AIScanType(graphene.ObjectType):
    """AI Market Scan definition"""
    id = String()
    name = String()
    description = String()
    category = String()
    riskLevel = String()
    timeHorizon = String()
    isActive = Boolean()
    lastRun = String()
    results = List(ScanResultType)
    playbook = Field(PlaybookType)
    performance = Field(PerformanceType)
    version = String()

# ===================
# Query Root
# ===================

class AIScansQueries(graphene.ObjectType):
    """GraphQL queries for AI Scans"""
    
    aiScans = graphene.List(
        AIScanType,
        filters=graphene.Argument(AIScanFilters),
        description="Get AI market scans with optional filters"
    )
    
    playbooks = graphene.List(
        PlaybookType,
        description="Get available trading playbooks"
    )
    
    def resolve_aiScans(self, info, filters=None):
        """Resolve AI scans query"""
        user = getattr(info.context, "user", None)
        user_id = user.id if user and not user.is_anonymous else None
        
        logger.info(f"📊 [AI Scans] Query from user {user_id}, filters: {filters}")
        
        # Generate sample scans based on filters
        scans = []
        
        # Sample scan categories
        categories = ['momentum', 'value', 'growth', 'dividend', 'volatility', 'earnings', 'sector_rotation', 'technical_breakout']
        risk_levels = ['low', 'medium', 'high']
        time_horizons = ['daily', 'weekly', 'monthly']
        
        # Apply filters
        filtered_categories = [categories[0]]  # Default
        if filters and filters.get('category'):
            filtered_categories = [filters['category']]
        elif not filters:
            filtered_categories = categories[:4]  # Show 4 different categories
        
        filtered_risk = risk_levels
        if filters and filters.get('riskLevel'):
            filtered_risk = [filters['riskLevel']]
        
        filtered_horizon = time_horizons
        if filters and filters.get('timeHorizon'):
            filtered_horizon = [filters['timeHorizon']]
        
        is_active_filter = True
        if filters and filters.get('isActive') is not None:
            is_active_filter = filters['isActive']
        
        # Generate scans
        scan_id = 1
        for cat in filtered_categories:
            for risk in filtered_risk:
                for horizon in filtered_horizon:
                    scan_name = f"{cat.replace('_', ' ').title()} {risk.title()} {horizon.title()}"
                    
                    # Sample results
                    results = []
                    sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']
                    for i, symbol in enumerate(sample_symbols[:3]):
                        # Ensure all numeric values are valid (not NaN)
                        current_price = float(150.0 + (i * 10))
                        change_val = float(2.5 + i)
                        change_pct = float(1.5 + (i * 0.3))
                        vol = int(1000000 + (i * 100000))
                        mcap = float(1000000000 * (i + 1))
                        score_val = float(0.7 + (i * 0.05))
                        conf_val = float(0.8 + (i * 0.03))
                        
                        # Validate no NaN values
                        if any(x != x for x in [current_price, change_val, change_pct, vol, mcap, score_val, conf_val]):  # NaN check
                            continue
                        
                        results.append(ScanResultType(
                            id=f"result-{scan_id}-{i+1}",
                            symbol=symbol,
                            name=f"{symbol} Inc.",
                            currentPrice=current_price,
                            change=change_val,
                            changePercent=change_pct,
                            volume=vol,
                            marketCap=mcap,
                            score=score_val,
                            confidence=conf_val,
                            reasoning=f"Strong {cat} signals detected",
                            riskFactors=["Market volatility", "Sector rotation"],
                            opportunityFactors=["Strong fundamentals", "Technical breakout"]
                        ))
                    
                    # Sample playbook - ensure all numeric values are valid
                    perf_success_rate = float(0.65 + (scan_id * 0.02))
                    perf_avg_return = float(0.12 + (scan_id * 0.01))
                    perf_max_dd = float(0.08)
                    perf_sharpe = float(1.5 + (scan_id * 0.1))
                    perf_win_rate = float(0.60 + (scan_id * 0.02))
                    perf_total_runs = int(100 + (scan_id * 10))
                    perf_hold_time = int(5 + scan_id)
                    
                    # Validate no NaN values
                    if any(x != x for x in [perf_success_rate, perf_avg_return, perf_max_dd, perf_sharpe, perf_win_rate]):
                        perf_success_rate = 0.65
                        perf_avg_return = 0.12
                        perf_max_dd = 0.08
                        perf_sharpe = 1.5
                        perf_win_rate = 0.60
                    
                    playbook = PlaybookType(
                        id=f"playbook-{scan_id}",
                        name=f"{cat.replace('_', ' ').title()} Strategy",
                        description=f"Professional {cat} trading strategy",
                        author="RichesReach AI",
                        category=cat,
                        riskLevel=risk,
                        isPublic=True,
                        isClonable=True,
                        tags=[cat, risk, horizon],
                        performance=PerformanceType(
                            successRate=perf_success_rate,
                            averageReturn=perf_avg_return,
                            maxDrawdown=perf_max_dd,
                            sharpeRatio=perf_sharpe,
                            winRate=perf_win_rate,
                            totalRuns=perf_total_runs,
                            avgHoldTime=perf_hold_time,
                            lastUpdated=datetime.now().isoformat()
                        ),
                        version="1.0.0"
                    )
                    
                    # Scan performance - ensure all numeric values are valid
                    scan_perf_success_rate = float(0.65 + (scan_id * 0.02))
                    scan_perf_avg_return = float(0.12 + (scan_id * 0.01))
                    scan_perf_max_dd = float(0.08)
                    scan_perf_sharpe = float(1.5 + (scan_id * 0.1))
                    scan_perf_win_rate = float(0.60 + (scan_id * 0.02))
                    scan_perf_total_runs = int(100 + (scan_id * 10))
                    scan_perf_hold_time = int(5 + scan_id)
                    
                    # Validate no NaN values
                    if any(x != x for x in [scan_perf_success_rate, scan_perf_avg_return, scan_perf_max_dd, scan_perf_sharpe, scan_perf_win_rate]):
                        scan_perf_success_rate = 0.65
                        scan_perf_avg_return = 0.12
                        scan_perf_max_dd = 0.08
                        scan_perf_sharpe = 1.5
                        scan_perf_win_rate = 0.60
                    
                    scan = AIScanType(
                        id=f"scan-{scan_id}",
                        name=scan_name,
                        description=f"AI-powered {cat} scan for {risk} risk, {horizon} horizon",
                        category=cat,
                        riskLevel=risk,
                        timeHorizon=horizon,
                        isActive=is_active_filter,
                        lastRun=datetime.now().isoformat(),
                        results=results if is_active_filter else [],
                        playbook=playbook,
                        performance=PerformanceType(
                            successRate=scan_perf_success_rate,
                            averageReturn=scan_perf_avg_return,
                            maxDrawdown=scan_perf_max_dd,
                            sharpeRatio=scan_perf_sharpe,
                            winRate=scan_perf_win_rate,
                            totalRuns=scan_perf_total_runs,
                            avgHoldTime=scan_perf_hold_time,
                            lastUpdated=datetime.now().isoformat()
                        ),
                        version="1.0.0"
                    )
                    
                    scans.append(scan)
                    scan_id += 1
                    
                    # Limit to reasonable number
                    if len(scans) >= 8:
                        break
                if len(scans) >= 8:
                    break
            if len(scans) >= 8:
                break
        
        logger.info(f"✅ [AI Scans] Returning {len(scans)} scans")
        return scans
    
    def resolve_playbooks(self, info):
        """Resolve playbooks query"""
        user = getattr(info.context, "user", None)
        user_id = user.id if user and not user.is_anonymous else None
        
        logger.info(f"📚 [Playbooks] Query from user {user_id}")
        
        # Generate sample playbooks
        playbooks = []
        categories = ['momentum', 'value', 'growth', 'dividend', 'volatility']
        risk_levels = ['low', 'medium', 'high']
        
        for i, cat in enumerate(categories):
            for j, risk in enumerate(risk_levels):
                playbook_id = i * len(risk_levels) + j + 1
                
                # Ensure all numeric values are valid (not NaN)
                pb_success_rate = float(0.60 + (playbook_id * 0.02))
                pb_avg_return = float(0.10 + (playbook_id * 0.01))
                pb_max_dd = float(max(0.01, 0.10 - (playbook_id * 0.01)))  # Ensure positive
                pb_sharpe = float(1.4 + (playbook_id * 0.1))
                pb_win_rate = float(0.58 + (playbook_id * 0.02))
                pb_total_runs = int(150 + (playbook_id * 20))
                pb_hold_time = int(7 + playbook_id)
                
                # Validate no NaN values
                if any(x != x for x in [pb_success_rate, pb_avg_return, pb_max_dd, pb_sharpe, pb_win_rate]):
                    pb_success_rate = 0.60
                    pb_avg_return = 0.10
                    pb_max_dd = 0.08
                    pb_sharpe = 1.4
                    pb_win_rate = 0.58
                
                playbook = PlaybookType(
                    id=f"playbook-{playbook_id}",
                    name=f"{cat.replace('_', ' ').title()} {risk.title()} Strategy",
                    description=f"Professional {cat} trading strategy optimized for {risk} risk tolerance",
                    author="RichesReach AI",
                    category=cat,
                    riskLevel=risk,
                    isPublic=True,
                    isClonable=True,
                    tags=[cat, risk, "institutional"],
                    performance=PerformanceType(
                        successRate=pb_success_rate,
                        averageReturn=pb_avg_return,
                        maxDrawdown=pb_max_dd,
                        sharpeRatio=pb_sharpe,
                        winRate=pb_win_rate,
                        totalRuns=pb_total_runs,
                        avgHoldTime=pb_hold_time,
                        lastUpdated=datetime.now().isoformat()
                    ),
                    version="1.0.0"
                )
                playbooks.append(playbook)
        
        logger.info(f"✅ [Playbooks] Returning {len(playbooks)} playbooks")
        return playbooks

