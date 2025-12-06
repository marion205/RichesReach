/**
 * Account Abstraction Service (ERC-4337)
 * Enables gasless transactions, smart wallets, and session keys
 * 
 * Integrates with:
 * - Stackup Bundler (https://docs.stackup.sh)
 * - Pimlico Paymaster (https://docs.pimlico.io)
 * - Biconomy (https://docs.biconomy.io)
 */

import { ethers } from 'ethers';

export interface SmartWalletConfig {
  bundlerUrl: string;
  paymasterUrl?: string;
  entryPointAddress: string;
  factoryAddress: string;
}

export interface UserOperation {
  sender: string;
  nonce: string;
  initCode: string;
  callData: string;
  callGasLimit: string;
  verificationGasLimit: string;
  preVerificationGas: string;
  maxFeePerGas: string;
  maxPriorityFeePerGas: string;
  paymasterAndData: string;
  signature: string;
}

export interface SessionKey {
  address: string;
  permissions: {
    contracts: string[];
    maxAmount: string;
    expiresAt: number;
  };
  signature: string;
}

class AccountAbstractionService {
  private provider: ethers.providers.JsonRpcProvider | null = null;
  private bundlerUrl: string;
  private paymasterUrl: string | null = null;
  private entryPointAddress: string;
  private factoryAddress: string;
  private smartWalletAddress: string | null = null;

  // ERC-4337 EntryPoint address (same across all networks)
  private readonly ENTRY_POINT_ADDRESS = '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789';
  
  // Pimlico Bundler URLs (using Pimlico for bundling)
  private readonly BUNDLER_URLS = {
    ethereum: 'https://api.pimlico.io/v1/polygon/bundler',
    polygon: 'https://api.pimlico.io/v1/polygon/bundler',
    arbitrum: 'https://api.pimlico.io/v1/arbitrum/bundler',
    optimism: 'https://api.pimlico.io/v1/optimism/bundler',
    base: 'https://api.pimlico.io/v1/base/bundler',
  };

  // Pimlico Paymaster URLs
  private readonly PAYMASTER_URLS = {
    ethereum: 'https://api.pimlico.io/v1/ethereum/rpc?apikey=pim_Zzdnedgr5NjyiSUu6ZNxo9',
    polygon: 'https://api.pimlico.io/v1/polygon/rpc?apikey=pim_Zzdnedgr5NjyiSUu6ZNxo9',
    arbitrum: 'https://api.pimlico.io/v1/arbitrum/rpc?apikey=pim_Zzdnedgr5NjyiSUu6ZNxo9',
    optimism: 'https://api.pimlico.io/v1/optimism/rpc?apikey=pim_Zzdnedgr5NjyiSUu6ZNxo9',
    base: 'https://api.pimlico.io/v1/base/rpc?apikey=pim_Zzdnedgr5NjyiSUu6ZNxo9',
  };

  // Biconomy Paymaster URLs (alternative/backup)
  private readonly BICONOMY_PAYMASTER_URLS = {
    ethereum: 'https://paymaster.biconomy.io/api/v2/84532/mee_K7UTWDUjqJsH14PhBv3JHa',
    polygon: 'https://paymaster.biconomy.io/api/v2/137/mee_K7UTWDUjqJsH14PhBv3JHa',
    arbitrum: 'https://paymaster.biconomy.io/api/v2/42161/mee_K7UTWDUjqJsH14PhBv3JHa',
    optimism: 'https://paymaster.biconomy.io/api/v2/10/mee_K7UTWDUjqJsH14PhBv3JHa',
    base: 'https://paymaster.biconomy.io/api/v2/8453/mee_K7UTWDUjqJsH14PhBv3JHa',
  };

  private readonly PIMLICO_API_KEY = 'pim_Zzdnedgr5NjyiSUu6ZNxo9';
  private readonly BICONOMY_API_KEY = 'mee_K7UTWDUjqJsH14PhBv3JHa';

  constructor(network: 'ethereum' | 'polygon' | 'arbitrum' | 'optimism' | 'base' = 'polygon') {
    this.bundlerUrl = this.BUNDLER_URLS[network];
    this.paymasterUrl = this.PAYMASTER_URLS[network];
    this.entryPointAddress = this.ENTRY_POINT_ADDRESS;
    // Factory address would be your smart wallet factory contract
    this.factoryAddress = '0x...'; // Replace with actual factory address
  }

  /**
   * Create a smart wallet for a user
   * Uses CREATE2 for deterministic addresses
   */
  async createSmartWallet(ownerAddress: string, salt: string = '0x0'): Promise<string> {
    try {
      // Calculate smart wallet address using CREATE2
      // This is deterministic - same owner + salt = same address
      const initCode = this.encodeFactoryCall(ownerAddress, salt);
      
      // Calculate address
      const walletAddress = await this.calculateWalletAddress(ownerAddress, salt);
      this.smartWalletAddress = walletAddress;
      
      return walletAddress;
    } catch (error) {
      console.error('Failed to create smart wallet:', error);
      throw new Error('Failed to create smart wallet');
    }
  }

