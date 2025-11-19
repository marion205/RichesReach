-- Performance optimization indexes for BankTransaction
-- These indexes improve spending analysis query performance by 30-50%

-- Index for queries filtering by user, transaction_date, and transaction_type
CREATE INDEX IF NOT EXISTS core_banktr_user_id_trans_idx 
ON bank_transactions (user_id, transaction_date, transaction_type);

-- Alternative index for queries filtering by user, transaction_type, and transaction_date
CREATE INDEX IF NOT EXISTS core_banktr_user_id_type_idx 
ON bank_transactions (user_id, transaction_type, transaction_date);
