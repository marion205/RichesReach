# core/refined_ai_prompts.py
"""
Refined AI Prompts for Direct Indexing and TSPT

These prompts ensure the AI explains complex tax benefits in a way that builds trust,
especially for high-stakes actions like selling $500k of stock.
"""
from typing import Dict, Any, Optional
from .visualization_generators import get_visualization_generators


class RefinedAIPrompts:
    """
    Refined prompts for communicating Direct Indexing and TSPT benefits.
    
    Key principles:
    1. Explain the "why" alongside the "how"
    2. Make tax alpha visible and tangible
    3. Build trust through transparency
    4. Emphasize the delta between tracking error and tax alpha
    """
    
    @staticmethod
    def get_direct_indexing_prompt(
        result: Dict[str, Any],
        excluded_stocks: Optional[list] = None,
        portfolio_value: float = 0
    ) -> str:
        """
        Get refined prompt for Direct Indexing explanation.
        
        Emphasizes:
        - Why direct indexing (tax alpha)
        - Tracking error vs tax alpha trade-off
        - Real dollar impact
        """
        target_etf = result.get("target_etf", "the ETF")
        total_stocks = result.get("total_stocks", 0)
        tax_benefits = result.get("expected_tax_benefits", {})
        annual_savings = tax_benefits.get("estimated_annual_tax_savings", 0)
        annual_savings_pct = tax_benefits.get("estimated_annual_savings_pct", 0)
        tracking_error = result.get("tracking_error", {})
        tracking_error_pct = tracking_error.get("estimated_annual_tracking_error_pct", 0)
        
        excluded_text = ""
        if excluded_stocks:
            excluded_text = f" excluding {', '.join(excluded_stocks)}"
        
        prompt = f"""I've customized your {target_etf} tracking{excluded_text} by creating a direct index portfolio of {total_stocks} individual stocks.

**Why This Matters:**
By unbundling the ETF into individual stocks, we've unlocked the ability to harvest losses on individual laggards even when the overall index is up. This "tax alpha" is the key advantage.

**The Numbers:**
- **Tax Alpha**: Approximately {annual_savings_pct:.2f}% annually (${annual_savings:,.2f} per year on a ${portfolio_value:,.0f} portfolio)
- **Tracking Error**: Estimated {tracking_error_pct:.2f}% annually
- **Net Benefit**: {annual_savings_pct - tracking_error_pct:.2f}% after accounting for tracking error

**What This Means:**
In a typical year, this tax alpha can add roughly 0.8% to 1.2% to your net returns compared to a standard ETF. The tracking error is a small cost compared to the tax benefits, especially in volatile markets where individual stock losses create harvesting opportunities.

**The Trade-off:**
We're accepting a small tracking error ({tracking_error_pct:.2f}%) to capture significant tax savings ({annual_savings_pct:.2f}%). This is a net positive for most investors, particularly those in higher tax brackets.

Would you like to see a detailed breakdown of the individual stock allocations, or do you have questions about how tax-loss harvesting works in this context?

---

{visualization}"""
        
        # Add visualization
        viz_gen = get_visualization_generators()
        allocations = result.get("allocations", [])
        if allocations:
            allocation_viz = viz_gen.generate_direct_index_allocation_chart(allocations)
            prompt = prompt.format(
                target_etf=target_etf,
                total_stocks=total_stocks,
                excluded_text=excluded_text,
                annual_savings_pct=annual_savings_pct,
                annual_savings=annual_savings,
                portfolio_value=portfolio_value,
                tracking_error_pct=tracking_error_pct,
                visualization=allocation_viz
            )
        else:
            prompt = prompt.format(
                target_etf=target_etf,
                total_stocks=total_stocks,
                excluded_text=excluded_text,
                annual_savings_pct=annual_savings_pct,
                annual_savings=annual_savings,
                portfolio_value=portfolio_value,
                tracking_error_pct=tracking_error_pct,
                visualization=""
            )
        
        return prompt
    
    @staticmethod
    def get_tspt_prompt(
        result: Dict[str, Any],
        concentrated_position: Dict[str, Any]
    ) -> str:
        """
        Get refined prompt for TSPT explanation.
        
        Emphasizes:
        - The "glide path" visualization
        - Tax savings vs selling all at once
        - Phase-by-phase strategy
        """
        symbol = concentrated_position.get("symbol", "your stock")
        total_tax_savings = result.get("total_tax_savings", 0)
        total_capital_gains_tax = result.get("total_capital_gains_tax", 0)
        transition_plan = result.get("transition_plan", [])
        time_horizon = result.get("time_horizon_months", 36)
        reinvestment_plan = result.get("reinvestment_plan", {})
        
        # Calculate if sold all at once
        total_value = sum(month.get("sale_amount", 0) for month in transition_plan)
        tax_if_sold_all = total_capital_gains_tax + total_tax_savings  # Approximate
        
        prompt = f"""I've created a {time_horizon//12}-year tax-smart transition plan for your concentrated {symbol} position.

**The Strategy:**
Instead of selling all at once (which would trigger a large tax bill), we'll gradually transition over {time_horizon} months, strategically harvesting losses from other positions to offset gains.

**The Glide Path:**
- **Phase 1 (Months 1-12)**: Sell high-basis lots first to minimize immediate tax impact
- **Phase 2 (Months 13-24)**: Offset gains with harvested losses from your direct indexing portfolio
- **Phase 3 (Months 25-{time_horizon})**: Complete remaining sales within lower tax brackets

**The Tax Savings:**
- **If sold all at once**: Approximately ${tax_if_sold_all:,.2f} in capital gains tax
- **With this plan**: Approximately ${total_capital_gains_tax:,.2f} in capital gains tax
- **Your savings**: ${total_tax_savings:,.2f} ({(total_tax_savings/tax_if_sold_all*100) if tax_if_sold_all > 0 else 0:.1f}% reduction)

**Reinvestment Strategy:**
As we sell, we'll reinvest according to your target allocation:
"""
        
        # Add reinvestment details
        allocations = reinvestment_plan.get("allocations", {})
        for asset, details in allocations.items():
            weight = details.get("weight", 0) * 100
            amount = details.get("allocation_amount", 0)
            prompt += f"- **{asset}**: {weight:.0f}% (${amount:,.2f})\n"
        
        prompt += f"""
**Why This Works:**
By spreading the sales over {time_horizon} months, we can:
1. Stay within lower tax brackets each year
2. Harvest losses from other positions to offset gains
3. Time sales to market conditions when possible
4. Reinvest gradually to maintain market exposure

**Next Steps:**
This is a plan, not an execution. Before we proceed, you'll have a chance to review and confirm each phase. Would you like to see the detailed monthly schedule, or do you have questions about the strategy?

---

{visualization}"""
        
        # Add visualization
        viz_gen = get_visualization_generators()
        if transition_plan:
            timeline_viz = viz_gen.generate_tspt_timeline(transition_plan)
            glide_path_viz = viz_gen.generate_glide_path_visualization(transition_plan)
            prompt = prompt.format(
                visualization=timeline_viz + "\n\n" + glide_path_viz
            )
        else:
            prompt = prompt.format(visualization="")
        
        return prompt
    
    @staticmethod
    def get_tax_alpha_dashboard_prompt(
        metrics: Dict[str, Any]
    ) -> str:
        """
        Get prompt for explaining Tax Alpha Dashboard metrics.
        
        Makes the "invisible" tax savings visible.
        """
        tax_alpha = metrics.get("tax_alpha", {})
        performance = metrics.get("performance", {})
        
        total_savings = tax_alpha.get("total_tax_savings", 0)
        annual_alpha = tax_alpha.get("annual_tax_alpha_pct", 0)
        harvested_ytd = tax_alpha.get("harvested_losses_ytd", 0)
        potential = tax_alpha.get("potential_harvestable_losses", 0)
        net_alpha = tax_alpha.get("net_alpha", 0)
        tracking_error = performance.get("tracking_error_pct", 0)
        divergence = performance.get("divergence", 0)
        
        prompt = f"""**Tax Alpha Dashboard Summary**

**Your Tax Savings (Real-Time):**
- **Harvested This Year**: ${harvested_ytd:,.2f} in realized tax savings
- **Potential Available**: ${potential:,.2f} in unrealized losses ready to harvest
- **Total Tax Alpha**: ${total_savings:,.2f} (approximately {annual_alpha:.2f}% of portfolio value)

**Performance vs. Benchmark:**
- **Tracking Error**: {tracking_error:.2f}% (the cost of replication)
- **Net Alpha**: {net_alpha:.2f}% (tax alpha minus tracking error)
- **Portfolio Divergence**: ${divergence:,.2f} (difference from ETF benchmark)

**What This Means:**
Your direct indexing strategy is generating {annual_alpha:.2f}% in tax alpha annually. After accounting for {tracking_error:.2f}% tracking error, you're still ahead by {net_alpha:.2f}%. This "tax alpha" is real money saved—money that would have gone to taxes if you held the ETF instead.

**The Win:**
Every dollar of harvested losses is a dollar you don't pay in taxes. This dashboard shows you exactly how much you're saving in real-time, making the "invisible" tax benefits visible.

---

{visualization}"""
        
        # Add visualization
        viz_gen = get_visualization_generators()
        tax_viz = viz_gen.generate_tax_savings_bar_chart(tax_alpha)
        comparison_viz = viz_gen.generate_tax_alpha_comparison(metrics)
        
        prompt = prompt.format(
            harvested=harvested,
            potential=potential,
            total=total,
            annual_alpha=annual_alpha,
            visualization=tax_viz + "\n\n" + comparison_viz
        )
        
        return prompt
    
    @staticmethod
    def get_compliance_review_prompt(
        review_summary: Dict[str, Any]
    ) -> str:
        """
        Get prompt for compliance review explanation.
        
        Ensures user understands risks before confirming.
        """
        action_name = review_summary.get("action_name", "Financial Action")
        tax_impact = review_summary.get("estimated_tax_impact", 0)
        cost = review_summary.get("estimated_cost", 0)
        risk_level = review_summary.get("risk_level", "medium")
        disclosures = review_summary.get("disclosures", [])
        
        prompt = f"""**Review Required: {action_name}**

Before we proceed with this action, please review the following:

**Estimated Impact:**
- **Tax Impact**: ${abs(tax_impact):,.2f} {'(savings)' if tax_impact < 0 else '(cost)'}
- **Transaction Costs**: ${cost:,.2f}
- **Risk Level**: {risk_level.upper()}

**Important Disclosures:**
"""
        
        for disclosure in disclosures:
            prompt += f"- {disclosure}\n"
        
        prompt += """
**Your Confirmation:**
By confirming, you acknowledge that you:
1. Understand the tax implications
2. Have reviewed the risks and costs
3. Are making an informed decision
4. May want to consult with a tax professional

This action will be logged in your audit trail for compliance purposes.

Would you like to proceed, or do you have questions first?"""
        
        return prompt

