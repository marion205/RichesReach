#!/usr/bin/env python3
import asyncio
import aiohttp

async def test_finnhub():
    """Test FinnHub API directly"""
    try:
        print("🚀 Testing FinnHub API...")
        async with aiohttp.ClientSession() as session:
            quote_url = "https://finnhub.io/api/v1/quote?symbol=AAPL&token=d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
            async with session.get(quote_url) as response:
                if response.status == 200:
                    quote_data = await response.json()
                    print(f"✅ AAPL Quote: {quote_data}")
                    return quote_data
                else:
                    print(f"❌ Error: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_finnhub())
    print(f"Result: {result}")
