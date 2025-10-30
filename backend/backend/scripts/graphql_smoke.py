# scripts/graphql_smoke.py
import os, json, time
import requests

BASE = os.environ.get("API_URL", "http://process.env.API_HOST || "localhost":8001/graphql/")
EMAIL = os.environ.get("AUTH_EMAIL", "test@example.com")
PASSWORD = os.environ.get("AUTH_PASSWORD", "testpass123")

def post(q, variables=None, token=None, name=""):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"JWT {token}"
    r = requests.post(BASE, json={"query": q, "variables": variables or {}}, headers=h, timeout=30)
    ok = (r.status_code == 200) and ("errors" not in r.json())
    print(f"[{'OK' if ok else 'FAIL'}] {name or 'query'}  HTTP {r.status_code}")
    if r.status_code != 200 or "errors" in r.json():
        try:
            print(json.dumps(r.json(), indent=2)[:2000])
        except:  # noqa
            print(r.text[:1000])
    return r.json() if r.headers.get("content-type","").startswith("application/json") else {"raw": r.text}

# --- Queries/Mutations --- #

PING = """query { ping }"""

TOKEN_AUTH = """
mutation($email:String!, $password:String!){
  tokenAuth(email:$email, password:$password){ token user { id email name } }
}
"""

ME = """query { me { id email name } }"""

GET_SIGNALS = """
query($minMlScore:Float,$isActive:Boolean,$limit:Int){
  signals(minMlScore:$minMlScore,isActive:$isActive,limit:$limit){
    id symbol signalType mlScore thesis isActive
    createdBy { id name }
  }
}
"""

LEADERBOARD = """
query{
  leaderboard{
    rank winRate totalReturn
    user { id name }
  }
}
"""

PORTFOLIO_METRICS = """
query{
  portfolioMetrics{
    totalValue totalCost totalReturn totalReturnPercent
    holdings{ symbol companyName shares currentPrice totalValue returnPercent }
  }
}
"""

CALC_POSITION = """
query($accountEquity:Float!,$entry:Float!,$stop:Float!,$risk:Float,$maxPct:Float,$conf:Float){
  calculatePositionSize(
    accountEquity:$accountEquity, entryPrice:$entry, stopPrice:$stop,
    riskPerTrade:$risk, maxPositionPct:$maxPct, confidence:$conf
  ){
    positionSize positionValue dollarRisk positionPct riskPerTradePct method
  }
}
"""

CALC_STOP = """
query($entry:Float!,$atr:Float!,$mult:Float){
  calculateDynamicStop(entryPrice:$entry, atr:$atr, atrMultiplier:$mult){
    stopPrice stopDistance riskPercentage method
  }
}
"""

CALC_TARGET = """
query($entry:Float!,$stop:Float!,$rr:Float){
  calculateTargetPrice(entryPrice:$entry, stopPrice:$stop, riskRewardRatio:$rr){
    targetPrice rewardDistance riskRewardRatio method
  }
}
"""

def main():
    print(f"Testing {BASE}\n")

    post(PING, name="ping")
    token = None

    # Auth (non-fatal if it fails for your dev DB)
    j = post(TOKEN_AUTH, {"email": EMAIL, "password": PASSWORD}, name="tokenAuth")
    token = None
    if j and j.get("data") and j["data"].get("tokenAuth"):
        token = j["data"]["tokenAuth"].get("token")

    # Me (works with/without token depending on your schema)
    post(ME, token=token, name="me")

    # Core UI calls
    post(GET_SIGNALS, {"minMlScore":0.5,"isActive":True,"limit":10}, token=token, name="signals")
    post(LEADERBOARD, token=token, name="leaderboard")
    post(PORTFOLIO_METRICS, token=token, name="portfolioMetrics")

    # Risk + backtest light checks (safe defaults)
    post(CALC_POSITION, {"accountEquity":10000,"entry":100,"stop":95,"risk":0.01,"maxPct":0.1,"conf":0.8}, name="calculatePositionSize")
    post(CALC_STOP, {"entry":100,"atr":2.0,"mult":1.5}, name="calculateDynamicStop")
    post(CALC_TARGET, {"entry":100,"stop":95,"rr":2.0}, name="calculateTargetPrice")

    print("\nDone.")

if __name__ == "__main__":
    main()
