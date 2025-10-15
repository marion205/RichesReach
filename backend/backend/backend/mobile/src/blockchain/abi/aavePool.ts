// AAVE v3 Pool minimal ABI
export const AAVE_POOL_ABI = [
  { "type":"function","name":"deposit","inputs":[
      {"name":"asset","type":"address"},
      {"name":"amount","type":"uint256"},
      {"name":"onBehalfOf","type":"address"},
      {"name":"referralCode","type":"uint16"}
    ],"outputs":[],"stateMutability":"nonpayable" },
  { "type":"function","name":"borrow","inputs":[
      {"name":"asset","type":"address"},
      {"name":"amount","type":"uint256"},
      {"name":"interestRateMode","type":"uint256"}, // 1=stable, 2=variable
      {"name":"referralCode","type":"uint16"},
      {"name":"onBehalfOf","type":"address"}
    ],"outputs":[],"stateMutability":"nonpayable" },
  { "type":"function","name":"repay","inputs":[
      {"name":"asset","type":"address"},
      {"name":"amount","type":"uint256"},
      {"name":"interestRateMode","type":"uint256"},
      {"name":"onBehalfOf","type":"address"}
    ],"outputs":[{"type":"uint256"}],"stateMutability":"nonpayable" },
  { "type":"function","name":"getUserAccountData","inputs":[{"name":"user","type":"address"}],
    "outputs":[
      {"name":"totalCollateralBase","type":"uint256"},
      {"name":"totalDebtBase","type":"uint256"},
      {"name":"availableBorrowsBase","type":"uint256"},
      {"name":"currentLiquidationThreshold","type":"uint256"},
      {"name":"ltv","type":"uint256"},
      {"name":"healthFactor","type":"uint256"}
    ],"stateMutability":"view" }
] as const;
