// Minimal ERC-20 ABI fragments
export const ERC20_ABI = [
  { "type":"function","name":"approve","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}], "stateMutability":"nonpayable" },
  { "type":"function","name":"allowance","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"type":"uint256"}],"stateMutability":"view" },
  { "type":"function","name":"balanceOf","inputs":[{"name":"account","type":"address"}],"outputs":[{"type":"uint256"}],"stateMutability":"view" },
  { "type":"function","name":"decimals","inputs":[],"outputs":[{"type":"uint8"}],"stateMutability":"view" }
] as const;