  /**
   * Get or create smart wallet address (doesn't deploy until first transaction)
   */
  async getSmartWalletAddress(ownerAddress: string): Promise<string> {
    if (this.smartWalletAddress) {
      return this.smartWalletAddress;
    }
    return await this.createSmartWallet(ownerAddress);
  }

  /**
   * Send a user operation (gasless transaction)
   */
  async sendUserOperation(
    target: string,
    data: string,
    value: string = '0',
    sponsorGas: boolean = true
  ): Promise<string> {
    try {
      if (!this.smartWalletAddress) {
        throw new Error('Smart wallet not initialized');
      }

      // Build user operation
      const userOp = await this.buildUserOperation(
        this.smartWalletAddress,
        target,
        data,
        value,
        sponsorGas
      );

      // Send to bundler
      const txHash = await this.sendToBundler(userOp);
      
      return txHash;
    } catch (error) {
      console.error('Failed to send user operation:', error);
      throw new Error('Failed to send user operation');
    }
  }

  /**
   * Build a user operation
   */
  private async buildUserOperation(
    sender: string,
    target: string,
    data: string,
    value: string,
    sponsorGas: boolean
  ): Promise<UserOperation> {
    // Get nonce
    const nonce = await this.getNonce(sender);
    
    // Build call data
    const callData = this.encodeExecuteCall(target, value, data);
    
    // Estimate gas
    const gasEstimates = await this.estimateGas(sender, target, data, value);
    
    // Get paymaster data if sponsoring gas
    let paymasterAndData = '0x';
    if (sponsorGas && this.paymasterUrl) {
      paymasterAndData = await this.getPaymasterData(sender, gasEstimates);
    }

    return {
      sender,
      nonce: nonce.toString(),
      initCode: '0x', // Empty if wallet already deployed
      callData,
      callGasLimit: gasEstimates.callGasLimit,
      verificationGasLimit: gasEstimates.verificationGasLimit,
      preVerificationGas: gasEstimates.preVerificationGas,
      maxFeePerGas: gasEstimates.maxFeePerGas,
      maxPriorityFeePerGas: gasEstimates.maxPriorityFeePerGas,
      paymasterAndData,
      signature: '0x', // Will be signed by owner
    };
  }

  /**
   * Create a session key for passwordless transactions
   */
  async createSessionKey(
    ownerSigner: ethers.Signer,
    permissions: {
      contracts: string[];
      maxAmount: string;
      expiresAt: number;
    }
  ): Promise<SessionKey> {
    try {
      // Create message for session key
      const message = ethers.utils.solidityKeccak256(
        ['address[]', 'uint256', 'uint256'],
        [permissions.contracts, permissions.maxAmount, permissions.expiresAt]
      );

      // Sign with owner's private key
      const signature = await ownerSigner.signMessage(ethers.utils.arrayify(message));

      // Derive session key address (simplified - in production, use proper key derivation)
      const sessionKeyAddress = ethers.utils.getAddress(
        ethers.utils.keccak256(signature).slice(0, 42)
      );

      return {
        address: sessionKeyAddress,
        permissions,
        signature,
      };
    } catch (error) {
      console.error('Failed to create session key:', error);
      throw new Error('Failed to create session key');
    }
  }

  /**
   * Check if session key is valid
   */
  async validateSessionKey(sessionKey: SessionKey, ownerAddress: string): Promise<boolean> {
    try {
      // Check expiration
      if (Date.now() / 1000 > sessionKey.permissions.expiresAt) {
        return false;
      }

      // Verify signature
      const message = ethers.utils.solidityKeccak256(
        ['address[]', 'uint256', 'uint256'],
        [
          sessionKey.permissions.contracts,
          sessionKey.permissions.maxAmount,
          sessionKey.permissions.expiresAt,
        ]
      );

      const recoveredAddress = ethers.utils.verifyMessage(
        ethers.utils.arrayify(message),
        sessionKey.signature
      );

      return recoveredAddress.toLowerCase() === ownerAddress.toLowerCase();
    } catch (error) {
      console.error('Failed to validate session key:', error);
      return false;
    }
  }

