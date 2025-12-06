/**
 * Comprehensive unit tests for VoiceWeb3Controller
 */
import VoiceWeb3Controller, { VoiceWeb3Command } from '../VoiceWeb3Controller';
import { Web3Service } from '../../../../services/Web3Service';

// Mock Web3Service
jest.mock('../../../../services/Web3Service');

describe('VoiceWeb3Controller', () => {
  let controller: VoiceWeb3Controller;
  let mockWeb3Service: jest.Mocked<Web3Service>;

  beforeEach(() => {
    jest.clearAllMocks();
    controller = VoiceWeb3Controller.getInstance();
    mockWeb3Service = Web3Service.getInstance() as jest.Mocked<Web3Service>;
  });

  describe('parseVoiceCommand', () => {
    it('should parse transfer command with amount and token', () => {
      const text = 'send 100 USDC to 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('transfer');
      expect(result?.params.amount).toBe(100);
      expect(result?.params.token).toBe('USDC');
      expect(result?.params.recipient).toBe('0x1234567890123456789012345678901234567890');
    });

    it('should parse transfer command with ETH', () => {
      const text = 'transfer 0.5 ETH to 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('transfer');
      expect(result?.params.amount).toBe(0.5);
      expect(result?.params.token).toBe('ETH');
    });

    it('should parse swap command', () => {
      const text = 'swap 100 USDC for ETH';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('swap');
      expect(result?.params.amount).toBe(100);
      expect(result?.params.token).toBe('USDC');
    });

    it('should parse stake command', () => {
      const text = 'stake 10 ETH';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('stake');
      expect(result?.params.amount).toBe(10);
      expect(result?.params.token).toBe('ETH');
    });

    it('should parse unstake command', () => {
      const text = 'unstake 5 ETH';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('unstake');
      expect(result?.params.amount).toBe(5);
    });

    it('should parse vote command', () => {
      const text = 'vote yes on proposal 1';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('vote');
      expect(result?.params.proposalId).toBe('1');
    });

    it('should parse bridge command', () => {
      const text = 'bridge 100 USDC to polygon';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('bridge');
      expect(result?.params.amount).toBe(100);
      expect(result?.params.chain).toBe('polygon');
    });

    it('should parse mint NFT command', () => {
      const text = 'mint NFT from 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('mint');
      expect(result?.params.nftContract).toBe('0x1234567890123456789012345678901234567890');
    });

    it('should return null for unrecognized command', () => {
      const text = 'hello world';
      const result = controller.parseVoiceCommand(text);

      expect(result).toBeNull();
    });

    it('should handle case insensitive commands', () => {
      const text = 'SEND 100 USDC TO 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('transfer');
    });

    it('should handle decimal amounts', () => {
      const text = 'send 0.5 ETH to 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.params.amount).toBe(0.5);
    });

    it('should handle commands with extra words', () => {
      const text = 'please send 100 USDC tokens to address 0x1234567890123456789012345678901234567890';
      const result = controller.parseVoiceCommand(text);

      expect(result).not.toBeNull();
      expect(result?.action).toBe('transfer');
      expect(result?.params.amount).toBe(100);
    });
  });

  describe('executeCommand', () => {
    it('should execute transfer command successfully', async () => {
      mockWeb3Service.transferToken = jest.fn().mockResolvedValue('0xtxhash123');

      const command: VoiceWeb3Command = {
        action: 'transfer',
        params: {
          token: 'ETH',
          recipient: '0x1234567890123456789012345678901234567890',
          amount: 1.0,
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(true);
      expect(result.txHash).toBe('0xtxhash123');
      expect(mockWeb3Service.transferToken).toHaveBeenCalledWith('ETH', '0x1234567890123456789012345678901234567890', 1.0);
    });

    it('should handle transfer command with missing parameters', async () => {
      const command: VoiceWeb3Command = {
        action: 'transfer',
        params: {
          amount: 1.0,
          // Missing recipient
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Missing');
    });

    it('should handle transfer command error', async () => {
      mockWeb3Service.transferToken = jest.fn().mockRejectedValue(new Error('Insufficient balance'));

      const command: VoiceWeb3Command = {
        action: 'transfer',
        params: {
          token: 'ETH',
          recipient: '0x1234567890123456789012345678901234567890',
          amount: 1.0,
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Insufficient balance');
    });

    it('should handle swap command (not yet implemented)', async () => {
      const command: VoiceWeb3Command = {
        action: 'swap',
        params: {
          token: 'USDC',
          amount: 100,
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not yet implemented');
    });

    it('should handle stake command (not yet implemented)', async () => {
      const command: VoiceWeb3Command = {
        action: 'stake',
        params: {
          token: 'ETH',
          amount: 10,
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not yet implemented');
    });

    it('should handle vote command (not yet implemented)', async () => {
      const command: VoiceWeb3Command = {
        action: 'vote',
        params: {
          proposalId: '1',
        },
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not yet implemented');
    });

    it('should handle unknown command', async () => {
      const command = {
        action: 'unknown' as any,
        params: {},
      };

      const result = await controller.executeCommand(command);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Unknown command');
    });
  });

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = VoiceWeb3Controller.getInstance();
      const instance2 = VoiceWeb3Controller.getInstance();

      expect(instance1).toBe(instance2);
    });
  });
});

