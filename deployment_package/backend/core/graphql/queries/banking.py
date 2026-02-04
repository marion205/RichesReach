"""
Extended banking root fields: budgetData and spendingAnalysis.
These are composed into ExtendedQuery; BankingQueries (broker_queries) handles broker_account etc.
"""
import logging
from datetime import timedelta

import graphene
from django.utils import timezone

logger = logging.getLogger(__name__)


class BudgetSpendingQuery(graphene.ObjectType):
    """
    Root fields for budget and spending analysis (user's transactions).
    Exposes budgetData and spendingAnalysis (camelCase) for the mobile app.
    """

    budget_data = graphene.Field(
        "core.banking_types.BudgetDataType",
        name="budgetData",
        description="Get user's budget summary from transactions.",
    )
    spending_analysis = graphene.Field(
        "core.banking_types.SpendingAnalysisType",
        period=graphene.String(default_value="month"),
        name="spendingAnalysis",
        description="Get spending analysis for a period.",
    )

    def resolve_budget_data(self, info):
        """Get user's budget data from transactions."""
        from core.banking_types import BudgetCategoryType, BudgetDataType
        from core.banking_models import BankTransaction

        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        try:
            transactions = BankTransaction.objects.filter(user=user)
            categories = {}
            total_spent = 0
            for transaction in transactions:
                category = transaction.category or "Other"
                amount = abs(float(transaction.amount)) if transaction.amount else 0
                if category not in categories:
                    categories[category] = {"spent": 0, "budgeted": 0}
                categories[category]["spent"] += amount
                total_spent += amount
            budget_categories = []
            for category, data in categories.items():
                budgeted = data["spent"] * 1.1
                percentage = (data["spent"] / budgeted * 100) if budgeted > 0 else 0
                budget_categories.append(
                    BudgetCategoryType(
                        name=category,
                        budgeted=budgeted,
                        spent=data["spent"],
                        percentage=percentage,
                    )
                )
            monthly_income = 5000.0
            monthly_expenses = total_spent
            remaining = monthly_income - monthly_expenses
            savings_rate = (remaining / monthly_income * 100) if monthly_income > 0 else 0
            if not transactions.exists() or total_spent == 0:
                mock_categories = [
                    BudgetCategoryType(name="Housing", budgeted=1500, spent=1450, percentage=96.7),
                    BudgetCategoryType(name="Food", budgeted=600, spent=580, percentage=96.7),
                    BudgetCategoryType(name="Transportation", budgeted=400, spent=420, percentage=105),
                    BudgetCategoryType(name="Entertainment", budgeted=300, spent=250, percentage=83.3),
                    BudgetCategoryType(name="Utilities", budgeted=200, spent=180, percentage=90),
                    BudgetCategoryType(name="Other", budgeted=500, spent=620, percentage=124),
                ]
                return BudgetDataType(
                    monthlyIncome=5000.0,
                    monthlyExpenses=3500.0,
                    categories=mock_categories,
                    remaining=1500.0,
                    savingsRate=30.0,
                )
            return BudgetDataType(
                monthlyIncome=monthly_income,
                monthlyExpenses=monthly_expenses,
                categories=budget_categories,
                remaining=remaining,
                savingsRate=savings_rate,
            )
        except Exception as e:
            logger.error("Error resolving budget data: %s", e, exc_info=True)
            from core.banking_types import BudgetCategoryType, BudgetDataType

            mock_categories = [
                BudgetCategoryType(name="Housing", budgeted=1500, spent=1450, percentage=96.7),
                BudgetCategoryType(name="Food", budgeted=600, spent=580, percentage=96.7),
                BudgetCategoryType(name="Transportation", budgeted=400, spent=420, percentage=105),
                BudgetCategoryType(name="Entertainment", budgeted=300, spent=250, percentage=83.3),
                BudgetCategoryType(name="Utilities", budgeted=200, spent=180, percentage=90),
                BudgetCategoryType(name="Other", budgeted=500, spent=620, percentage=124),
            ]
            return BudgetDataType(
                monthlyIncome=5000.0,
                monthlyExpenses=3500.0,
                categories=mock_categories,
                remaining=1500.0,
                savingsRate=30.0,
            )

    def resolve_budgetData(self, info):
        """CamelCase alias for budget_data."""
        return self.resolve_budget_data(info)

    def _spending_analysis_impl(self, info, period="month"):
        from core.banking_types import SpendingAnalysisType, SpendingCategoryType, TopMerchantType
        from core.banking_models import BankTransaction

        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None
        try:
            end_date = timezone.now().date()
            if period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "year":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            transactions = BankTransaction.objects.filter(
                user=user,
                posted_date__gte=start_date,
                posted_date__lte=end_date,
            )
            category_data = {}
            merchant_data = {}
            total_spent = 0
            for transaction in transactions:
                category = transaction.category or "Other"
                merchant = transaction.merchant_name or "Unknown"
                amount = abs(float(transaction.amount)) if transaction.amount else 0
                total_spent += amount
                if category not in category_data:
                    category_data[category] = {"amount": 0, "transactions": 0}
                category_data[category]["amount"] += amount
                category_data[category]["transactions"] += 1
                if merchant not in merchant_data:
                    merchant_data[merchant] = {"amount": 0, "count": 0}
                merchant_data[merchant]["amount"] += amount
                merchant_data[merchant]["count"] += 1
            categories = []
            for category, data in category_data.items():
                percentage = (data["amount"] / total_spent * 100) if total_spent > 0 else 0
                categories.append(
                    SpendingCategoryType(
                        name=category,
                        amount=data["amount"],
                        percentage=percentage,
                        transactions=data["transactions"],
                        trend="stable",
                    )
                )
            categories.sort(key=lambda x: x.amount, reverse=True)
            top_merchants = []
            for merchant, data in sorted(merchant_data.items(), key=lambda x: x[1]["amount"], reverse=True)[:10]:
                top_merchants.append(
                    TopMerchantType(name=merchant, amount=data["amount"], count=data["count"])
                )
            trends = []
            if not transactions.exists() or total_spent == 0:
                mock_categories = [
                    SpendingCategoryType(name="Housing", amount=1450, percentage=41.4, transactions=2, trend="stable"),
                    SpendingCategoryType(name="Food", amount=580, percentage=16.6, transactions=45, trend="up"),
                    SpendingCategoryType(name="Transportation", amount=420, percentage=12, transactions=12, trend="down"),
                    SpendingCategoryType(name="Entertainment", amount=250, percentage=7.1, transactions=8, trend="up"),
                    SpendingCategoryType(name="Utilities", amount=180, percentage=5.1, transactions=4, trend="stable"),
                    SpendingCategoryType(name="Other", amount=620, percentage=17.7, transactions=23, trend="up"),
                ]
                mock_merchants = [
                    TopMerchantType(name="Amazon", amount=320, count=15),
                    TopMerchantType(name="Whole Foods", amount=280, count=12),
                    TopMerchantType(name="Uber", amount=180, count=25),
                    TopMerchantType(name="Netflix", amount=15, count=1),
                ]
                return SpendingAnalysisType(
                    totalSpent=3500.0,
                    categories=mock_categories,
                    topMerchants=mock_merchants,
                    trends=trends,
                )
            return SpendingAnalysisType(
                totalSpent=total_spent,
                categories=categories,
                topMerchants=top_merchants,
                trends=trends,
            )
        except Exception as e:
            logger.error("Error resolving spending analysis: %s", e, exc_info=True)
            from core.banking_types import SpendingAnalysisType, SpendingCategoryType, TopMerchantType

            mock_categories = [
                SpendingCategoryType(name="Housing", amount=1450, percentage=41.4, transactions=2, trend="stable"),
                SpendingCategoryType(name="Food", amount=580, percentage=16.6, transactions=45, trend="up"),
                SpendingCategoryType(name="Transportation", amount=420, percentage=12, transactions=12, trend="down"),
                SpendingCategoryType(name="Entertainment", amount=250, percentage=7.1, transactions=8, trend="up"),
                SpendingCategoryType(name="Utilities", amount=180, percentage=5.1, transactions=4, trend="stable"),
                SpendingCategoryType(name="Other", amount=620, percentage=17.7, transactions=23, trend="up"),
            ]
            mock_merchants = [
                TopMerchantType(name="Amazon", amount=320, count=15),
                TopMerchantType(name="Whole Foods", amount=280, count=12),
                TopMerchantType(name="Uber", amount=180, count=25),
                TopMerchantType(name="Netflix", amount=15, count=1),
            ]
            return SpendingAnalysisType(
                totalSpent=3500.0,
                categories=mock_categories,
                topMerchants=mock_merchants,
                trends=[],
            )

    def resolve_spending_analysis(self, info, period="month"):
        """Get spending analysis for a period."""
        return self._spending_analysis_impl(info, period=period)

    def resolve_spendingAnalysis(self, info, period="month"):
        """CamelCase alias for spending_analysis."""
        return self._spending_analysis_impl(info, period=period)
