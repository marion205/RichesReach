import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import CryptoPortfolioCard from '../components/crypto/CryptoPortfolioCard';

const mockPortfolio = {
  total_value_usd: 15000.50,
  total_pnl: 2500.75,
  total_pnl_percentage: 20.0,
  total_pnl_1d: 150.25,
  total_pnl_pct_1d: 1.0,
  total_pnl_1w: 800.50,
  total_pnl_pct_1w: 5.6,
  total_pnl_1m: 2000.25,
  total_pnl_pct_1m: 15.4,
  holdings: [
    {
      cryptocurrency: { symbol: 'BTC' },
      quantity: 0.25,
      current_value: 11250.00,
      unrealized_pnl_percentage: 12.5,
    },
    {
      cryptocurrency: { symbol: 'ETH' },
      quantity: 2.0,
      current_value: 6400.00,
      unrealized_pnl_percentage: 8.3,
    },
  ],
};

const mockAnalytics = {
  portfolio_volatility: 0.045,
  sharpe_ratio: 1.8,
  max_drawdown: 0.15,
  diversification_score: 75.0,
  sector_allocation: {
    LOW: 25.0,
    MEDIUM: 40.0,
    HIGH: 30.0,
    EXTREME: 5.0,
  },
  best_performer: { symbol: 'BTC', pnl_percentage: 12.5 },
  worst_performer: { symbol: 'ETH', pnl_percentage: 8.3 },
};

describe('CryptoPortfolioCard', () => {
  const defaultProps = {
    portfolio: mockPortfolio,
    analytics: mockAnalytics,
    loading: false,
    onRefresh: jest.fn(),
  };

  it('renders portfolio summary correctly', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('Portfolio Value')).toBeTruthy();
    expect(screen.getByText('$15,000.50')).toBeTruthy();
    expect(screen.getByText('+$2,500.75')).toBeTruthy();
    expect(screen.getByText('+20.00%')).toBeTruthy();
  });

  it('shows timeframe switcher', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('1D')).toBeTruthy();
    expect(screen.getByText('1W')).toBeTruthy();
    expect(screen.getByText('1M')).toBeTruthy();
    expect(screen.getByText('ALL')).toBeTruthy();
  });

  it('switches timeframe and updates P&L', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    // Click 1D timeframe
    fireEvent.press(screen.getByText('1D'));
    
    // Should show 1D P&L values
    expect(screen.getByText('+$150.25')).toBeTruthy();
    expect(screen.getByText('+1.00%')).toBeTruthy();
  });

  it('toggles balance masking', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    // Initially shows real values
    expect(screen.getByText('$15,000.50')).toBeTruthy();
    
    // Click eye icon to hide
    const eyeIcon = screen.getByLabelText('Hide balances');
    fireEvent.press(eyeIcon);
    
    // Should show masked values
    expect(screen.getByText('•••••')).toBeTruthy();
  });

  it('renders holdings list', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('Holdings')).toBeTruthy();
    expect(screen.getByText('2 assets')).toBeTruthy();
    expect(screen.getByText('BTC')).toBeTruthy();
    expect(screen.getByText('ETH')).toBeTruthy();
  });

  it('renders risk metrics', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('Risk & Quality')).toBeTruthy();
    expect(screen.getByText('4.5%')).toBeTruthy(); // Volatility
    expect(screen.getByText('1.80')).toBeTruthy(); // Sharpe
    expect(screen.getByText('15.0%')).toBeTruthy(); // Max DD
    expect(screen.getByText('75%')).toBeTruthy(); // Diversification
  });

  it('renders allocation bars', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('Allocation by Risk Tier')).toBeTruthy();
    expect(screen.getByText('LOW')).toBeTruthy();
    expect(screen.getByText('MEDIUM')).toBeTruthy();
    expect(screen.getByText('HIGH')).toBeTruthy();
    expect(screen.getByText('EXTREME')).toBeTruthy();
  });

  it('renders performance section', () => {
    render(<CryptoPortfolioCard {...defaultProps} />);
    
    expect(screen.getByText('Performance')).toBeTruthy();
    expect(screen.getByText('Best')).toBeTruthy();
    expect(screen.getByText('Worst')).toBeTruthy();
    expect(screen.getByText('BTC  +12.50%')).toBeTruthy();
    expect(screen.getByText('ETH  +8.30%')).toBeTruthy();
  });

  it('shows loading state', () => {
    render(<CryptoPortfolioCard {...defaultProps} loading={true} />);
    
    expect(screen.getByText('Loading portfolio…')).toBeTruthy();
  });

  it('shows empty state when no portfolio', () => {
    render(<CryptoPortfolioCard {...defaultProps} portfolio={null} />);
    
    expect(screen.getByText('No Crypto Holdings')).toBeTruthy();
    expect(screen.getByText('Start trading crypto to build your portfolio.')).toBeTruthy();
    expect(screen.getByText('Start Trading')).toBeTruthy();
  });

  it('calls onRefresh when refresh button is pressed', () => {
    const onRefresh = jest.fn();
    render(<CryptoPortfolioCard {...defaultProps} onRefresh={onRefresh} />);
    
    const refreshButton = screen.getByLabelText('Refresh portfolio');
    fireEvent.press(refreshButton);
    
    expect(onRefresh).toHaveBeenCalled();
  });

  it('calls onPressHolding when holding is pressed', () => {
    const onPressHolding = jest.fn();
    render(<CryptoPortfolioCard {...defaultProps} onPressHolding={onPressHolding} />);
    
    // Find and press a holding row
    const btcHolding = screen.getByLabelText('Open BTC details');
    fireEvent.press(btcHolding);
    
    expect(onPressHolding).toHaveBeenCalledWith('BTC');
  });

  it('calls onStartTrading when start trading button is pressed', () => {
    const onStartTrading = jest.fn();
    render(<CryptoPortfolioCard {...defaultProps} portfolio={null} onStartTrading={onStartTrading} />);
    
    const startTradingButton = screen.getByLabelText('Start Trading');
    fireEvent.press(startTradingButton);
    
    expect(onStartTrading).toHaveBeenCalled();
  });

  it('handles missing analytics gracefully', () => {
    render(<CryptoPortfolioCard {...defaultProps} analytics={null} />);
    
    // Should still render portfolio summary
    expect(screen.getByText('Portfolio Value')).toBeTruthy();
    expect(screen.getByText('Holdings')).toBeTruthy();
  });

  it('handles missing timeframe data gracefully', () => {
    const portfolioWithoutTimeframes = {
      ...mockPortfolio,
      total_pnl_1d: undefined,
      total_pnl_pct_1d: undefined,
    };
    
    render(<CryptoPortfolioCard {...defaultProps} portfolio={portfolioWithoutTimeframes} />);
    
    // Should fall back to overall P&L when timeframe data is missing
    fireEvent.press(screen.getByText('1D'));
    expect(screen.getByText('+$2,500.75')).toBeTruthy(); // Falls back to total_pnl
  });

  it('matches snapshot', () => {
    const tree = render(<CryptoPortfolioCard {...defaultProps} />);
    expect(tree.toJSON()).toMatchSnapshot();
  });
});
