/**
 * Unit tests for demo Private Markets service: saved deals (getSavedDealIds, saveDeal, unsaveDeal).
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { demoPrivateMarketsService } from '../demoPrivateMarketsService';

const mockGetItem = AsyncStorage.getItem as jest.Mock;
const mockSetItem = AsyncStorage.setItem as jest.Mock;

describe('demoPrivateMarketsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getSavedDealIds', () => {
    it('returns empty array when nothing stored', async () => {
      mockGetItem.mockResolvedValue(null);
      const ids = await demoPrivateMarketsService.getSavedDealIds();
      expect(ids).toEqual([]);
      expect(mockGetItem).toHaveBeenCalledWith('privateMarkets_savedDealIds');
    });

    it('returns parsed array when storage has valid JSON', async () => {
      mockGetItem.mockResolvedValue(JSON.stringify(['1', '2']));
      const ids = await demoPrivateMarketsService.getSavedDealIds();
      expect(ids).toEqual(['1', '2']);
    });

    it('returns empty array when storage has invalid JSON', async () => {
      mockGetItem.mockResolvedValue('not json');
      const ids = await demoPrivateMarketsService.getSavedDealIds();
      expect(ids).toEqual([]);
    });
  });

  describe('saveDeal', () => {
    it('persists deal id to storage', async () => {
      mockGetItem.mockResolvedValue(null);
      await demoPrivateMarketsService.saveDeal('1');
      expect(mockSetItem).toHaveBeenCalledWith('privateMarkets_savedDealIds', JSON.stringify(['1']));
    });

    it('appends to existing saved ids', async () => {
      mockGetItem.mockResolvedValue(JSON.stringify(['1']));
      await demoPrivateMarketsService.saveDeal('2');
      expect(mockSetItem).toHaveBeenCalledWith('privateMarkets_savedDealIds', JSON.stringify(['1', '2']));
    });

    it('does not duplicate when deal already saved', async () => {
      mockGetItem.mockResolvedValue(JSON.stringify(['1', '2']));
      await demoPrivateMarketsService.saveDeal('1');
      expect(mockSetItem).not.toHaveBeenCalled();
    });
  });

  describe('unsaveDeal', () => {
    it('removes deal id from storage', async () => {
      mockGetItem.mockResolvedValue(JSON.stringify(['1', '2']));
      await demoPrivateMarketsService.unsaveDeal('1');
      expect(mockSetItem).toHaveBeenCalledWith('privateMarkets_savedDealIds', JSON.stringify(['2']));
    });

    it('writes empty array when last deal unsaved', async () => {
      mockGetItem.mockResolvedValue(JSON.stringify(['1']));
      await demoPrivateMarketsService.unsaveDeal('1');
      expect(mockSetItem).toHaveBeenCalledWith('privateMarkets_savedDealIds', JSON.stringify([]));
    });
  });
});
