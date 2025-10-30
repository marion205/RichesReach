# Sepolia Testnet Configuration
# Add these to your main settings.py

# AAVE v3 Configuration
AAVE_POOL_ADDRESSES_PROVIDER = "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e"
AAVE_POOL_ADDRESS = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM"

# Sepolia Asset Addresses (verified from AAVE faucet)
SEPOLIA_ASSETS = {
    "USDC": "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
    "AAVE-USDC": "0x94717b03B39f321c354429f417b4e558c8f7e9d1", 
    "WETH": "0xfff9976782d46CC05630D1f6eBAb18b2324d6B14",
}

# CORS Configuration for Sepolia testing
CORS_ALLOWED_ORIGINS = [
    "process.env.API_BASE_URL || "http://localhost":19006",   # Expo web
    "exp://192.168.1.151:19000", # Expo dev
    "exp://process.env.API_HOST || "localhost":19000",   # Expo local
]

# Rate limiting for testnet
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True
