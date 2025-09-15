"""
GraphQL types for portfolio management
"""
import graphene
from graphene_django import DjangoObjectType
from .models import Portfolio, Stock
from .portfolio_service import PortfolioService
class PortfolioHoldingType(graphene.ObjectType):
"""Individual stock holding within a portfolio"""
id = graphene.ID()
stock = graphene.Field('core.types.StockType')
shares = graphene.Int()
average_price = graphene.Float()
current_price = graphene.Float()
total_value = graphene.Float()
notes = graphene.String()
created_at = graphene.DateTime()
updated_at = graphene.DateTime()
def resolve_stock(self, info):
# Handle both dict and model object
if hasattr(self, 'stock'):
return self.stock
return self.get('stock')
def resolve_average_price(self, info):
# Handle both dict and model object
if hasattr(self, 'average_price'):
return float(self.average_price) if self.average_price else None
return float(self['average_price']) if self.get('average_price') else None
def resolve_current_price(self, info):
# Handle both dict and model object
if hasattr(self, 'current_price'):
return float(self.current_price) if self.current_price else None
return float(self['current_price']) if self.get('current_price') else None
def resolve_total_value(self, info):
# Handle both dict and model object
if hasattr(self, 'current_price') and hasattr(self, 'shares'):
# Calculate total value for model object
if self.current_price and self.shares:
return float(self.current_price * self.shares)
return 0.0
return float(self['total_value']) if self.get('total_value') else None
class PortfolioType(graphene.ObjectType):
"""Virtual portfolio containing multiple holdings"""
name = graphene.String()
holdings = graphene.List(PortfolioHoldingType)
total_value = graphene.Float()
holdings_count = graphene.Int()
def resolve_total_value(self, info):
if self['total_value']:
return float(self['total_value'])
return 0.0
class PortfolioSummaryType(graphene.ObjectType):
"""Summary of all user portfolios"""
portfolios = graphene.List(PortfolioType)
total_portfolios = graphene.Int()
total_value = graphene.Float()
def resolve_total_value(self, info):
if self['total_value']:
return float(self['total_value'])
return 0.0
class CreatePortfolioHolding(graphene.Mutation):
"""Add a stock holding to a specific portfolio"""
class Arguments:
stock_id = graphene.ID(required=True)
shares = graphene.Int(required=True)
portfolio_name = graphene.String(required=True)
average_price = graphene.Float()
current_price = graphene.Float()
success = graphene.Boolean()
message = graphene.String()
holding = graphene.Field(PortfolioHoldingType)
def mutate(self, info, stock_id, shares, portfolio_name, average_price=None, current_price=None):
user = info.context.user
if not user or user.is_anonymous:
return CreatePortfolioHolding(
success=False,
message="Authentication required"
)
if shares <= 0:
return CreatePortfolioHolding(
success=False,
message="Shares must be greater than 0"
)
holding = PortfolioService.add_holding_to_portfolio(
user=user,
stock_id=stock_id,
shares=shares,
portfolio_name=portfolio_name,
average_price=average_price,
current_price=current_price
)
if holding:
return CreatePortfolioHolding(
success=True,
message=f"Added {shares} shares to {portfolio_name}",
holding=holding
)
else:
return CreatePortfolioHolding(
success=False,
message="Stock not found"
)
class UpdatePortfolioHolding(graphene.Mutation):
"""Move a holding to a different portfolio"""
class Arguments:
holding_id = graphene.ID(required=True)
new_portfolio_name = graphene.String(required=True)
success = graphene.Boolean()
message = graphene.String()
holding = graphene.Field(PortfolioHoldingType)
def mutate(self, info, holding_id, new_portfolio_name):
user = info.context.user
if not user or user.is_anonymous:
return UpdatePortfolioHolding(
success=False,
message="Authentication required"
)
holding = PortfolioService.update_holding_portfolio(holding_id, new_portfolio_name)
if holding:
return UpdatePortfolioHolding(
success=True,
message=f"Moved holding to {new_portfolio_name}",
holding=holding
)
else:
return UpdatePortfolioHolding(
success=False,
message="Holding not found"
)
class UpdateHoldingShares(graphene.Mutation):
"""Update the number of shares for a holding"""
class Arguments:
holding_id = graphene.ID(required=True)
new_shares = graphene.Int(required=True)
success = graphene.Boolean()
message = graphene.String()
holding = graphene.Field(PortfolioHoldingType)
def mutate(self, info, holding_id, new_shares):
user = info.context.user
if not user or user.is_anonymous:
return UpdateHoldingShares(
success=False,
message="Authentication required"
)
if new_shares <= 0:
return UpdateHoldingShares(
success=False,
message="Shares must be greater than 0"
)
holding = PortfolioService.update_holding_shares(holding_id, new_shares)
if holding:
return UpdateHoldingShares(
success=True,
message=f"Updated shares to {new_shares}",
holding=holding
)
else:
return UpdateHoldingShares(
success=False,
message="Holding not found"
)
class RemovePortfolioHolding(graphene.Mutation):
"""Remove a holding from portfolio"""
class Arguments:
holding_id = graphene.ID(required=True)
success = graphene.Boolean()
message = graphene.String()
def mutate(self, info, holding_id):
user = info.context.user
if not user or user.is_anonymous:
return RemovePortfolioHolding(
success=False,
message="Authentication required"
)
success = PortfolioService.remove_holding_from_portfolio(holding_id)
if success:
return RemovePortfolioHolding(
success=True,
message="Holding removed successfully"
)
else:
return RemovePortfolioHolding(
success=False,
message="Holding not found"
)
