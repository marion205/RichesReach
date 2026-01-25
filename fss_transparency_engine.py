#!/usr/bin/env python3
"""
FSS v3.0 Automated Transparency Engine
Generates weekly PDF reports comparing FSS v3.0 vs Ghost Portfolio
"""
import sys
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import json
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
import django
django.setup()

from core.fss_engine import get_fss_engine
from core.fss_backtest import FSSBacktester
from core.fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
import asyncio

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class FSSTransparencyEngine:
    """Generates transparent weekly reports for FSS v3.0"""
    
    def __init__(self, paper_trading_db_path="fss_paper_trading.json"):
        self.paper_trading_db_path = paper_trading_db_path
        self.fss_engine = get_fss_engine()
        self.backtester = FSSBacktester(transaction_cost_bps=10.0)
    
    def load_paper_trading_data(self):
        """Load paper trading results from JSON file"""
        try:
            if os.path.exists(self.paper_trading_db_path):
                with open(self.paper_trading_db_path, 'r') as f:
                    data = json.load(f)
                return data
            return None
        except Exception as e:
            logger.warning(f"Could not load paper trading data: {e}")
            return None
    
    def get_portfolio_returns(self, period_days=365):
        """
        Returns DataFrame with daily returns:
        columns: ['FSS_Returns', 'Ghost_Returns', 'FSS_CumReturn', 'Ghost_CumReturn']
        index: dates
        """
        data = self.load_paper_trading_data()
        
        if data and 'daily_returns' in data and len(data['daily_returns']) > 0:
            # Load from paper trading
            # daily_returns is a dict: {date_str: {fss_return: X, ghost_return: Y}}
            returns_dict = data['daily_returns']
            
            # Convert to DataFrame
            df_list = []
            for date_str, rets in returns_dict.items():
                df_list.append({
                    'date': pd.to_datetime(date_str),
                    'FSS_Returns': rets.get('fss_return', 0),
                    'Ghost_Returns': rets.get('ghost_return', 0)
                })
            
            if len(df_list) == 0:
                return self._generate_from_backtest(period_days)
            
            daily_returns = pd.DataFrame(df_list).set_index('date').sort_index()
            
            # Get last period_days
            if len(daily_returns) > period_days:
                daily_returns = daily_returns.tail(period_days)
            
            # Calculate cumulative returns (starting from 1.0)
            daily_returns['FSS_CumReturn'] = (1 + daily_returns['FSS_Returns']).cumprod()
            daily_returns['Ghost_CumReturn'] = (1 + daily_returns['Ghost_Returns']).cumprod()
            
            return daily_returns[['FSS_Returns', 'Ghost_Returns', 'FSS_CumReturn', 'Ghost_CumReturn']]
        
        # Fallback: generate from backtest if paper trading not available
        return self._generate_from_backtest(period_days)
    
    def _generate_from_backtest(self, period_days=365):
        """Generate returns from historical backtest"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 50)  # Extra for lookback
            
            # Use a representative universe
            test_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META", "JNJ", "V", "JPM"]
            
            async def fetch_and_backtest():
                pipeline = get_fss_data_pipeline()
                async with pipeline:
                    request = FSSDataRequest(
                        tickers=test_stocks,
                        lookback_days=period_days + 50,
                        include_fundamentals=False
                    )
                    data_result = await pipeline.fetch_fss_data(request)
                
                if len(data_result.prices) < 200:
                    return None
                
                # Calculate FSS
                fss_data = self.fss_engine.compute_fss_v3(
                    prices=data_result.prices,
                    volumes=data_result.volumes,
                    spy=data_result.spy,
                    vix=data_result.vix
                )
                
                # Filter to period
                prices_test = data_result.prices.loc[start_date:end_date]
                spy_test = data_result.spy.loc[start_date:end_date]
                fss_test = fss_data["FSS"].loc[start_date:end_date]
                
                if len(prices_test) < 200:
                    return None
                
                # Create regime series
                regime_series = pd.Series(index=prices_test.index, dtype=object)
                for date in prices_test.index:
                    date_idx = spy_test.index.get_loc(date)
                    window_start = max(0, date_idx - 200)
                    spy_window = spy_test.iloc[window_start:date_idx+1]
                    vix_window = data_result.vix.iloc[window_start:date_idx+1] if data_result.vix is not None else None
                    
                    if len(spy_window) >= 200:
                        regime_result = self.fss_engine.detect_market_regime(spy_window, vix_window)
                        regime_series.loc[date] = regime_result.regime
                    else:
                        regime_series.loc[date] = "Expansion"
                
                # FSS v3.0 (Regime-Aware)
                fss_result = self.backtester.backtest_rank_strategy(
                    prices=prices_test,
                    fss=fss_test,
                    spy=spy_test,
                    rebalance_freq="M",
                    top_n=5,
                    regime=regime_series,
                    cash_out_on_crisis=True,
                    cash_return_rate=0.04
                )
                
                # Ghost (Always-In)
                ghost_result = self.backtester.backtest_rank_strategy(
                    prices=prices_test,
                    fss=fss_test,
                    spy=spy_test,
                    rebalance_freq="M",
                    top_n=5,
                    regime=None,
                    cash_out_on_crisis=False,
                    cash_return_rate=0.04
                )
                
                # Convert to daily returns
                fss_equity = fss_result.equity_curve
                ghost_equity = ghost_result.equity_curve
                
                # Align dates
                common_dates = fss_equity.index.intersection(ghost_equity.index)
                fss_equity = fss_equity.loc[common_dates]
                ghost_equity = ghost_equity.loc[common_dates]
                
                # Calculate daily returns
                fss_rets = fss_equity.pct_change().fillna(0.0)
                ghost_rets = ghost_equity.pct_change().fillna(0.0)
                
                df = pd.DataFrame({
                    'FSS_Returns': fss_rets,
                    'Ghost_Returns': ghost_rets,
                    'FSS_CumReturn': fss_equity,
                    'Ghost_CumReturn': ghost_equity
                }, index=common_dates)
                
                return df
            
            return asyncio.run(fetch_and_backtest())
        
        except Exception as e:
            logger.warning(f"Backtest generation failed: {e}")
            return None
    
    def get_current_regime(self):
        """Get current market regime"""
        try:
            # Try to get from paper trading data
            data = self.load_paper_trading_data()
            if data and 'current_regime' in data:
                return data['current_regime']
            
            # Fallback: calculate from recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=300)
            
            test_stocks = ["SPY"]
            
            async def fetch_regime():
                pipeline = get_fss_data_pipeline()
                async with pipeline:
                    request = FSSDataRequest(
                        tickers=test_stocks,
                        lookback_days=300,
                        include_fundamentals=False
                    )
                    data_result = await pipeline.fetch_fss_data(request)
                
                if len(data_result.spy) < 200:
                    return "Expansion"
                
                spy_recent = data_result.spy.tail(252)
                vix_recent = data_result.vix.tail(252) if data_result.vix is not None else None
                
                regime_result = self.fss_engine.detect_market_regime(spy_recent, vix_recent)
                return regime_result.regime
            
            return asyncio.run(fetch_regime())
        
        except Exception as e:
            logger.warning(f"Regime detection failed: {e}")
            return "Expansion"
    
    def calculate_cagr(self, returns_series):
        """Calculate Compound Annual Growth Rate"""
        if len(returns_series) == 0:
            return 0.0
        cum_ret = (1 + returns_series).prod() - 1
        n_years = len(returns_series) / 252.0  # trading days
        return (1 + cum_ret) ** (1 / n_years) - 1 if n_years > 0 and cum_ret > -1 else 0.0
    
    def calculate_max_drawdown(self, cum_returns):
        """Calculate maximum drawdown"""
        if len(cum_returns) == 0:
            return 0.0
        roll_max = cum_returns.cummax()
        drawdown = (cum_returns - roll_max) / roll_max
        return drawdown.min()  # negative value
    
    def calculate_calmar_ratio(self, returns_series):
        """Calculate Calmar Ratio = CAGR / Max Drawdown"""
        cagr = self.calculate_cagr(returns_series)
        cum_ret = (1 + returns_series).cumprod()
        mdd = abs(self.calculate_max_drawdown(cum_ret))
        return cagr / mdd if mdd > 0 else float('inf') if cagr > 0 else 0.0
    
    def calculate_sharpe_ratio(self, returns_series, risk_free_rate=0.04):
        """Calculate Sharpe Ratio"""
        if len(returns_series) == 0:
            return 0.0
        excess_returns = returns_series - (risk_free_rate / 252.0)
        if excess_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def calculate_sortino_ratio(self, returns_series, risk_free_rate=0.04):
        """Calculate Sortino Ratio (downside deviation)"""
        if len(returns_series) == 0:
            return 0.0
        excess_returns = returns_series - (risk_free_rate / 252.0)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        downside_std = downside_returns.std() * np.sqrt(252)
        return (excess_returns.mean() * 252) / downside_std if downside_std > 0 else 0.0
    
    def calculate_safety_alpha(self, fss_returns, ghost_returns):
        """Calculate Safety Alpha (outperformance during drawdowns)"""
        # Identify drawdown periods (when Ghost is negative)
        drawdown_periods = ghost_returns < 0
        if drawdown_periods.sum() == 0:
            return 0.0
        
        fss_dd_returns = fss_returns[drawdown_periods]
        ghost_dd_returns = ghost_returns[drawdown_periods]
        
        fss_dd_cum = (1 + fss_dd_returns).prod() - 1
        ghost_dd_cum = (1 + ghost_dd_returns).prod() - 1
        
        return fss_dd_cum - ghost_dd_cum  # Positive = FSS outperformed during drawdowns
    
    def generate_equity_curve(self, df):
        """Generate equity curve chart"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.plot(df.index, df['FSS_CumReturn'], label='FSS v3.0 (Regime-Aware)', 
                color='#2ecc71', linewidth=2.5)
        ax.plot(df.index, df['Ghost_CumReturn'], label='Ghost Portfolio (Always-In)', 
                color='#e74c3c', linestyle='--', linewidth=2)
        
        ax.set_title('Equity Curve: FSS v3.0 vs Ghost Portfolio', fontsize=14, fontweight='bold')
        ax.set_ylabel('Cumulative Return', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        buf = BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        plt.close(fig)
        return buf
    
    def generate_drawdown_chart(self, df):
        """Generate drawdown chart"""
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Calculate drawdowns
        fss_cum = df['FSS_CumReturn']
        ghost_cum = df['Ghost_CumReturn']
        
        fss_dd = (fss_cum / fss_cum.cummax()) - 1.0
        ghost_dd = (ghost_cum / ghost_cum.cummax()) - 1.0
        
        ax.fill_between(df.index, fss_dd, 0, alpha=0.3, color='#2ecc71', label='FSS v3.0')
        ax.fill_between(df.index, ghost_dd, 0, alpha=0.3, color='#e74c3c', label='Ghost Portfolio')
        
        ax.plot(df.index, fss_dd, color='#2ecc71', linewidth=1.5)
        ax.plot(df.index, ghost_dd, color='#e74c3c', linewidth=1.5, linestyle='--')
        
        ax.set_title('Drawdown Analysis', fontsize=14, fontweight='bold')
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=min(fss_dd.min(), ghost_dd.min()) * 1.1, top=0.01)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        buf = BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(buf)
        buf.seek(0)
        plt.close(fig)
        return buf
    
    def generate_weekly_pdf(self, output_dir="reports"):
        """Generate weekly transparency PDF report"""
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        filename = os.path.join(output_dir, f"FSS_Weekly_Report_{date_str}.pdf")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#2ecc71'),
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8
        )
        
        elements = []
        
        # Header
        elements.append(Paragraph(f"FSS v3.0 Weekly Transparency Report", title_style))
        elements.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Regime Status
        regime = self.get_current_regime()
        regime_color = {
            "Expansion": colors.HexColor('#2ecc71'),
            "Parabolic": colors.HexColor('#f39c12'),
            "Deflation": colors.HexColor('#e67e22'),
            "Crisis": colors.HexColor('#e74c3c')
        }.get(regime, colors.black)
        
        regime_style = ParagraphStyle(
            'RegimeStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=regime_color,
            spaceAfter=12
        )
        
        elements.append(Paragraph(f"<b>Current Market Regime:</b> {regime}", regime_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Fetch data
        df = self.get_portfolio_returns(period_days=365)
        
        if df is None or len(df) == 0:
            elements.append(Paragraph("⚠️ Insufficient data for report generation.", styles['Normal']))
            doc.build(elements)
            print(f"⚠️ PDF generated with warning: {filename}")
            return filename
        
        fss_rets = df['FSS_Returns']
        ghost_rets = df['Ghost_Returns']
        
        # Calculate metrics
        fss_cagr = self.calculate_cagr(fss_rets)
        ghost_cagr = self.calculate_cagr(ghost_rets)
        
        fss_mdd = abs(self.calculate_max_drawdown(df['FSS_CumReturn']))
        ghost_mdd = abs(self.calculate_max_drawdown(df['Ghost_CumReturn']))
        
        fss_calmar = self.calculate_calmar_ratio(fss_rets)
        ghost_calmar = self.calculate_calmar_ratio(ghost_rets)
        
        fss_sharpe = self.calculate_sharpe_ratio(fss_rets)
        ghost_sharpe = self.calculate_sharpe_ratio(ghost_rets)
        
        fss_sortino = self.calculate_sortino_ratio(fss_rets)
        ghost_sortino = self.calculate_sortino_ratio(ghost_rets)
        
        safety_alpha = self.calculate_safety_alpha(fss_rets, ghost_rets)
        
        # Metrics Table
        elements.append(Paragraph("<b>Performance Metrics (Last 12 Months)</b>", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        metrics_data = [
            ["Metric", "FSS v3.0", "Ghost Portfolio", "Advantage"],
            ["Annualized Return (CAGR)", f"{fss_cagr:.2%}", f"{ghost_cagr:.2%}", 
             f"{(fss_cagr - ghost_cagr):.2%}"],
            ["Max Drawdown", f"{fss_mdd:.2%}", f"{ghost_mdd:.2%}", 
             f"{(ghost_mdd - fss_mdd):.2%} better"],
            ["Calmar Ratio", f"{fss_calmar:.2f}", f"{ghost_calmar:.2f}", 
             f"{fss_calmar - ghost_calmar:+.2f}"],
            ["Sharpe Ratio", f"{fss_sharpe:.2f}", f"{ghost_sharpe:.2f}", 
             f"{fss_sharpe - ghost_sharpe:+.2f}"],
            ["Sortino Ratio", f"{fss_sortino:.2f}", f"{ghost_sortino:.2f}", 
             f"{fss_sortino - ghost_sortino:+.2f}"],
            ["Safety Alpha", f"{safety_alpha:.2%}", "N/A", 
             "Outperformance during drawdowns"]
        ]
        
        table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Equity Curve
        elements.append(Paragraph("<b>Equity Curve Comparison</b>", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        img_buf = self.generate_equity_curve(df)
        img = Image(img_buf, width=6.5*inch, height=3.25*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.3*inch))
        
        # Drawdown Chart
        elements.append(Paragraph("<b>Drawdown Analysis</b>", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        dd_buf = self.generate_drawdown_chart(df)
        dd_img = Image(dd_buf, width=6.5*inch, height=2.6*inch)
        elements.append(dd_img)
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Insights
        elements.append(PageBreak())
        elements.append(Paragraph("<b>Key Insights</b>", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        insights = []
        
        if fss_cagr > ghost_cagr:
            insights.append(f"✅ FSS v3.0 outperformed Ghost Portfolio by {(fss_cagr - ghost_cagr):.2%} annualized")
        else:
            insights.append(f"⚠️ FSS v3.0 underperformed Ghost Portfolio by {(ghost_cagr - fss_cagr):.2%} annualized")
        
        if fss_mdd < ghost_mdd:
            insights.append(f"✅ FSS v3.0 reduced max drawdown by {(ghost_mdd - fss_mdd):.2%} vs Ghost Portfolio")
        
        if fss_calmar > ghost_calmar:
            insights.append(f"✅ FSS v3.0 achieved superior Calmar Ratio ({fss_calmar:.2f} vs {ghost_calmar:.2f})")
        
        if fss_sharpe > ghost_sharpe:
            insights.append(f"✅ FSS v3.0 delivered better risk-adjusted returns (Sharpe {fss_sharpe:.2f} vs {ghost_sharpe:.2f})")
        
        if safety_alpha > 0:
            insights.append(f"✅ Safety Alpha: FSS v3.0 outperformed by {safety_alpha:.2%} during drawdown periods")
        
        if regime in ["Crisis", "Deflation"]:
            insights.append(f"🛡️ Regime-Aware Protection: FSS v3.0 moved to cash during {regime} regime")
        
        for insight in insights:
            elements.append(Paragraph(f"• {insight}", styles['Normal']))
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        elements.append(Paragraph(
            "<i>FSS v3.0: Regime-Aware Execution Engine | Safety Alpha via Hysteresis & Slippage Modeling | "
            "All figures slippage-adjusted (10 bps). Ghost = always-in benchmark. Not investment advice.</i>",
            styles['Italic']
        ))
        
        doc.build(elements)
        print(f"✅ PDF generated: {filename}")
        return filename


def main():
    """Main entry point"""
    engine = FSSTransparencyEngine()
    engine.generate_weekly_pdf()


if __name__ == "__main__":
    main()

