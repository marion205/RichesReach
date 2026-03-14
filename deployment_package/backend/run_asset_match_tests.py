#!/usr/bin/env python
"""
Standalone test runner for Asset Match Score
=============================================
Runs tests without Django dependency.
"""

import sys
import os

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.reallocation_strategy_service import (
    AssetData,
    AssetMatchScore,
    AssetMatchScorer,
    ASSET_DATABASE,
    ReallocationStrategyService,
    asset_scorer,
)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def ok(self, name):
        self.passed += 1
        print(f"  ✓ {name}")
    
    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ✗ {name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed")
        if self.errors:
            print(f"\nFailures:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        return self.failed == 0


def run_tests():
    result = TestResult()
    
    print("="*60)
    print("ASSET MATCH SCORE TEST SUITE")
    print("="*60)
    
    # ── Test 1: Expense Ratio Scoring ────────────────────────────────────
    print("\n[1] EXPENSE RATIO SCORING")
    
    # 1.1 Excellent expense ratio
    score, rationale = asset_scorer._calculate_expense_score(0.0003)
    if score == 100.0 and "Excellent" in rationale:
        result.ok("VTI (0.03%) scores 100")
    else:
        result.fail("VTI (0.03%) scores 100", f"Got {score}, rationale={rationale}")
    
    # 1.2 High expense ratio
    score, rationale = asset_scorer._calculate_expense_score(0.0075)
    if score <= 40:
        result.ok("0.75% scores ≤40 (high cost)")
    else:
        result.fail("0.75% scores ≤40", f"Got {score}")
    
    # 1.3 Zero expense (stocks)
    score, rationale = asset_scorer._calculate_expense_score(0.0)
    if score == 95.0:
        result.ok("Individual stock (0%) scores 95")
    else:
        result.fail("Individual stock scores 95", f"Got {score}")
    
    # ── Test 2: Diversification Delta ────────────────────────────────────
    print("\n[2] DIVERSIFICATION DELTA")
    
    # 2.1 Total market always high
    vti = ASSET_DATABASE["VTI"]
    score, _ = asset_scorer._calculate_diversification_score(vti, {"tech": 60.0})
    if score >= 80:
        result.ok("VTI scores ≥80 even with 60% tech user")
    else:
        result.fail("VTI diversification for tech-heavy", f"Got {score}")
    
    # 2.2 Tech penalized for tech-heavy user
    qqq = ASSET_DATABASE["QQQ"]
    score, rationale = asset_scorer._calculate_diversification_score(qqq, {"tech": 42.0})
    if score <= 60:
        result.ok("QQQ penalized for 42% tech user")
    else:
        result.fail("QQQ should be penalized", f"Got {score}")
    
    # 2.3 International boosted for US-heavy
    vxus = ASSET_DATABASE["VXUS"]
    score, _ = asset_scorer._calculate_diversification_score(vxus, {"us": 80.0, "total_market": 70.0})
    if score >= 75:
        result.ok("VXUS boosted for US-heavy user")
    else:
        result.fail("VXUS should be boosted", f"Got {score}")
    
    # ── Test 3: Liquidity Scoring ────────────────────────────────────────
    print("\n[3] LIQUIDITY SCORING")
    
    # 3.1 High liquidity
    score, _ = asset_scorer._calculate_liquidity_score(250.0)
    if score == 100.0:
        result.ok("$250M volume scores 100")
    else:
        result.fail("$250M volume = 100", f"Got {score}")
    
    # 3.2 Low liquidity
    score, _ = asset_scorer._calculate_liquidity_score(5.0)
    if score < 45:
        result.ok("$5M volume scores <45 (low liquidity)")
    else:
        result.fail("$5M volume should be low", f"Got {score}")
    
    # ── Test 4: Composite Formula ────────────────────────────────────────
    print("\n[4] COMPOSITE FORMULA (40% + 40% + 20%)")
    
    # 4.1 All 100s = 100
    score_obj = AssetMatchScore(
        symbol="TEST",
        expense_ratio_score=100,
        diversification_delta=100,
        liquidity_score=100,
    )
    score_obj.calculate_total()
    if score_obj.total_score == 100.0:
        result.ok("100/100/100 = 100 total")
    else:
        result.fail("Formula weights", f"Got {score_obj.total_score}")
    
    # 4.2 Weighted correctly
    score_obj = AssetMatchScore(
        symbol="TEST",
        expense_ratio_score=100,  # 40 pts
        diversification_delta=50,  # 20 pts
        liquidity_score=0,         # 0 pts
    )
    score_obj.calculate_total()
    expected = (100 * 0.4) + (50 * 0.4) + (0 * 0.2)  # 60
    if abs(score_obj.total_score - expected) < 0.1:
        result.ok(f"Weighted formula correct: {expected}")
    else:
        result.fail("Weighted formula", f"Expected {expected}, got {score_obj.total_score}")
    
    # ── Test 5: Tech-Heavy User Gets VTI over QQQ ────────────────────────
    print("\n[5] ANTI-CONCENTRATION LOGIC")
    
    vti_score = asset_scorer.score_asset(ASSET_DATABASE["VTI"], {"tech": 42.0})
    qqq_score = asset_scorer.score_asset(ASSET_DATABASE["QQQ"], {"tech": 42.0})
    
    if vti_score.total_score > qqq_score.total_score:
        result.ok(f"VTI ({vti_score.total_score:.1f}) beats QQQ ({qqq_score.total_score:.1f}) for tech-heavy user")
    else:
        result.fail("VTI should beat QQQ", f"VTI={vti_score.total_score}, QQQ={qqq_score.total_score}")
    
    # 5.2 Best asset for tech-heavy is not QQQ
    best, score = asset_scorer.get_best_asset(
        user_sector_exposure={"tech": 40.0},
        user_archetype="steady_builder",
    )
    if best.symbol != "QQQ":
        result.ok(f"Best for tech-heavy: {best.symbol} (not QQQ)")
    else:
        result.fail("Should not recommend QQQ to tech-heavy", f"Got {best.symbol}")
    
    # ── Test 6: Service Integration ──────────────────────────────────────
    print("\n[6] SERVICE INTEGRATION")
    
    service = ReallocationStrategyService()
    suggestion = service.suggest(user_id=1, monthly_amount=127)
    
    # 6.1 Returns strategies
    if len(suggestion.strategies) > 0:
        result.ok(f"Returns {len(suggestion.strategies)} strategies")
    else:
        result.fail("Should return strategies", "Empty list")
    
    # 6.2 Has scored assets
    has_scored = any(len(s.scored_assets) > 0 for s in suggestion.strategies)
    if has_scored:
        result.ok("Strategies have scored assets")
    else:
        result.fail("Missing scored assets", "All empty")
    
    # 6.3 Best asset populated
    if suggestion.best_asset and suggestion.best_asset.match_score > 0:
        result.ok(f"Best asset: {suggestion.best_asset.symbol} ({suggestion.best_asset.match_score})")
    else:
        result.fail("Best asset missing", "None or zero score")
    
    # 6.4 Scored assets have all three factors
    if suggestion.strategies and suggestion.strategies[0].scored_assets:
        asset = suggestion.strategies[0].scored_assets[0]
        has_all = all([
            hasattr(asset, 'expense_score'),
            hasattr(asset, 'diversification_score'),
            hasattr(asset, 'liquidity_score'),
            hasattr(asset, 'match_score'),
        ])
        if has_all:
            result.ok("Scored assets have all three factor scores")
        else:
            result.fail("Missing factor scores", "Not all present")
    
    # ── Test 7: Edge Cases ───────────────────────────────────────────────
    print("\n[7] EDGE CASES")
    
    # 7.1 Empty sector exposure
    score = asset_scorer.score_asset(ASSET_DATABASE["VTI"], {})
    if score.total_score > 0:
        result.ok("Works with empty sector data")
    else:
        result.fail("Empty data handling", f"Got {score.total_score}")
    
    # 7.2 Extreme concentration
    score, _ = asset_scorer._calculate_diversification_score(
        ASSET_DATABASE["QQQ"], 
        {"tech": 100.0}
    )
    if 0 <= score <= 30:
        result.ok(f"100% tech user: QQQ diversification = {score} (correctly low)")
    else:
        result.fail("Extreme concentration", f"Got {score}")
    
    # 7.3 Service without graph context
    result_no_ctx = service.suggest(user_id=1, monthly_amount=50)
    if result_no_ctx.data_quality == "estimated":
        result.ok("No graph context → 'estimated' data quality")
    else:
        result.fail("Data quality flag", f"Got {result_no_ctx.data_quality}")
    
    # ── Summary ──────────────────────────────────────────────────────────
    success = result.summary()
    
    # Print example output
    print("\n" + "="*60)
    print("EXAMPLE OUTPUT")
    print("="*60)
    print(f"\nHeadline: {suggestion.headline_sentence}")
    print(f"Best Asset: {suggestion.best_asset.symbol if suggestion.best_asset else 'None'}")
    print(f"Match Score: {suggestion.best_asset.match_score if suggestion.best_asset else 'N/A'}")
    print(f"Rationale: {suggestion.best_asset_rationale}")
    
    if suggestion.strategies and suggestion.strategies[0].scored_assets:
        print(f"\nTop strategy: {suggestion.strategies[0].name}")
        print("Top 3 scored assets:")
        for i, a in enumerate(suggestion.strategies[0].scored_assets[:3], 1):
            print(f"  {i}. {a.symbol}: {a.match_score}/100")
            print(f"     Expense: {a.expense_score:.0f} | Diversification: {a.diversification_score:.0f} | Liquidity: {a.liquidity_score:.0f}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_tests())
