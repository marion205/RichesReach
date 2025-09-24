# Environment variables for hybrid transaction flow
# Add these to your main settings.py or .env file

# Blockchain Configuration
AAVE_POOL_ADDRESS = "<AAVE_POOL_ADDRESS>"  # e.g., "0x794a61358D6845594F94dc1DB02A252b5b4814aD" (Polygon v3)
CHAINLINK_USDC_USD_FEED = "<FEED_ADDR>"     # optional if you validate prices
RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/<ALCHEMY_KEY>"

# Testnet Configuration (for development)
# AAVE_POOL_ADDRESS = "0x6C9fB0D5bD9429eb0Cd11661Fd4f3C5c5De81F8c"  # Polygon Amoy testnet
# RPC_URL = "https://polygon-amoy.g.alchemy.com/v2/<ALCHEMY_KEY>"

# Asset Addresses (Polygon Mainnet)
ASSET_ADDRESSES = {
    'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
    'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
    'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
    'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
    'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
}

# Testnet Asset Addresses (Polygon Amoy)
TESTNET_ASSET_ADDRESSES = {
    'USDC': '0x41E94Eb019C0762f9BfF9fE4e6C21d348E0E9a6',
    'WETH': '0x7c68C7866A64FA2160F78EEaE1220FF21e0a5140',
    'WMATIC': '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
}
