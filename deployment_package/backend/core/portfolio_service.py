"""
Portfolio service to manage multiple virtual portfolios using the existing Portfolio model
"""
from django.contrib.auth import get_user_model
from .models import Portfolio, Stock
from decimal import Decimal
import json
User = get_user_model()


class PortfolioService:
    """Service to manage virtual portfolios using the existing Portfolio model"""

    @staticmethod
    def get_user_portfolios(user):
        """Get all virtual portfolios for a user"""
        # Optimize: Use select_related to reduce database queries
        holdings = Portfolio.objects.filter(user=user).select_related('stock').only(
            'id', 'shares', 'average_price', 'current_price', 'notes', 'created_at', 'updated_at',
            'stock__symbol', 'stock__name', 'stock__exchange'
        )
        # Group holdings by portfolio name (stored in notes)
        portfolios = {}
        total_value = Decimal('0')
        for holding in holdings:
            # Extract portfolio name from notes
            portfolio_name = PortfolioService._extract_portfolio_name(
                holding.notes)
            if portfolio_name not in portfolios:
                portfolios[portfolio_name] = {
                    'name': portfolio_name,
                    'holdings': [],
                    'total_value': Decimal('0'),
                    'holdings_count': 0
                }
            # Calculate holding value
            holding_value = Decimal('0')
            if holding.current_price and holding.shares:
                holding_value = holding.current_price * holding.shares
            portfolios[portfolio_name]['holdings'].append({
                'id': holding.id,
                'stock': holding.stock,
                'shares': holding.shares,
                'average_price': holding.average_price,
                'current_price': holding.current_price,
                'total_value': holding_value,
                'notes': holding.notes,
                'created_at': holding.created_at,
                'updated_at': holding.updated_at
            })
            portfolios[portfolio_name]['total_value'] += holding_value
            portfolios[portfolio_name]['holdings_count'] += 1
            total_value += holding_value
        # Convert to list and sort by total value
        portfolio_list = list(portfolios.values())
        portfolio_list.sort(key=lambda x: x['total_value'], reverse=True)
        return {
            'portfolios': portfolio_list,
            'total_portfolios': len(portfolio_list),
            'total_value': total_value
        }

    @staticmethod
    def add_holding_to_portfolio(
            user,
            stock_id,
            shares,
            portfolio_name,
            average_price=None,
            current_price=None):
        """Add a stock holding to a specific portfolio"""
        try:
            stock = Stock.objects.get(id=stock_id)
            # Create notes with portfolio information
            notes = PortfolioService._create_portfolio_notes(portfolio_name)
            # Use get_or_create to handle existing holdings
            portfolio_item, created = Portfolio.objects.get_or_create(
                user=user,
                stock=stock,
                defaults={
                    'shares': shares,
                    'notes': notes,
                    'average_price': average_price or current_price or Decimal('0'),
                    'current_price': current_price
                }
            )
            if not created:
                # Update existing holding
                portfolio_item.shares += shares
                portfolio_item.notes = notes
                if current_price:
                    portfolio_item.current_price = current_price
                portfolio_item.save()
            return portfolio_item
        except Stock.DoesNotExist:
            return None
    @staticmethod
    def update_holding_portfolio(holding_id, new_portfolio_name):

        """Move a holding to a different portfolio"""
        try:
            holding = Portfolio.objects.get(id=holding_id)
            holding.notes = PortfolioService._create_portfolio_notes(new_portfolio_name)
            holding.save()
            return holding
        except Portfolio.DoesNotExist:
            return None
    @staticmethod
    def update_holding_shares(holding_id, new_shares):

        """Update the number of shares for a holding"""
        try:
            holding = Portfolio.objects.get(id=holding_id)
            holding.shares = new_shares
            holding.save()
            return holding
        except Portfolio.DoesNotExist:
            return None

    @staticmethod
    def remove_holding_from_portfolio(holding_id):
        """Remove a holding from portfolio (delete it)"""
        try:
            holding = Portfolio.objects.get(id=holding_id)
            holding.delete()
            return True
        except Portfolio.DoesNotExist:
            return False

    @staticmethod
    def _extract_portfolio_name(notes):
        """Extract portfolio name from notes field"""
        if not notes:
            return "Main Portfolio"
        try:
            # Try to parse as JSON first
            data = json.loads(notes)
            return data.get('portfolio_name', 'Main Portfolio')
        except (json.JSONDecodeError, TypeError):
            # If not JSON, check if it starts with portfolio info
            if notes.startswith('portfolio:'):
                return notes.split(':', 1)[1].strip()
            return "Main Portfolio"
    @staticmethod
    def _create_portfolio_notes(portfolio_name):

        """Create notes field with portfolio information"""
        if portfolio_name == "Main Portfolio":
            return ""
        return json.dumps({
            'portfolio_name': portfolio_name,
            'type': 'portfolio_holding'
        })
    @staticmethod
    def get_portfolio_names(user):

        """Get list of all portfolio names for a user"""
        holdings = Portfolio.objects.filter(user=user)
        portfolio_names = set()
        for holding in holdings:
            portfolio_name = PortfolioService._extract_portfolio_name(holding.notes)
            portfolio_names.add(portfolio_name)
        return sorted(list(portfolio_names))
