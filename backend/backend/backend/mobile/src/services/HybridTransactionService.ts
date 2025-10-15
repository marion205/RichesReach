/**
 * Hybrid service: calls backend risk validator, then sends on-chain tx via WalletConnect.
 * Supports: approve -> deposit, borrow, repay
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

export class HybridTransactionService {
  constructor(private deps: HybridDeps) {}
  private erc20Iface = new ethers.utils.Interface(ERC20_ABI);
  private poolIface = new ethers.utils.Interface(AAVE_POOL_ABI);

  private async validate(type: string, data: any) {
    const res = await fetch(`${this.deps.backendBaseUrl}/defi/validate-transaction/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, data, wallet_address: this.deps.userAddress })
    });
    if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
    const json = await res.json();
    if (!json?.isValid) throw new Error(json?.reason || 'Transaction not allowed by risk engine');
    return json;
  }

  async approveIfNeeded(symbol: string, amountHuman: string) {
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);

    const erc = new ethers.Contract(asset.address, ERC20_ABI, getReadProvider());
    const allowance = await erc.allowance(userAddress, aavePool);
    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);

    if (allowance >= amount) return { skipped: true };

    const data = this.erc20Iface.encodeFunctionData('approve', [aavePool, amount]);
    const tx = { from: userAddress, to: asset.address, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });
    return { skipped: false, hash };
  }

  async deposit(symbol: string, amountHuman: string) {
    await this.validate('deposit', { symbol, amountHuman });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);
    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('deposit', [asset.address, amount, userAddress, 0]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });
    return { hash };
  }

  async borrow(symbol: string, amountHuman: string, rateMode: 1|2 = 2) {
    await this.validate('borrow', { symbol, amountHuman, rateMode });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);
    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('borrow', [asset.address, amount, rateMode, 0, userAddress]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });
    return { hash };
  }

  async repay(symbol: string, amountHuman: string, rateMode: 1|2 = 2) {
    await this.validate('repay', { symbol, amountHuman, rateMode });
    const { aavePool, userAddress, chainIdWC, wcClient, wcSession, assetMap } = this.deps;
    const asset = assetMap[symbol];
    if (!asset) throw new Error(`Unknown asset symbol: ${symbol}`);
    const amount = ethers.utils.parseUnits(amountHuman, asset.decimals);
    const data = this.poolIface.encodeFunctionData('repay', [asset.address, amount, rateMode, userAddress]);
    const tx = { from: userAddress, to: aavePool, data };
    const hash = await sendTx({ client: wcClient, session: wcSession, chainIdWC, tx });
    return { hash };
  }
}