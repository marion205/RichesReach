# core/visualization_generators.py
"""
Visualization Generators for Chat-Friendly Charts

Generates simple, text-based visualizations that render well in chat:
- TSPT timeline chart (sales schedule)
- Tax savings bar graph
- Direct indexing allocation pie chart
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math


class VisualizationGenerators:
    """
    Generates simple visualizations for chat interfaces.
    
    These are text-based charts that render well in markdown/chat.
    """
    
    @staticmethod
    def generate_tspt_timeline(
        transition_plan: List[Dict[str, Any]],
        months_to_show: int = 12
    ) -> str:
        """
        Generate a timeline chart for TSPT sales schedule.
        
        Returns markdown-formatted timeline visualization.
        """
        if not transition_plan:
            return "No transition plan available."
        
        # Get first N months
        plan_slice = transition_plan[:months_to_show]
        
        # Find max sale amount for scaling
        max_sale = max(month.get("sale_amount", 0) for month in plan_slice)
        
        timeline = "## TSPT Sales Timeline (First 12 Months)\n\n"
        timeline += "```\n"
        timeline += "Month | Sale Amount | Tax | Progress\n"
        timeline += "------|-------------|-----|---------\n"
        
        cumulative_sold = 0
        total_value = sum(m.get("sale_amount", 0) for m in transition_plan)
        
        for month in plan_slice:
            month_num = month.get("month", 0)
            sale_amount = month.get("sale_amount", 0)
            tax = month.get("estimated_tax", 0)
            
            cumulative_sold += sale_amount
            progress_pct = (cumulative_sold / total_value * 100) if total_value > 0 else 0
            
            # Create progress bar (20 chars max)
            bar_length = int(progress_pct / 5)  # 5% per char
            progress_bar = "█" * bar_length + "░" * (20 - bar_length)
            
            timeline += f"{month_num:5d} | ${sale_amount:>10,.0f} | ${tax:>6,.0f} | {progress_bar} {progress_pct:.0f}%\n"
        
        timeline += "```\n\n"
        
        # Add summary
        total_months = len(transition_plan)
        timeline += f"**Total Transition Period:** {total_months} months ({total_months//12} years)\n"
        timeline += f"**Total Value:** ${total_value:,.2f}\n"
        
        return timeline
    
    @staticmethod
    def generate_tax_savings_bar_chart(
        tax_data: Dict[str, Any],
        max_bars: int = 10
    ) -> str:
        """
        Generate a bar chart for tax savings visualization.
        
        Args:
            tax_data: Dictionary with tax savings data
                - harvested_ytd: Harvested losses YTD
                - potential_harvestable: Potential harvestable losses
                - total_savings: Total tax savings
                - annual_alpha: Annual tax alpha %
        """
        harvested = tax_data.get("harvested_losses_ytd", 0)
        potential = tax_data.get("potential_harvestable_losses", 0)
        total = tax_data.get("total_tax_savings", 0)
        annual_alpha = tax_data.get("annual_tax_alpha_pct", 0)
        
        # Find max for scaling
        max_value = max(harvested, potential, total) if max(harvested, potential, total) > 0 else 1
        
        chart = "## Tax Savings Breakdown\n\n"
        chart += "```\n"
        chart += "Category                    | Amount      | Visual\n"
        chart += "----------------------------|-------------|----------------------------------------\n"
        
        # Harvested YTD
        bar_length = int((harvested / max_value) * 40) if max_value > 0 else 0
        bar = "█" * bar_length
        chart += f"{'Harvested This Year':<27} | ${harvested:>10,.2f} | {bar}\n"
        
        # Potential
        bar_length = int((potential / max_value) * 40) if max_value > 0 else 0
        bar = "█" * bar_length
        chart += f"{'Potential Available':<27} | ${potential:>10,.2f} | {bar}\n"
        
        # Total
        bar_length = int((total / max_value) * 40) if max_value > 0 else 0
        bar = "█" * bar_length
        chart += f"{'Total Tax Savings':<27} | ${total:>10,.2f} | {bar}\n"
        
        chart += "```\n\n"
        
        # Add summary
        chart += f"**Annual Tax Alpha:** {annual_alpha:.2f}% of portfolio value\n"
        chart += f"**Total Savings:** ${total:,.2f}\n"
        
        return chart
    
    @staticmethod
    def generate_direct_index_allocation_chart(
        allocations: List[Dict[str, Any]],
        top_n: int = 10
    ) -> str:
        """
        Generate a pie chart-style visualization for direct index allocations.
        
        Shows top N holdings with percentages.
        """
        if not allocations:
            return "No allocations available."
        
        # Sort by allocation value
        sorted_allocations = sorted(
            allocations,
            key=lambda x: x.get("allocation_value", 0),
            reverse=True
        )
        
        top_allocations = sorted_allocations[:top_n]
        total_value = sum(a.get("allocation_value", 0) for a in allocations)
        
        chart = f"## Direct Index Allocation (Top {top_n} Holdings)\n\n"
        chart += "```\n"
        chart += "Stock | Weight  | Value      | Visual\n"
        chart += "------|---------|------------|----------------------------------------\n"
        
        for alloc in top_allocations:
            symbol = alloc.get("symbol", "N/A")
            weight = alloc.get("weight", 0) * 100
            value = alloc.get("allocation_value", 0)
            
            # Create bar (40 chars max, scaled to weight)
            bar_length = int(weight * 0.4)  # 1% = 0.4 chars
            bar = "█" * bar_length
            
            chart += f"{symbol:5s} | {weight:6.2f}% | ${value:>10,.2f} | {bar}\n"
        
        chart += "```\n\n"
        
        # Add summary
        other_value = total_value - sum(a.get("allocation_value", 0) for a in top_allocations)
        other_pct = (other_value / total_value * 100) if total_value > 0 else 0
        
        chart += f"**Total Holdings:** {len(allocations)} stocks\n"
        chart += f"**Top {top_n} Holdings:** {sum(a.get('weight', 0) * 100 for a in top_allocations):.1f}% of portfolio\n"
        if other_pct > 0:
            chart += f"**Other Holdings:** {other_pct:.1f}% (${other_value:,.2f})\n"
        
        return chart
    
    @staticmethod
    def generate_tax_alpha_comparison(
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate comparison chart showing tax alpha vs tracking error.
        """
        tax_alpha = metrics.get("tax_alpha", {})
        performance = metrics.get("performance", {})
        
        annual_alpha = tax_alpha.get("annual_tax_alpha_pct", 0)
        tracking_error = performance.get("tracking_error_pct", 0)
        net_alpha = tax_alpha.get("net_alpha", 0)
        
        chart = "## Tax Alpha vs Tracking Error\n\n"
        chart += "```\n"
        chart += "Metric           | Value    | Visual\n"
        chart += "-----------------|----------|----------------------------------------\n"
        
        # Tax Alpha (positive)
        bar_length = int(abs(annual_alpha) * 4)  # Scale for visibility
        bar = "█" * min(bar_length, 40)
        chart += f"{'Tax Alpha':<17} | {annual_alpha:>7.2f}% | {bar} (+)\n"
        
        # Tracking Error (negative)
        bar_length = int(abs(tracking_error) * 4)
        bar = "█" * min(bar_length, 40)
        chart += f"{'Tracking Error':<17} | {tracking_error:>7.2f}% | {bar} (-)\n"
        
        # Net Alpha
        bar_length = int(abs(net_alpha) * 4)
        bar = "█" * min(bar_length, 40)
        sign = "+" if net_alpha >= 0 else "-"
        chart += f"{'Net Alpha':<17} | {net_alpha:>7.2f}% | {bar} ({sign})\n"
        
        chart += "```\n\n"
        
        # Add interpretation
        if net_alpha > 0:
            chart += f"✅ **Net Benefit:** {net_alpha:.2f}% - Tax alpha exceeds tracking error\n"
        else:
            chart += f"⚠️ **Net Cost:** {abs(net_alpha):.2f}% - Tracking error exceeds tax alpha\n"
        
        return chart
    
    @staticmethod
    def generate_glide_path_visualization(
        transition_plan: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a visual "glide path" showing the transition over time.
        """
        if not transition_plan:
            return "No transition plan available."
        
        total_months = len(transition_plan)
        years = total_months // 12
        
        # Group by year
        yearly_sales = {}
        for month in transition_plan:
            month_num = month.get("month", 0)
            year = (month_num - 1) // 12 + 1
            if year not in yearly_sales:
                yearly_sales[year] = 0
            yearly_sales[year] += month.get("sale_amount", 0)
        
        total_value = sum(yearly_sales.values())
        max_year_value = max(yearly_sales.values()) if yearly_sales else 1
        
        chart = f"## TSPT Glide Path ({years}-Year Transition)\n\n"
        chart += "```\n"
        chart += "Year | Annual Sales    | Progress\n"
        chart += "-----|-----------------|----------------------------------------\n"
        
        cumulative = 0
        for year in sorted(yearly_sales.keys()):
            year_value = yearly_sales[year]
            cumulative += year_value
            progress_pct = (cumulative / total_value * 100) if total_value > 0 else 0
            
            # Create progress bar
            bar_length = int(progress_pct / 2.5)  # 2.5% per char
            progress_bar = "█" * min(bar_length, 40)
            
            chart += f"{year:4d} | ${year_value:>14,.0f} | {progress_bar} {progress_pct:.0f}%\n"
        
        chart += "```\n\n"
        
        # Add phase breakdown
        chart += "**Transition Phases:**\n"
        chart += f"- **Phase 1 (Year 1)**: High-basis lots, minimal tax impact\n"
        if years >= 2:
            chart += f"- **Phase 2 (Year 2)**: Offset gains with harvested losses\n"
        if years >= 3:
            chart += f"- **Phase 3 (Year 3)**: Complete remaining sales in lower brackets\n"
        
        return chart


# Singleton instance
_visualization_generators = VisualizationGenerators()


def get_visualization_generators() -> VisualizationGenerators:
    """Get singleton visualization generators instance"""
    return _visualization_generators

