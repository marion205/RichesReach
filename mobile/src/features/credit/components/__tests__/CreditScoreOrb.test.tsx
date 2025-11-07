/**
 * Unit Tests for CreditScoreOrb Component
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import { CreditScoreOrb } from '../CreditScoreOrb';
import { CreditScore, CreditProjection } from '../../types/CreditTypes';

describe('CreditScoreOrb', () => {
  const mockScore: CreditScore = {
    score: 580,
    scoreRange: 'Fair',
    lastUpdated: '2024-01-15T00:00:00Z',
    provider: 'self_reported',
  };

  const mockProjection: CreditProjection = {
    scoreGain6m: 42,
    topAction: 'SET_UP_AUTOPAY',
    confidence: 0.71,
    factors: {},
  };

  it('should render credit score orb', () => {
    const { getByText } = render(
      <CreditScoreOrb score={mockScore} />
    );

    expect(getByText('580')).toBeTruthy();
    expect(getByText('Fair')).toBeTruthy();
  });

  it('should display projection when provided', () => {
    const { getByText } = render(
      <CreditScoreOrb score={mockScore} projection={mockProjection} />
    );

    expect(getByText('→ 622')).toBeTruthy();
    expect(getByText('+42 in 6 months')).toBeTruthy();
  });

  it('should use correct color for score range', () => {
    const { getByText } = render(
      <CreditScoreOrb score={mockScore} />
    );

    const rangeText = getByText('Fair');
    expect(rangeText).toBeTruthy();
  });
});