  /**
   * Send user operation to bundler (Pimlico)
   */
  private async sendToBundler(userOp: UserOperation): Promise<string> {
    try {
      const response = await fetch(this.bundlerUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': this.PIMLICO_API_KEY,
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'eth_sendUserOperation',
          params: [userOp, this.entryPointAddress],
          id: Date.now(),
        }),
      });

      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error.message);
      }

      return result.result;
    } catch (error) {
      console.error('Failed to send to bundler:', error);
      throw error;
    }
  }

  /**
   * Get paymaster data for gas sponsorship (Pimlico)
   */
  private async getPaymasterData(
    sender: string,
    gasEstimates: any
  ): Promise<string> {
    if (!this.paymasterUrl) {
      return '0x';
    }

    try {
      // Pimlico paymaster API
      const response = await fetch(this.paymasterUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'pm_sponsorUserOperation',
          params: [
            {
              sender,
              callData: '0x', // Will be filled by bundler
              callGasLimit: gasEstimates.callGasLimit,
              verificationGasLimit: gasEstimates.verificationGasLimit,
              preVerificationGas: gasEstimates.preVerificationGas,
              maxFeePerGas: gasEstimates.maxFeePerGas,
              maxPriorityFeePerGas: gasEstimates.maxPriorityFeePerGas,
            },
            {
              entryPoint: this.entryPointAddress,
            },
          ],
          id: Date.now(),
        }),
      });

      const result = await response.json();
      
      if (result.error) {
        console.warn('Pimlico paymaster failed, trying Biconomy:', result.error);
        return await this.getBiconomyPaymasterData(sender, gasEstimates);
      }

      return result.result?.paymasterAndData || '0x';
    } catch (error) {
      console.error('Failed to get Pimlico paymaster data:', error);
      // Fallback to Biconomy
      return await this.getBiconomyPaymasterData(sender, gasEstimates);
    }
  }

  /**
   * Get paymaster data from Biconomy (fallback)
   */
  private async getBiconomyPaymasterData(
    sender: string,
    gasEstimates: any
  ): Promise<string> {
    try {
      // Get network from current chain
      const network = 'polygon'; // Default, should be dynamic
      const biconomyUrl = this.BICONOMY_PAYMASTER_URLS[network as keyof typeof this.BICONOMY_PAYMASTER_URLS];
      
      if (!biconomyUrl) {
        return '0x';
      }

      const response = await fetch(biconomyUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender,
          ...gasEstimates,
        }),
      });

      const result = await response.json();
      return result.paymasterAndData || '0x';
    } catch (error) {
      console.error('Failed to get Biconomy paymaster data:', error);
      return '0x';
    }
  }

  /**
   * Estimate gas for user operation
   */
  private async estimateGas(
    sender: string,
    target: string,
    data: string,
    value: string
  ): Promise<any> {
    // Simplified - in production, use proper gas estimation
    return {
      callGasLimit: '100000',
      verificationGasLimit: '100000',
      preVerificationGas: '50000',
      maxFeePerGas: '1000000000', // 1 gwei
      maxPriorityFeePerGas: '1000000000',
    };
  }

  /**
   * Get nonce for smart wallet
   */
  private async getNonce(sender: string): Promise<number> {
    // In production, query EntryPoint contract for nonce
    return 0;
  }

  /**
   * Encode execute call for smart wallet
   */
  private encodeExecuteCall(target: string, value: string, data: string): string {
    // ERC-4337 execute function signature
    const executeInterface = new ethers.utils.Interface([
      'function execute(address to, uint256 value, bytes calldata data) external',
    ]);
    
    return executeInterface.encodeFunctionData('execute', [target, value, data]);
  }

  /**
   * Encode factory call for wallet creation
   */
  private encodeFactoryCall(owner: string, salt: string): string {
    // Factory createAccount function
    const factoryInterface = new ethers.utils.Interface([
      'function createAccount(address owner, uint256 salt) external returns (address)',
    ]);
    
    return factoryInterface.encodeFunctionData('createAccount', [owner, salt]);
  }

  /**
   * Calculate wallet address using CREATE2
   */
  private async calculateWalletAddress(owner: string, salt: string): Promise<string> {
    // Simplified - in production, use proper CREATE2 calculation
    const initCode = this.encodeFactoryCall(owner, salt);
    const initCodeHash = ethers.utils.keccak256(initCode);
    
    // CREATE2: keccak256(0xff ++ deployer ++ salt ++ keccak256(init_code))[12:]
    const address = ethers.utils.getAddress(
      ethers.utils.keccak256(
        ethers.utils.solidityPack(
          ['bytes1', 'address', 'bytes32', 'bytes32'],
          ['0xff', this.factoryAddress, salt, initCodeHash]
        )
      ).slice(-40)
    );
    
    return address;
  }

  /**
   * Check if smart wallet is deployed
   */
  async isWalletDeployed(address: string): Promise<boolean> {
    try {
      if (!this.provider) {
        return false;
      }
      const code = await this.provider.getCode(address);
      return code !== '0x';
    } catch (error) {
      return false;
    }
  }

  /**
   * Get wallet balance
   */
  async getWalletBalance(address: string): Promise<string> {
    try {
      if (!this.provider) {
        throw new Error('Provider not initialized');
      }
      const balance = await this.provider.getBalance(address);
      return ethers.utils.formatEther(balance);
    } catch (error) {
      console.error('Failed to get wallet balance:', error);
      throw error;
    }
  }
}

export default AccountAbstractionService;

