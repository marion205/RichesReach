/**
 * Hybrid Transaction Service
 * Calls backend risk validator, then sends on-chain tx via WalletConnect.
 * Supports: approve, deposit, borrow, repay, harvest.
 * Includes transaction confirmation polling and backend position recording.
 */
import { ethers } from 'ethers';
import { getReadProvider } from '../blockchain/web3Service';
import { sendTx } from '../blockchain/wallet/walletConnect';
import { ERC20_ABI } from '../blockchain/abi/erc20';
import { AAVE_POOL_ABI } from '../blockchain/abi/aavePool';

type HybridDeps = {
  wcClient: any;
  wcSession: any;
  chainIdWC: string;
  userAddress: string;
  aavePool: string;
  assetMap: Record<string, { address: string; decimals: number }>;
  backendBaseUrl: string; // e.g., https://api.yourapp.com
};

export type TxResult = {
  hash: string;
  confirmed?: boolean;
  blockNumber?: number;
  gasUsed?: string;
};

export class HybridTransactionService {
  constructor(private deps: HybridDeps) {}
  private erc20Iface = new ethers.utils.Interface(ERC20_ABI);
  private poolIface = new ethers.utils.Interface(AAVE_POOL_ABI);

  // ---- Backend validation ----

  private async validate(type: string, data: any) {
    const res = await fetch(`${this.deps.backendBaseUrl}/defi/validate-transaction/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, data, wallet_address: this.deps.userAddress }),
    });
    if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
    const json = await res.json();
    if (!json?.isValid) throw new Error(json?.reason || 'Transaction not allowed by risk engine');
    return json;
  }

  // ---- Backend position recording ----

  private async recordTransaction(data: {
    poolId: string;
    chainId: number;
    txHash: string;
    amount: string;
    action: string;
  }) {
    try {
      const res = await fetch(`${this.deps.backendBaseUrl}/graphql/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `
            mutation RecordStakeTransaction(
              $poolId: String!, $chainId: Int!, $wallet: String!,
              $txHash: String!, $amount: Float!
            ) {
              recordStakeTransaction(
                poolId: $poolId, chainId: $chainId, wallet: $wallet,
                txHash: $txHash, amount: $amount
              ) {
                success
                message
              }
            }
          `,
          variables: {
            poolId: data.poolId,
            chainId: data.chainId,
            wallet: this.deps.userAddress,
            txHash: data.txHash,
            amount: parseFloat(data.amount),
          },
        }),
      });
      const json = await res.json();
      return json?.data?.recordStakeTransaction;
    } catch (error) {
      // Non-critical — transaction already happened on-chain
      console.warn('Failed to record transaction on backend:', error);
      return null;
    }
  }

  // ---- Transaction confirmation polling ----

  /**
   * Wait for a transaction to be confirmed on-chain.
   * Polls every 3 seconds, up to maxWaitMs (default 2 minutes).
   */
  async waitForConfirmation(
    txHash: string,
    confirmations: number = 1,
    maxWaitMs: number = 120_000
  ): Promise<{ confirmed: boolean; blockNumber?: number; gasUsed?: string }> {
    const provider = getReadProvider();
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      try {
        const receipt = await provider.getTransactionReceipt(txHash);
        if (receipt && receipt.confirmations >= confirmations) {
          return {
            confirmed: receipt.status === 1,
            blockNumber: receipt.blockNumber,
            gasUsed: receipt.gasUsed?.toString(),
          };
        }
      } catch (e) {
        // RPC might be slow, keep polling
      }
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }

    return { confirmed: false };
  }

  // ---- Core operations ----

  async approveIfNeeded(symbol: string, amountHuman: string) {
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);

    const erc = new ethers.Contract(asset.address, ERC20_ABI, getReadProvider());
    const allowance = await erc.allowance(userAddress, aavePool);
    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);

    if (allowance.gte(amount)) return { skipped: true, hash: '' };

    const data = this.erc20Iface.encodeFunctionData('approve', [aavePool, amount]);
    const tx = { from: userAddress, to: asset.address, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });

    // Wait for approval to confirm before proceeding
    await this.waitForConfirmation(hash, 1, 60_000);
    return { skipped: false, hash };
  }

  async deposit(symbol: string, amountHuman: string, poolId?: string): Promise<TxResult> {
    await this.validate('deposit', { symbol, amountHuman });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);

    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('deposit', [asset.address, amount, userAddress, 0]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });

    // Wait for confirmation
    const confirmation = await this.waitForConfirmation(hash);

    // Record on backend
    if (poolId) {
      const chainIdNum = parseInt(chainIdWC.split(':')[1], 10);
      await this.recordTransaction({
        poolId,
        chainId: chainIdNum,
        txHash: hash,
        amount: amountHuman,
        action: 'deposit',
      });
    }

    return { hash, ...confirmation };
  }

  async borrow(symbol: string, amountHuman: string, rateMode: 1 | 2 = 2): Promise<TxResult> {
    await this.validate('borrow', { symbol, amountHuman, rateMode });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);

    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('borrow', [
      asset.address, amount, rateMode, 0, userAddress,
    ]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });

    const confirmation = await this.waitForConfirmation(hash);
    return { hash, ...confirmation };
  }

  async repay(symbol: string, amountHuman: string, rateMode: 1 | 2 = 2): Promise<TxResult> {
    await this.validate('repay', { symbol, amountHuman, rateMode });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);

    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('repay', [
      asset.address, amount, rateMode, userAddress,
    ]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });

    const confirmation = await this.waitForConfirmation(hash);
    return { hash, ...confirmation };
  }

  /**
   * Harvest (claim) reward tokens from a staking position.
   * Uses a generic claim function ABI — adjust per protocol.
   */
  async harvest(
    claimContract: string,
    claimFunctionData: string,
    poolId?: string
  ): Promise<TxResult> {
    await this.validate('harvest', { claimContract });
    const { userAddress, chainIdWC, wcClient, wcSession } = this.deps;

    const tx = { from: userAddress, to: claimContract, data: claimFunctionData };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });

    const confirmation = await this.waitForConfirmation(hash);

    if (poolId) {
      const chainIdNum = parseInt(chainIdWC.split(':')[1], 10);
      await this.recordTransaction({
        poolId,
        chainId: chainIdNum,
        txHash: hash,
        amount: '0',
        action: 'harvest',
      });
    }

    return { hash, ...confirmation };
  }
}
