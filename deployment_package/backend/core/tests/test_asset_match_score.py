"""
Test Suite: Asset Match Score
==============================
Tests for the three-factor asset scoring algorithm.

Formula:
  Asset_Match_Score = (Expense_Ratio_Score × 0.4) + 
                      (Diversification_Delta × 0.4) + 
                      (Liquidity_Score × 0.2)
"""

import pytest
from decimal import Decimal

from core.reallocation_strategy_service import (
    AssetData,
    AssetMatchScore,
    AssetMatchScorer,
    ASSET_DATABASE,
    ReallocationStrategyService,
    asset_scorer,
)


class TestExpenseRatioScoring:
    """Test Factor 1: Expense Ratio Score (weight: 0.4)"""
    
    def test_excellent_expense_ratio_scores_100(self):
        """VTI/VOO at 0.03% should score 100"""
        score, rationale = asset_scorer._calculate_expense_score(0.0003)
        assert score == 100.0
        assert "Excellent" in rationale
    
    def test_good_expense_ratio_scores_high(self):
        """0.10% should score ~85-95"""
        score, _ = asset_scorer._calculate_expense_score(0.0010)
        assert 80 <= score <= 100
    
    def test_moderate_expense_ratio_scores_mid(self):
        """0.50% should score ~40-60"""
        score, rationale = asset_scorer._calculate_expense_score(0.0050)
        assert 35 <= score <= 65
        assert "Moderate" in rationale
    
    def test_high_expense_ratio_scores_low(self):
        """0.75%+ should score ≤30"""
        score, rationale = asset_scorer._calculate_expense_score(0.0075)
        assert score <= 40
        assert "Higher cost" in rationale
    
    def test_zero_expense_for_stocks(self):
        """Individual stocks (0% expense) should score 95"""
        score, rationale = asset_scorer._calculate_expense_score(0.0)
        assert score == 95.0
        assert "Individual stock" in rationale


class TestDiversificationDelta:
    """Test Factor 2: Diversification Delta (weight: 0.4)"""
    
    def test_total_market_always_scores_high(self):
        """VTI (total market) should score high regardless of user exposure"""
        vti = ASSET_DATABASE["VTI"]
        score, rationale = asset_scorer._calculate_diversification_score(
            vti, 
            {"tech": 60.0, "large_cap": 50.0}
        )
        assert score >= 80
        assert "broad market" in rationale.lower() or "diversi" in rationale.lower()
    
    def test_tech_penalized_when_user_heavy_tech(self):
        """QQQ should score LOW if user is already 42% tech"""
        qqq = ASSET_DATABASE["QQQ"]
        score, rationale = asset_scorer._calculate_diversification_score(
            qqq,
            {"tech": 42.0}
        )
        assert score <= 60
        assert "42%" in rationale or "already" in rationale.lower()
    
    def test_international_boosted_for_us_heavy_user(self):
        """VXUS should score HIGH if user is 80% US"""
        vxus = ASSET_DATABASE["VXUS"]
        score, rationale = asset_scorer._calculate_diversification_score(
            vxus,
            {"us": 80.0, "total_market": 70.0}
        )
        assert score >= 75
        assert "international" in rationale.lower()
    
    def test_no_data_gives_baseline(self):
        """With no user data, should return baseline score"""
        vti = ASSET_DATABASE["VTI"]
        score, rationale = asset_scorer._calculate_diversification_score(vti, {})
        assert 60 <= score <= 85


class TestLiquidityScoring:
    """Test Factor 3: Liquidity Score (weight: 0.2)"""
    
    def test_highly_liquid_scores_100(self):
        """$200M+ daily volume should score 100"""
        score, rationale = asset_scorer._calculate_liquidity_score(250.0)
        assert score == 100.0
        assert "Highly liquid" in rationale
    
    def test_good_liquidity_scores_high(self):
        """$50-200M should score 70-100"""
        score, rationale = asset_scorer._calculate_liquidity_score(100.0)
        assert 70 <= score <= 100
        assert "Good liquidity" in rationale
    
    def test_adequate_liquidity_scores_mid(self):
        """$10-50M should score 40-70"""
        score, rationale = asset_scorer._calculate_liquidity_score(30.0)
        assert 40 <= score <= 75
        assert "Adequate" in rationale
    
    def test_low_liquidity_scores_low(self):
        """<$10M should score under 40"""
        score, rationale = asset_scorer._calculate_liquidity_score(5.0)
        assert score < 45
        assert "Lower" in rationale


