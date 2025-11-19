# AI/ML Stock & Crypto Recommendation System - How It Works

## Current Implementation ✅

### What the System DOES Use:

#### 1. **User Profile Data** (from Income Profile)
The system uses the following user profile data for AI/ML recommendations:

- ✅ **Age** - Used to adjust risk tolerance and investment horizon
- ✅ **Income Bracket** - Used to determine budget capacity (e.g., "Under $30,000", "$100,000 - $150,000")
- ✅ **Risk Tolerance** - Conservative, Moderate, or Aggressive
- ✅ **Investment Goals** - Retirement, Buy a Home, Emergency Fund, Wealth Building, etc.
- ✅ **Investment Horizon** - 1-3 years, 3-5 years, 5-10 years, 10+ years
- ✅ **Investment Experience** - Beginner, Intermediate, Advanced, Expert
- ✅ **Tax Bracket** - Used for tax-optimized recommendations

#### 2. **ML Feature Engineering**
The system creates a 25-feature vector from:
- User profile (7 features: age, income, risk, horizon, experience, tax, goals)
- Market conditions (market features)
- Stock characteristics (beginner-friendly score, ESG, value, momentum)

#### 3. **AI/ML Models Used**
- **MLStockRecommender** - Generates personalized stock recommendations
- **Portfolio Optimizer** - ML model for optimal asset allocation
- **Stock Scorer** - ML model that scores stocks based on user profile
- **Market Regime Predictor** - Predicts market conditions

### Example: How Recommendations Are Generated

```python
# From ml_service.py - User profile features used:
user_features = [
    age / 100.0,                    # Normalized age
    income_encoding[income_bracket], # Income bracket (0.2 to 1.0)
    risk_encoding[risk_tolerance],   # Risk (0.3=Conservative, 0.9=Aggressive)
    horizon_encoding[horizon],       # Investment horizon
    experience_encoding[experience],  # Investment experience
    tax_encoding[tax_bracket],       # Tax bracket
    goal_score                       # Investment goals weighted score
]
```

## What the System DOES NOT Currently Use ❌

### Missing Features:

1. **❌ Spending Habits Analysis**
   - The system does NOT analyze transaction history
   - Does NOT track spending patterns
   - Does NOT use spending behavior to adjust recommendations

2. **❌ Dynamic Budget Calculation**
   - Uses static income bracket from profile
   - Does NOT calculate available budget from spending patterns
   - Does NOT adjust recommendations based on actual spending vs. income

3. **❌ Transaction-Based Recommendations**
   - Bank transactions are stored (via Yodlee integration)
   - But transactions are NOT used for stock/crypto recommendations
   - Transactions are only used for banking/accounting features

## How It Currently Works

### Stock Recommendations Flow:

1. **User Creates Income Profile** → Stores: age, income bracket, risk tolerance, goals
2. **ML System Reads Profile** → Creates feature vector from profile data
3. **ML Models Score Stocks** → Uses user features + market data + stock characteristics
4. **Recommendations Generated** → Personalized based on risk tolerance, goals, income bracket

### Example Recommendation Logic:

```python
# Conservative user (low income, conservative risk):
- Recommends: VTI (40%), BND (35%), VXUS (15%), REIT (10%)
- Expected return: 6.5%
- Focus: Capital preservation

# Aggressive user (high income, aggressive risk):
- Recommends: Growth stocks (70%), Individual stocks (20%), International (10%)
- Expected return: 12-15%
- Focus: Wealth building
```

## Potential Enhancement: Adding Spending Habits Analysis 💡

### What Could Be Added:

1. **Transaction Analysis**
   - Analyze bank transactions to understand spending patterns
   - Calculate discretionary income (income - expenses)
   - Track spending categories (food, travel, subscriptions, etc.)

2. **Dynamic Budget Calculation**
   - Calculate available investment budget from: `Income - Essential Expenses - Savings Goal`
   - Adjust recommendations based on actual available budget
   - Suggest investment amounts based on spending patterns

3. **Spending-Based Stock Recommendations**
   - If user spends heavily on tech → Recommend tech stocks
   - If user travels frequently → Recommend travel/leisure stocks
   - If user has high subscription spending → Recommend subscription-based companies

### Implementation Example:

```python
# Potential enhancement in ml_service.py:
def _analyze_spending_habits(self, user_id):
    """Analyze user spending from transaction history"""
    transactions = BankTransaction.objects.filter(user_id=user_id)
    
    spending_by_category = {}
    for txn in transactions:
        category = categorize_transaction(txn.description)
        spending_by_category[category] += txn.amount
    
    # Calculate discretionary income
    monthly_income = get_monthly_income(user_id)
    monthly_expenses = sum(spending_by_category.values())
    discretionary_income = monthly_income - monthly_expenses
    
    return {
        'spending_by_category': spending_by_category,
        'discretionary_income': discretionary_income,
        'spending_habits': analyze_patterns(transactions)
    }

def _enhance_recommendations_with_spending(self, user_profile, spending_analysis):
    """Enhance recommendations based on spending habits"""
    # If user spends on tech, weight tech stocks higher
    if spending_analysis['spending_by_category'].get('Technology', 0) > threshold:
        tech_stocks_weight += 0.2
    
    # Adjust budget based on discretionary income
    available_budget = spending_analysis['discretionary_income'] * 0.3  # 30% of discretionary
    recommendations['suggested_investment_amount'] = available_budget
```

## Summary

### ✅ Currently Implemented:
- **User Profile**: Age, income bracket, risk tolerance, goals, horizon, experience, tax bracket
- **ML Models**: Stock scoring, portfolio optimization, market regime prediction
- **Personalization**: Recommendations based on risk tolerance and investment goals

### ❌ Not Currently Implemented:
- **Spending Habits**: Transaction history analysis
- **Dynamic Budget**: Calculation from spending patterns
- **Spending-Based Recommendations**: Stock suggestions based on spending categories

### 💡 Recommendation:
The system has a solid foundation with user profile-based recommendations. To answer your question:

**Yes, the system uses AI/ML to recommend stocks/crypto based on:**
- ✅ User profile (age, income bracket, risk tolerance, goals)
- ✅ Investment habits (risk tolerance, experience level)
- ✅ Budget capacity (income bracket)

**But it does NOT currently use:**
- ❌ Spending habits from transaction history
- ❌ Dynamic budget calculation from actual spending

**To add spending habits analysis**, you would need to:
1. Integrate transaction analysis from `BankTransaction` model
2. Add spending pattern analysis to ML feature engineering
3. Enhance recommendations to consider spending categories
4. Calculate dynamic budget from discretionary income

---

**Files to Review:**
- `deployment_package/backend/core/ml_service.py` - ML feature engineering
- `deployment_package/backend/core/ml_mutations.py` - ML recommendation generation
- `deployment_package/backend/core/banking_models.py` - Transaction storage
- `main_server.py` (lines 2111-2420) - AI recommendations handler

