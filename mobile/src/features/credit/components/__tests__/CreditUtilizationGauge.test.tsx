/**
 * Unit Tests for CreditUtilizationGauge Component
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { CreditUtilizationGauge } from '../CreditUtilizationGauge';
import { CreditUtilization } from '../../types/CreditTypes';

describe('CreditUtilizationGauge', () => {
  const mockUtilization: CreditUtilization = {
    totalLimit: 1000,
    totalBalance: 450,
    currentUtilization: 0.45,
    optimalUtilization: 0.3,
    paydownSuggestion: 150,
    projectedScoreGain: 8,
  };

  it('should render utilization gauge', () => {
    const { getByText } = render(
      <CreditUtilizationGauge utilization={mockUtilization} />
    );

    expect(getByText('Credit Utilization')).toBeTruthy();
    expect(getByText('45%')).toBeTruthy();
  });

  it('should show paydown suggestion when utilization is high', () => {
    const { getByText } = render(
      <CreditUtilizationGauge utilization={mockUtilization} />
    );

    expect(getByText(/Pay down \$150/)).toBeTruthy();
    expect(getByText(/\+8 points/)).toBeTruthy();
  });

  it('should display optimal marker at 30%', () => {
    const { getByText } = render(
      <CreditUtilizationGauge utilization={mockUtilization} />
    );

    expect(getByText('Optimal: 30%')).toBeTruthy();
  });
});