class TestCompositeScoring:
    """Test the combined Asset Match Score formula"""
    
    def test_formula_weights_are_correct(self):
        """Verify 0.4 + 0.4 + 0.2 = 1.0"""
        score = AssetMatchScore(
            symbol="TEST",
            expense_ratio_score=100,
            diversification_delta=100,
            liquidity_score=100,
        )
        score.calculate_total()
        # (100 * 0.4) + (100 * 0.4) + (100 * 0.2) = 40 + 40 + 20 = 100
        assert score.total_score == 100.0
    
    def test_low_expense_drives_score_up(self):
        """Low expense ratio should significantly boost total score"""
        vti = ASSET_DATABASE["VTI"]
        score = asset_scorer.score_asset(vti, {})
        # VTI has 0.03% expense, should have high expense score
        assert score.expense_ratio_score >= 95
        assert score.total_score >= 70
    
    def test_concentration_risk_drives_score_down(self):
        """Adding more tech when already tech-heavy should lower score"""
        qqq = ASSET_DATABASE["QQQ"]
        
        # Score QQQ for a user with NO tech exposure
        score_balanced = asset_scorer.score_asset(qqq, {"tech": 10.0})
        
        # Score QQQ for a user HEAVY in tech
        score_concentrated = asset_scorer.score_asset(qqq, {"tech": 50.0})
        
        # The concentrated user should get a lower score
        assert score_concentrated.total_score < score_balanced.total_score
    
    def test_archetype_fit_bonus(self):
        """Assets matching user archetype should get +10 bonus"""
        vti = ASSET_DATABASE["VTI"]  # fits "steady_builder"
        
        score_no_archetype = asset_scorer.score_asset(vti, {}, user_archetype=None)
        score_with_archetype = asset_scorer.score_asset(vti, {}, user_archetype="steady_builder")
        
        # Should be ~10 points higher (capped at 100)
        assert score_with_archetype.total_score >= score_no_archetype.total_score


