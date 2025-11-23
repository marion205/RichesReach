# R&D Automation Roadmap

## Goal
Build automated research pipeline so 1-2 people can test hundreds of strategy variants.

## What We're Building

### Phase 1: Daily Research Pipeline (Weeks 1-3)

#### 1.1 Research Pipeline Command
**File**: `deployment_package/backend/core/management/commands/daily_research_pipeline.py`

```python
class Command(BaseCommand):
    """
    Nightly research pipeline:
    1. Pull DayTradingSignal + market data
    2. Retrain or re-score models
    3. Evaluate candidate tweaks
    4. Promote winners, retire losers
    """
    
    def handle(self):
        # 1. Pull signals and market data
        signals = DayTradingSignal.objects.filter(
            generated_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # 2. Retrain models if needed
        if self._should_retrain(signals):
            ml_scorer.retrain(signals)
        
        # 3. Generate candidate strategies
        candidates = self._generate_candidates()
        
        # 4. Evaluate each candidate
        for candidate in candidates:
            performance = self._evaluate_candidate(candidate, signals)
            
            StrategyPerformance.objects.create(
                strategy_id=f"{candidate.name}_v{candidate.version}",
                mode=candidate.mode,
                period='DAILY',
                # ... performance metrics
            )
        
        # 5. Promote winners, retire losers
        self._promote_winners()
        self._retire_losers()
```

#### 1.2 Candidate Generation
```python
def _generate_candidates(self) -> List[StrategyCandidate]:
    """
    Generate strategy variants to test:
    - Different feature weights
    - Different universe filters
    - Different volatility thresholds
    - Different momentum windows
    """
    candidates = []
    
    # Test different momentum windows
    for window in [10, 15, 20, 30]:  # minutes
        candidates.append(StrategyCandidate(
            name='day_trading_safe',
            version=f'momentum_{window}m',
            params={'momentum_window': window}
        ))
    
    # Test different volatility filters
    for vol_threshold in [0.02, 0.025, 0.03, 0.035]:
        candidates.append(StrategyCandidate(
            name='day_trading_safe',
            version=f'vol_{vol_threshold}',
            params={'max_volatility': vol_threshold}
        ))
    
    return candidates
```

#### 1.3 Cron Schedule
```bash
# deployment_package/backend/cron_jobs.sh

# Nightly research pipeline (2 AM)
0 2 * * * cd /path/to/backend && source venv/bin/activate && python manage.py daily_research_pipeline

# Weekly strategy evaluation (3 AM Monday)
0 3 * * 1 cd /path/to/backend && source venv/bin/activate && python manage.py strategy_health_check --all

# Monthly performance report (4 AM 1st of month)
0 4 1 * * cd /path/to/backend && source venv/bin/activate && python manage.py generate_performance_report
```

### Phase 2: A/B Testing Framework (Weeks 4-6)

#### 2.1 A/B Testing Service
**File**: `deployment_package/backend/core/strategy_ab_testing.py`

```python
class StrategyABTester:
    """
    Automated A/B testing of strategy variants.
    Split signals 50/50, compare performance, promote winners.
    """
    
    def create_test(self, control_strategy: str, candidate_strategy: str) -> str:
        """Create A/B test, return test_id"""
        test = StrategyABTest.objects.create(
            control_strategy=control_strategy,
            candidate_strategy=candidate_strategy,
            status='ACTIVE',
            start_date=timezone.now()
        )
        return test.id
    
    def split_signals(self, test_id: str, signals: List) -> Dict:
        """Split signals 50/50 between control and candidate"""
        import random
        random.shuffle(signals)
        mid = len(signals) // 2
        
        return {
            'control': signals[:mid],
            'candidate': signals[mid:]
        }
    
    def evaluate_test(self, test_id: str) -> Dict:
        """
        After X days, compare performance:
        {
            'control_performance': {...},
            'candidate_performance': {...},
            'winner': 'candidate',  # or 'control'
            'promote': True  # Should we promote candidate?
        }
        """
        test = StrategyABTest.objects.get(id=test_id)
        
        control_perf = StrategyPerformance.objects.filter(
            strategy_id=test.control_strategy
        ).latest('period_end')
        
        candidate_perf = StrategyPerformance.objects.filter(
            strategy_id=test.candidate_strategy
        ).latest('period_end')
        
        # Compare Sharpe, win rate, DD
        winner = self._determine_winner(control_perf, candidate_perf)
        
        if winner == 'candidate':
            self._promote_strategy(test.candidate_strategy)
            self._retire_strategy(test.control_strategy)
        
        return {
            'winner': winner,
            'promote': winner == 'candidate'
        }
```

#### 2.2 Test Examples
```python
# Example: Test CORE vs DYNAMIC_MOVERS
ab_tester.create_test(
    control_strategy='day_trading_safe_core_v1',
    candidate_strategy='day_trading_safe_dynamic_v1'
)

# Example: Test different feature weights
ab_tester.create_test(
    control_strategy='day_trading_safe_v1',
    candidate_strategy='day_trading_safe_momentum_boost_v2'
)
```

### Phase 3: Research Harness (Weeks 7-9)

#### 3.1 Jupyter Notebook Integration
**Structure**:
```
research/
  notebooks/
    exploratory_analysis.ipynb
    backtest_strategy_variant.ipynb
    evaluate_feature_importance.ipynb
  scripts/
    backtest_candidate.py
    evaluate_variant.py
    generate_report.py
```

#### 3.2 Backtest Script
```python
# research/scripts/backtest_candidate.py
def backtest_strategy_variant(candidate: StrategyCandidate, signals: List):
    """
    Backtest a strategy variant against historical signals.
    Returns performance metrics.
    """
    # Load historical data
    # Apply candidate parameters
    # Calculate performance
    # Return metrics
    pass
```

#### 3.3 Cloud Compute Integration
```python
# Use AWS/GCP for heavy backtests
def run_parallel_backtests(candidates: List):
    """Run multiple backtests in parallel on cloud"""
    # Submit jobs to cloud
    # Collect results
    # Store in database
    pass
```

## Success Metrics

- ✅ 10+ strategy variants tested per month
- ✅ Automated promotion/retirement of strategies
- ✅ Research pipeline runs without manual intervention
- ✅ A/B tests complete and winners promoted automatically

## Implementation Timeline

- **Weeks 1-3**: Daily research pipeline
- **Weeks 4-6**: A/B testing framework
- **Weeks 7-9**: Research harness (notebooks, scripts)
- **Week 10**: Cloud compute integration
- **Week 11**: Monitoring and alerts
- **Week 12**: Documentation and training

## Expected Impact

- **Research Velocity**: 10x faster strategy testing
- **Quality**: Automated quality control
- **Scalability**: Test hundreds of variants with 1-2 people
- **Edge**: Continuous improvement through automation

