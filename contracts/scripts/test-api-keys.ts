/**
 * Test API Keys Script
 * Verifies Pimlico and Biconomy API keys are working
 */

const PIMLICO_API_KEY = "pim_Zzdnedgr5NjyiSUu6ZNxo9";
const BICONOMY_API_KEY = "mee_K7UTWDUjqJsH14PhBv3JHa";

async function testPimlico() {
  console.log("🔍 Testing Pimlico API Key...");
  
  try {
    // Test bundler endpoint
    const bundlerUrl = `https://api.pimlico.io/v1/polygon/bundler`;
    const response = await fetch(bundlerUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": PIMLICO_API_KEY,
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "eth_chainId",
        params: [],
        id: 1,
      }),
    });

    const result = await response.json();
    
    if (result.error) {
      console.log("❌ Pimlico Bundler Error:", result.error);
      return false;
    }

    console.log("✅ Pimlico Bundler: Connected");
    console.log("   Chain ID:", result.result);

    // Test paymaster endpoint
    const paymasterUrl = `https://api.pimlico.io/v1/polygon/rpc?apikey=${PIMLICO_API_KEY}`;
    const paymasterResponse = await fetch(paymasterUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "pm_getPaymasterStatus",
        params: [],
        id: 1,
      }),
    });

    const paymasterResult = await paymasterResponse.json();
    
    if (paymasterResult.error) {
      console.log("⚠️  Pimlico Paymaster Error:", paymasterResult.error);
      console.log("   (This is normal if paymaster isn't configured yet)");
    } else {
      console.log("✅ Pimlico Paymaster: Connected");
    }

    return true;
  } catch (error: any) {
    console.log("❌ Pimlico Test Failed:", error.message);
    return false;
  }
}

async function testBiconomy() {
  console.log("\n🔍 Testing Biconomy API Key...");
  
  try {
    // Test paymaster endpoint (Polygon mainnet)
    const paymasterUrl = `https://paymaster.biconomy.io/api/v2/137/${BICONOMY_API_KEY}`;
    const response = await fetch(paymasterUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();
    
    if (result.error || response.status !== 200) {
      console.log("❌ Biconomy Paymaster Error:", result.error || result);
      return false;
    }

    console.log("✅ Biconomy Paymaster: Connected");
    console.log("   Status:", result.status || "OK");
    return true;
  } catch (error: any) {
    console.log("❌ Biconomy Test Failed:", error.message);
    return false;
  }
}

async function main() {
  console.log("=".repeat(60));
  console.log("🔑 API KEY TESTING");
  console.log("=".repeat(60));

  const pimlicoResult = await testPimlico();
  const biconomyResult = await testBiconomy();

  console.log("\n" + "=".repeat(60));
  console.log("📊 TEST RESULTS");
  console.log("=".repeat(60));
  console.log(`Pimlico: ${pimlicoResult ? "✅ PASS" : "❌ FAIL"}`);
  console.log(`Biconomy: ${biconomyResult ? "✅ PASS" : "❌ FAIL"}`);
  console.log("=".repeat(60));

  if (pimlicoResult && biconomyResult) {
    console.log("\n✅ All API keys are working!");
    process.exit(0);
  } else {
    console.log("\n⚠️  Some API keys failed. Check the errors above.");
    process.exit(1);
  }
}

main();