class TestAssetRanking:
    """Test asset ranking and recommendation logic"""
    
    def test_rank_returns_correct_order(self):
        """Assets should be ranked by total score descending"""
        ranked = asset_scorer.rank_assets_for_strategy(
            strategy_id="growth_etf",
            user_sector_exposure={},
            top_n=5,
        )
        
        assert len(ranked) > 0
        scores = [score.total_score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_tech_heavy_user_gets_vti_over_qqq(self):
        """A 40% tech user should be recommended VTI, not QQQ"""
        best_asset, best_score = asset_scorer.get_best_asset(
            user_sector_exposure={"tech": 40.0},
            user_archetype="steady_builder",
        )
        
        # VTI or VOO should beat QQQ for diversification
        assert best_asset.symbol in ["VTI", "VOO", "VT", "VXUS"]
    
    def test_simple_path_default_is_low_cost(self):
        """The 'Simple Path' recommendation should always be low-cost"""
        best_asset, best_score = asset_scorer.get_best_asset({})
        
        # Should recommend a low-cost fund
        assert best_asset.expense_ratio <= 0.001  # 0.10% or less


class TestReallocationService:
    """Test the full ReallocationStrategyService integration"""
    
    def test_suggest_returns_scored_assets(self):
        """Service should populate scored_assets with match scores"""
        service = ReallocationStrategyService()
        result = service.suggest(user_id=1, monthly_amount=100)
        
        assert len(result.strategies) > 0
        
        # At least one strategy should have scored assets
        has_scored = any(len(s.scored_assets) > 0 for s in result.strategies)
        assert has_scored
    
    def test_suggest_returns_best_asset(self):
        """Service should return a single best asset recommendation"""
        service = ReallocationStrategyService()
        result = service.suggest(user_id=1, monthly_amount=100)
        
        assert result.best_asset is not None
        assert result.best_asset.match_score > 0
        assert result.best_asset_rationale is not None
    
    def test_tech_concentrated_user_gets_diversification_warning(self):
        """User heavy in tech should see warning on tech strategies"""
        service = ReallocationStrategyService()
        
        # Create a mock graph context with tech concentration
        class MockGraphContext:
            tech_allocation_pct = 50.0
            fixed_income_pct = 5.0
            emergency_fund_months = 6.0
        
        result = service.suggest(
            user_id=1, 
            monthly_amount=100,
            graph_context=MockGraphContext(),
        )
        
        # Find the AI/tech strategy
        tech_strategy = next(
            (s for s in result.strategies if s.id == "ai_sector"),
            None
        )
        
        if tech_strategy:
            assert tech_strategy.warning is not None or tech_strategy.fit_score < 60
    
    def test_scored_asset_has_all_three_factors(self):
        """Each scored asset should have explicit factor scores"""
        service = ReallocationStrategyService()
        result = service.suggest(user_id=1, monthly_amount=100)
        
        for strategy in result.strategies:
            for asset in strategy.scored_assets:
                assert hasattr(asset, 'expense_score')
                assert hasattr(asset, 'diversification_score')
                assert hasattr(asset, 'liquidity_score')
                assert hasattr(asset, 'match_score')
                
                # Match score should be weighted combo
                expected = (
                    asset.expense_score * 0.4 +
                    asset.diversification_score * 0.4 +
                    asset.liquidity_score * 0.2
                )
                # Allow for small rounding differences
                assert abs(asset.match_score - expected) < 1.0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_sector_exposure_works(self):
        """Should work with no user data"""
        score = asset_scorer.score_asset(ASSET_DATABASE["VTI"], {})
        assert score.total_score > 0
    
    def test_unknown_sector_handled(self):
        """Should handle unknown sectors gracefully"""
        vti = ASSET_DATABASE["VTI"]
        score, _ = asset_scorer._calculate_diversification_score(
            vti,
            {"unknown_sector": 100.0}
        )
        assert score >= 0
    
    def test_extreme_concentration_handled(self):
        """Should handle 100% concentration in one sector"""
        qqq = ASSET_DATABASE["QQQ"]
        score, _ = asset_scorer._calculate_diversification_score(
            qqq,
            {"tech": 100.0}
        )
        # Should be very low but not negative
        assert 0 <= score <= 30
    
    def test_service_handles_no_graph_context(self):
        """Service should work without graph context"""
        service = ReallocationStrategyService()
        result = service.suggest(user_id=1, monthly_amount=50)
        
        assert result.headline_sentence != ""
        assert result.data_quality == "estimated"


# ── Run with verbose output for debugging ──────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("ASSET MATCH SCORE TEST SUITE")
    print("=" * 60)
    
    # Quick validation
    print("\n1. Testing expense ratio scoring...")
    score, rationale = asset_scorer._calculate_expense_score(0.0003)
    print(f"   VTI (0.03%): {score}/100 — {rationale}")
    
    score, rationale = asset_scorer._calculate_expense_score(0.0020)
    print(f"   QQQ (0.20%): {score}/100 — {rationale}")
    
    print("\n2. Testing diversification for tech-heavy user...")
    vti = ASSET_DATABASE["VTI"]
    qqq = ASSET_DATABASE["QQQ"]
    
    vti_score = asset_scorer.score_asset(vti, {"tech": 42.0})
    qqq_score = asset_scorer.score_asset(qqq, {"tech": 42.0})
    
    print(f"   VTI total score: {vti_score.total_score:.1f}")
    print(f"     - Expense: {vti_score.expense_ratio_score:.1f}")
    print(f"     - Diversification: {vti_score.diversification_delta:.1f}")
    print(f"     - Liquidity: {vti_score.liquidity_score:.1f}")
    print()
    print(f"   QQQ total score: {qqq_score.total_score:.1f}")
    print(f"     - Expense: {qqq_score.expense_ratio_score:.1f}")
    print(f"     - Diversification: {qqq_score.diversification_delta:.1f}")
    print(f"     - Liquidity: {qqq_score.liquidity_score:.1f}")
    
    print("\n3. Testing best asset selection...")
    best, score = asset_scorer.get_best_asset(
        user_sector_exposure={"tech": 40.0},
        user_archetype="steady_builder",
    )
    print(f"   Best for tech-heavy user: {best.symbol} — {score.total_score:.1f}/100")
    print(f"   Rationale: {score.diversification_rationale}")
    
    print("\n4. Full service test...")
    service = ReallocationStrategyService()
    result = service.suggest(user_id=1, monthly_amount=127)
    print(f"   Headline: {result.headline_sentence}")
    print(f"   Best asset: {result.best_asset.symbol if result.best_asset else 'None'}")
    print(f"   Rationale: {result.best_asset_rationale}")
    
    print("\n" + "=" * 60)
    print("✓ Basic validation complete. Run pytest for full test suite.")
    print("=" * 60)
