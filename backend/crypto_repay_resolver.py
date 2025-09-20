"""
Crypto SBLOC Loan Repayment Resolver
Handles GraphQL mutation for repaying SBLOC loans with interest calculation
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RepaySblocLoanResult:
    """Result type for repay SBLOC loan mutation"""
    def __init__(self, success: bool, message: str = "", new_outstanding: float = 0.0, 
                 interest_paid: float = 0.0, principal_paid: float = 0.0, loan: Optional[Dict] = None):
        self.success = success
        self.message = message
        self.new_outstanding = new_outstanding
        self.interest_paid = interest_paid
        self.principal_paid = principal_paid
        self.loan = loan

def repay_sbloc_loan(loan_id: str, amount_usd: float, user_id: str, db_connection) -> RepaySblocLoanResult:
    """
    Process SBLOC loan repayment with interest calculation
    
    Args:
        loan_id: ID of the loan to repay
        amount_usd: Amount to repay in USD
        user_id: ID of the user making the repayment
        db_connection: Database connection (SQLite/PostgreSQL)
    
    Returns:
        RepaySblocLoanResult with repayment details
    """
    
    if amount_usd <= 0:
        return RepaySblocLoanResult(
            success=False, 
            message="Amount must be > 0", 
            new_outstanding=0, 
            interest_paid=0, 
            principal_paid=0
        )
    
    try:
        # 1) Load loan (with user validation)
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT id, loan_amount, interest_rate, status, created_at, updated_at, user_id
            FROM crypto_sbloc_loans 
            WHERE id = ? AND user_id = ?
        """, (loan_id, user_id))
        
        loan_row = cursor.fetchone()
        if not loan_row:
            return RepaySblocLoanResult(
                success=False, 
                message="Loan not found", 
                new_outstanding=0, 
                interest_paid=0, 
                principal_paid=0
            )
        
        loan_id, loan_amount, interest_rate, status, created_at, updated_at, user_id = loan_row
        
        if status in ['REPAID', 'LIQUIDATED']:
            return RepaySblocLoanResult(
                success=False, 
                message=f"Loan is {status}", 
                new_outstanding=loan_amount, 
                interest_paid=0, 
                principal_paid=0
            )
        
        # 2) Compute accrued interest since last update
        apr = float(interest_rate or 0)  # e.g., 0.05
        principal_outstanding = float(loan_amount)  # USD outstanding
        
        # Calculate days since last update
        last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00')) if updated_at else datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days = max(0, (now - last_update).total_seconds() / (24 * 60 * 60))
        
        # Simple interest calculation (non-compounding)
        interest_accrued = principal_outstanding * (apr / 365) * days
        
        # 3) Apply payment: interest first, then principal
        interest_paid = min(amount_usd, interest_accrued)
        principal_paid = max(0, amount_usd - interest_paid)
        new_outstanding = max(0, principal_outstanding - principal_paid)
        
        # 4) Update loan atomically
        new_status = 'REPAID' if new_outstanding == 0 else status
        now_iso = now.isoformat()
        
        cursor.execute("""
            UPDATE crypto_sbloc_loans 
            SET loan_amount = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (new_outstanding, new_status, now_iso, loan_id))
        
        # 5) Log repayment
        cursor.execute("""
            INSERT INTO crypto_loan_repayments 
            (loan_id, user_id, amount_usd, interest_paid, principal_paid, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (loan_id, user_id, amount_usd, interest_paid, principal_paid, now_iso))
        
        # 6) Get updated loan details
        cursor.execute("""
            SELECT id, status, loan_amount, updated_at, 
                   (SELECT symbol FROM cryptocurrencies WHERE id = csl.cryptocurrency_id) as symbol
            FROM crypto_sbloc_loans csl
            WHERE id = ?
        """, (loan_id,))
        
        updated_loan_row = cursor.fetchone()
        updated_loan = {
            'id': updated_loan_row[0],
            'status': updated_loan_row[1],
            'loanAmount': updated_loan_row[2],
            'updatedAt': updated_loan_row[3],
            'cryptocurrency': {'symbol': updated_loan_row[4]}
        } if updated_loan_row else None
        
        db_connection.commit()
        
        logger.info(f"Repayment processed: loan_id={loan_id}, amount={amount_usd}, interest={interest_paid}, principal={principal_paid}")
        
        return RepaySblocLoanResult(
            success=True,
            message="Repayment processed",
            new_outstanding=new_outstanding,
            interest_paid=interest_paid,
            principal_paid=principal_paid,
            loan=updated_loan
        )
        
    except Exception as e:
        logger.error(f"Error processing repayment: {e}")
        db_connection.rollback()
        return RepaySblocLoanResult(
            success=False, 
            message="Could not process repayment", 
            new_outstanding=0, 
            interest_paid=0, 
            principal_paid=0
        )

def create_repayment_table(db_connection):
    """Create repayment history table if it doesn't exist"""
    cursor = db_connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_loan_repayments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            interest_paid REAL NOT NULL,
            principal_paid REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES crypto_sbloc_loans (id)
        )
    """)
    db_connection.commit()
    logger.info("Created crypto_loan_repayments table")

# GraphQL resolver function
def resolve_repay_sbloc_loan(parent, info, loan_id: str, amount_usd: float):
    """
    GraphQL resolver for repaySblocLoan mutation
    
    This would be called from your GraphQL server (Strawberry, Ariadne, etc.)
    """
    # Get database connection and user_id from context
    context = info.context
    db_connection = context.get('db_connection')
    user_id = context.get('user_id', 'demo_user')  # Replace with actual auth
    
    if not db_connection:
        return {
            'success': False,
            'message': 'Database connection not available',
            'newOutstanding': 0.0,
            'interestPaid': 0.0,
            'principalPaid': 0.0,
            'loan': None
        }
    
    result = repay_sbloc_loan(loan_id, amount_usd, user_id, db_connection)
    
    return {
        'success': result.success,
        'message': result.message,
        'newOutstanding': result.new_outstanding,
        'interestPaid': result.interest_paid,
        'principalPaid': result.principal_paid,
        'loan': result.loan
    }
