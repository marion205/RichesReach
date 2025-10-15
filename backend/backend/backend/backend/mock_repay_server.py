"""
Mock Crypto Repay Server
Provides a mock GraphQL endpoint for testing repay functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import random
from datetime import datetime, timezone

app = FastAPI(title="Mock Crypto Repay Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database
mock_loans = {
    "loan_1": {
        "id": "loan_1",
        "status": "ACTIVE",
        "loanAmount": 5000.0,
        "interestRate": 0.05,  # 5% APR
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-15T00:00:00Z",
        "cryptocurrency": {"symbol": "BTC"}
    },
    "loan_2": {
        "id": "loan_2", 
        "status": "ACTIVE",
        "loanAmount": 2500.0,
        "interestRate": 0.06,  # 6% APR
        "createdAt": "2024-01-10T00:00:00Z",
        "updatedAt": "2024-01-20T00:00:00Z",
        "cryptocurrency": {"symbol": "ETH"}
    }
}

# Request/Response models
class RepayRequest(BaseModel):
    loanId: str
    amountUsd: float

class RepayResponse(BaseModel):
    success: bool
    message: str
    newOutstanding: float
    interestPaid: float
    principalPaid: float
    loan: Optional[Dict[str, Any]] = None

def calculate_interest(loan: Dict[str, Any], days: int) -> float:
    """Calculate accrued interest for a loan"""
    principal = loan["loanAmount"]
    apr = loan["interestRate"]
    return principal * (apr / 365) * days

def process_repayment(loan_id: str, amount_usd: float) -> RepayResponse:
    """Process a loan repayment"""
    
    if amount_usd <= 0:
        return RepayResponse(
            success=False,
            message="Amount must be > 0",
            newOutstanding=0,
            interestPaid=0,
            principalPaid=0
        )
    
    # Get loan
    loan = mock_loans.get(loan_id)
    if not loan:
        return RepayResponse(
            success=False,
            message="Loan not found",
            newOutstanding=0,
            interestPaid=0,
            principalPaid=0
        )
    
    if loan["status"] in ["REPAID", "LIQUIDATED"]:
        return RepayResponse(
            success=False,
            message=f"Loan is {loan['status']}",
            newOutstanding=loan["loanAmount"],
            interestPaid=0,
            principalPaid=0
        )
    
    # Calculate interest (simulate 7 days since last update)
    days_accrued = 7
    interest_accrued = calculate_interest(loan, days_accrued)
    
    # Apply payment: interest first, then principal
    interest_paid = min(amount_usd, interest_accrued)
    principal_paid = max(0, amount_usd - interest_paid)
    new_outstanding = max(0, loan["loanAmount"] - principal_paid)
    
    # Update loan
    loan["loanAmount"] = new_outstanding
    loan["status"] = "REPAID" if new_outstanding == 0 else loan["status"]
    loan["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    return RepayResponse(
        success=True,
        message="Repayment processed",
        newOutstanding=new_outstanding,
        interestPaid=interest_paid,
        principalPaid=principal_paid,
        loan=loan
    )

@app.post("/api/crypto/repay", response_model=RepayResponse)
async def repay_loan(request: RepayRequest):
    """Repay a SBLOC loan"""
    try:
        result = process_repayment(request.loanId, request.amountUsd)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crypto/loans")
async def get_loans():
    """Get all loans for testing"""
    return {"loans": list(mock_loans.values())}

@app.get("/api/crypto/loans/{loan_id}")
async def get_loan(loan_id: str):
    """Get specific loan"""
    loan = mock_loans.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return {"loan": loan}

# GraphQL endpoint (simplified)
@app.post("/graphql")
async def graphql_endpoint(request: Dict[str, Any]):
    """Simple GraphQL endpoint for repay mutation"""
    query = request.get("query", "")
    variables = request.get("variables", {})
    
    if "repaySblocLoan" in query:
        # Extract from variables or try to parse from query string
        loan_id = variables.get("loanId")
        amount_usd = variables.get("amountUsd")
        
        # If not in variables, try to extract from query string
        if not loan_id or amount_usd is None:
            import re
            loan_match = re.search(r'loanId:\s*"([^"]+)"', query)
            amount_match = re.search(r'amountUsd:\s*([0-9.]+)', query)
            if loan_match:
                loan_id = loan_match.group(1)
            if amount_match:
                amount_usd = float(amount_match.group(1))
        
        if not loan_id or amount_usd is None:
            return {
                "data": {
                    "repaySblocLoan": {
                        "success": False,
                        "message": "Missing loanId or amountUsd",
                        "newOutstanding": 0,
                        "interestPaid": 0,
                        "principalPaid": 0,
                        "loan": None
                    }
                }
            }
        
        result = process_repayment(loan_id, amount_usd)
        return {
            "data": {
                "repaySblocLoan": {
                    "success": result.success,
                    "message": result.message,
                    "newOutstanding": result.newOutstanding,
                    "interestPaid": result.interestPaid,
                    "principalPaid": result.principalPaid,
                    "loan": result.loan
                }
            }
        }
    
    return {"data": None, "errors": [{"message": "Query not supported"}]}

@app.get("/")
async def root():
    return {
        "message": "Mock Crypto Repay Server",
        "endpoints": [
            "POST /api/crypto/repay",
            "GET /api/crypto/loans",
            "GET /api/crypto/loans/{loan_id}",
            "POST /graphql"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Mock Crypto Repay Server on port 8128...")
    print("📊 Endpoints available:")
    print("   POST /api/crypto/repay")
    print("   GET  /api/crypto/loans")
    print("   POST /graphql")
    uvicorn.run(app, host="0.0.0.0", port=8128)
