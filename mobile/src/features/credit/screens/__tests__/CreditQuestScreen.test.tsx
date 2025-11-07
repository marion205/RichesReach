/**
 * Unit Tests for CreditQuestScreen Component
 */

import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { CreditQuestScreen } from '../CreditQuestScreen';
import { creditScoreService } from '../../services/CreditScoreService';

// Mock services
jest.mock('../../services/CreditScoreService');
jest.mock('../../services/CreditUtilizationService');

describe('CreditQuestScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    (creditScoreService.getSnapshot as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { getByText } = render(
      <CreditQuestScreen visible={true} onClose={() => {}} />
    );

    expect(getByText('Loading your credit journey...')).toBeTruthy();
  });

  it('should render empty state when no snapshot', async () => {
    (creditScoreService.getSnapshot as jest.Mock).mockRejectedValue(
      new Error('No data')
    );

    const { getByText } = render(
      <CreditQuestScreen visible={true} onClose={() => {}} />
    );

    await waitFor(() => {
      expect(getByText('Start Your Credit Journey')).toBeTruthy();
    });
  });

  it('should not render when not visible', () => {
    const { queryByText } = render(
      <CreditQuestScreen visible={false} onClose={() => {}} />
    );

    expect(queryByText('Credit Quest')).toBeNull();
  });
});

