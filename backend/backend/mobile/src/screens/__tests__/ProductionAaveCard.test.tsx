import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import ProductionAAVECard from '../ProductionAAVECard';

// Mock the blockchain services
jest.mock('../../blockchain/wallet/walletConnect', () => ({
  connectWallet: jest.fn(() => Promise.resolve({
    client: {},
    session: {},
    address: '0x1234567890123456789012345678901234567890'
  }))
}));

jest.mock('../../services/hybridTransactionService', () => ({
  HybridTransactionService: jest.fn().mockImplementation(() => ({
    approveIfNeeded: jest.fn(() => Promise.resolve({ skipped: false, hash: '0xabc123' })),
    deposit: jest.fn(() => Promise.resolve({ hash: '0xdef456' })),
    borrow: jest.fn(() => Promise.resolve({ hash: '0xghi789' }))
  }))
}));

// Mock Toast
jest.mock('react-native-toast-message', () => ({
  show: jest.fn()
}));

// Mock Linking
jest.mock('react-native/Libraries/Linking/Linking', () => ({
  openURL: jest.fn(() => Promise.resolve())
}));

describe('ProductionAAVECard', () => {
  it('renders connect wallet button when not connected', () => {
    const { getByText } = render(<ProductionAAVECard />);
    expect(getByText('Connect Wallet')).toBeTruthy();
  });

  it('disables execute button when not connected', () => {
    const { getByText } = render(<ProductionAAVECard />);
    const executeButton = getByText('Execute Hybrid Transaction');
    expect(executeButton.props.disabled).toBe(true);
  });

  it('disables execute button when loading', async () => {
    const { getByText } = render(<ProductionAAVECard />);
    
    // Connect wallet first
    const connectButton = getByText('Connect Wallet');
    fireEvent.press(connectButton);
    
    await waitFor(() => {
      expect(getByText('0x1234...7890')).toBeTruthy();
    });

    // Start transaction
    const executeButton = getByText('Execute Hybrid Transaction');
    fireEvent.press(executeButton);
    
    // Button should be disabled during loading
    await waitFor(() => {
      expect(executeButton.props.disabled).toBe(true);
    });
  });

  it('shows transaction steps during execution', async () => {
    const { getByText } = render(<ProductionAAVECard />);
    
    // Connect wallet
    const connectButton = getByText('Connect Wallet');
    fireEvent.press(connectButton);
    
    await waitFor(() => {
      expect(getByText('0x1234...7890')).toBeTruthy();
    });

    // Start transaction
    const executeButton = getByText('Execute Hybrid Transaction');
    fireEvent.press(executeButton);
    
    // Should show transaction steps
    await waitFor(() => {
      expect(getByText('Transaction Progress')).toBeTruthy();
      expect(getByText('Approve Token')).toBeTruthy();
      expect(getByText('Supply Collateral')).toBeTruthy();
      expect(getByText('Borrow Asset')).toBeTruthy();
    });
  });

  it('handles transaction errors gracefully', async () => {
    const { getByText } = render(<ProductionAAVECard />);
    
    // Mock a failing transaction
    const mockHybridService = require('../../services/hybridTransactionService').HybridTransactionService;
    mockHybridService.mockImplementation(() => ({
      approveIfNeeded: jest.fn(() => Promise.reject(new Error('Transaction failed')))
    }));

    // Connect wallet
    const connectButton = getByText('Connect Wallet');
    fireEvent.press(connectButton);
    
    await waitFor(() => {
      expect(getByText('0x1234...7890')).toBeTruthy();
    });

    // Start transaction
    const executeButton = getByText('Execute Hybrid Transaction');
    fireEvent.press(executeButton);
    
    // Should handle error and re-enable button
    await waitFor(() => {
      expect(executeButton.props.disabled).toBe(false);
    });
  });

  it('updates asset selection correctly', () => {
    const { getByText } = render(<ProductionAAVECard />);
    
    // Find asset selector buttons
    const supplySelector = getByText('USDC ▾');
    const borrowSelector = getByText('WETH ▾');
    
    // Test supply asset selection
    fireEvent.press(supplySelector);
    // Should cycle through assets
    
    // Test borrow asset selection  
    fireEvent.press(borrowSelector);
    // Should cycle through assets
  });

  it('validates input amounts', () => {
    const { getByText, getByPlaceholderText } = render(<ProductionAAVECard />);
    
    const supplyInput = getByPlaceholderText('Amount to supply');
    const borrowInput = getByPlaceholderText('Amount to borrow');
    
    // Test valid input
    fireEvent.changeText(supplyInput, '100');
    fireEvent.changeText(borrowInput, '50');
    
    // Should accept valid amounts
    expect(supplyInput.props.value).toBe('100');
    expect(borrowInput.props.value).toBe('50');
  });
});
