import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from .models import User, Stock, Watchlist, Portfolio, StockDiscussion, DiscussionComment, Follow
logger = logging.getLogger(__name__)
class DataValidationService:
"""Service for validating and ensuring data consistency"""
def __init__(self):
self.validation_errors = []
def validate_all_data(self):
"""Run all data validation checks"""
self.validation_errors = []
logger.info("Starting comprehensive data validation")
# Validate users
self.validate_users()
# Validate stocks
self.validate_stocks()
# Validate watchlists
self.validate_watchlists()
# Validate portfolios
self.validate_portfolios()
# Validate discussions
self.validate_discussions()
# Validate comments
self.validate_comments()
# Validate follows
self.validate_follows()
# Validate relationships
self.validate_relationships()
if self.validation_errors:
logger.warning(f"Data validation found {len(self.validation_errors)} issues")
return False, self.validation_errors
else:
logger.info("Data validation passed successfully")
return True, []
def validate_users(self):
"""Validate user data"""
logger.info("Validating users")
# Check for users without email
users_without_email = User.objects.filter(email__isnull=True)
for user in users_without_email:
self.validation_errors.append(f"User {user.id} has no email address")
# Check for duplicate emails
duplicate_emails = User.objects.values('email').annotate(
count=models.Count('id')
).filter(count__gt=1, email__isnull=False)
for duplicate in duplicate_emails:
self.validation_errors.append(f"Duplicate email found: {duplicate['email']}")
# Check for invalid email formats
invalid_emails = User.objects.exclude(email__contains='@')
for user in invalid_emails:
self.validation_errors.append(f"User {user.id} has invalid email format: {user.email}")
# Check for users with empty names
empty_names = User.objects.filter(name__isnull=True) | User.objects.filter(name='')
for user in empty_names:
self.validation_errors.append(f"User {user.id} has empty name")
def validate_stocks(self):
"""Validate stock data"""
logger.info("Validating stocks")
# Check for stocks without symbols
stocks_without_symbols = Stock.objects.filter(symbol__isnull=True) | Stock.objects.filter(symbol='')
for stock in stocks_without_symbols:
self.validation_errors.append(f"Stock {stock.id} has no symbol")
# Check for duplicate symbols
duplicate_symbols = Stock.objects.values('symbol').annotate(
count=models.Count('id')
).filter(count__gt=1, symbol__isnull=False)
for duplicate in duplicate_symbols:
self.validation_errors.append(f"Duplicate stock symbol found: {duplicate['symbol']}")
# Check for negative prices
negative_prices = Stock.objects.filter(current_price__lt=0)
for stock in negative_prices:
self.validation_errors.append(f"Stock {stock.symbol} has negative price: {stock.current_price}")
def validate_watchlists(self):
"""Validate watchlist data"""
logger.info("Validating watchlists")
# Check for orphaned watchlist items
orphaned_watchlists = Watchlist.objects.filter(stock__isnull=True)
for watchlist in orphaned_watchlists:
self.validation_errors.append(f"Watchlist item {watchlist.id} has no associated stock")
# Check for orphaned user references
orphaned_user_watchlists = Watchlist.objects.filter(user__isnull=True)
for watchlist in orphaned_user_watchlists:
self.validation_errors.append(f"Watchlist item {watchlist.id} has no associated user")
# Check for duplicate watchlist entries
duplicate_watchlists = Watchlist.objects.values('user', 'stock').annotate(
count=models.Count('id')
).filter(count__gt=1)
for duplicate in duplicate_watchlists:
self.validation_errors.append(f"Duplicate watchlist entry for user {duplicate['user']} and stock {duplicate['stock']}")
def validate_portfolios(self):
"""Validate portfolio data"""
logger.info("Validating portfolios")
# Check for orphaned portfolios
orphaned_portfolios = Portfolio.objects.filter(user__isnull=True)
for portfolio in orphaned_portfolios:
self.validation_errors.append(f"Portfolio {portfolio.id} has no associated user")
# Check for negative portfolio values
negative_values = Portfolio.objects.filter(total_value__lt=0)
for portfolio in negative_values:
self.validation_errors.append(f"Portfolio {portfolio.id} has negative total value: {portfolio.total_value}")
# Check for empty portfolio names
empty_names = Portfolio.objects.filter(name__isnull=True) | Portfolio.objects.filter(name='')
for portfolio in empty_names:
self.validation_errors.append(f"Portfolio {portfolio.id} has empty name")
def validate_discussions(self):
"""Validate discussion data"""
logger.info("Validating discussions")
# Check for orphaned discussions
orphaned_discussions = StockDiscussion.objects.filter(user__isnull=True)
for discussion in orphaned_discussions:
self.validation_errors.append(f"Discussion {discussion.id} has no associated user")
# Check for empty titles
empty_titles = StockDiscussion.objects.filter(title__isnull=True) | StockDiscussion.objects.filter(title='')
for discussion in empty_titles:
self.validation_errors.append(f"Discussion {discussion.id} has empty title")
# Check for empty content
empty_content = StockDiscussion.objects.filter(content__isnull=True) | StockDiscussion.objects.filter(content='')
for discussion in empty_content:
self.validation_errors.append(f"Discussion {discussion.id} has empty content")
# Check for invalid visibility values
invalid_visibility = StockDiscussion.objects.exclude(visibility__in=['public', 'followers'])
for discussion in invalid_visibility:
self.validation_errors.append(f"Discussion {discussion.id} has invalid visibility: {discussion.visibility}")
# Check for negative vote counts
negative_upvotes = StockDiscussion.objects.filter(upvotes__lt=0)
for discussion in negative_upvotes:
self.validation_errors.append(f"Discussion {discussion.id} has negative upvotes: {discussion.upvotes}")
negative_downvotes = StockDiscussion.objects.filter(downvotes__lt=0)
for discussion in negative_downvotes:
self.validation_errors.append(f"Discussion {discussion.id} has negative downvotes: {discussion.downvotes}")
def validate_comments(self):
"""Validate comment data"""
logger.info("Validating comments")
# Check for orphaned comments
orphaned_comments = DiscussionComment.objects.filter(discussion__isnull=True)
for comment in orphaned_comments:
self.validation_errors.append(f"Comment {comment.id} has no associated discussion")
orphaned_user_comments = DiscussionComment.objects.filter(user__isnull=True)
for comment in orphaned_user_comments:
self.validation_errors.append(f"Comment {comment.id} has no associated user")
# Check for empty content
empty_content = DiscussionComment.objects.filter(content__isnull=True) | DiscussionComment.objects.filter(content='')
for comment in empty_content:
self.validation_errors.append(f"Comment {comment.id} has empty content")
# Check for negative vote counts
negative_upvotes = DiscussionComment.objects.filter(upvotes__lt=0)
for comment in negative_upvotes:
self.validation_errors.append(f"Comment {comment.id} has negative upvotes: {comment.upvotes}")
negative_downvotes = DiscussionComment.objects.filter(downvotes__lt=0)
for comment in negative_downvotes:
self.validation_errors.append(f"Comment {comment.id} has negative downvotes: {comment.downvotes}")
def validate_follows(self):
"""Validate follow relationships"""
logger.info("Validating follows")
# Check for orphaned follows
orphaned_follows = Follow.objects.filter(follower__isnull=True)
for follow in orphaned_follows:
self.validation_errors.append(f"Follow {follow.id} has no follower")
orphaned_following = Follow.objects.filter(following__isnull=True)
for follow in orphaned_following:
self.validation_errors.append(f"Follow {follow.id} has no following user")
# Check for self-follows
self_follows = Follow.objects.filter(follower=models.F('following'))
for follow in self_follows:
self.validation_errors.append(f"User {follow.follower.id} is following themselves")
# Check for duplicate follows
duplicate_follows = Follow.objects.values('follower', 'following').annotate(
count=models.Count('id')
).filter(count__gt=1)
for duplicate in duplicate_follows:
self.validation_errors.append(f"Duplicate follow relationship: user {duplicate['follower']} following user {duplicate['following']}")
def validate_relationships(self):
"""Validate cross-model relationships"""
logger.info("Validating relationships")
# Check watchlist-stock relationships
invalid_watchlist_stocks = Watchlist.objects.exclude(
stock__in=Stock.objects.all()
)
for watchlist in invalid_watchlist_stocks:
self.validation_errors.append(f"Watchlist {watchlist.id} references non-existent stock")
# Check discussion-stock relationships
invalid_discussion_stocks = StockDiscussion.objects.exclude(
stock__in=Stock.objects.all()
).exclude(stock__isnull=True)
for discussion in invalid_discussion_stocks:
self.validation_errors.append(f"Discussion {discussion.id} references non-existent stock")
# Check comment-discussion relationships
invalid_comment_discussions = DiscussionComment.objects.exclude(
discussion__in=StockDiscussion.objects.all()
)
for comment in invalid_comment_discussions:
self.validation_errors.append(f"Comment {comment.id} references non-existent discussion")
def fix_common_issues(self):
"""Fix common data issues automatically"""
logger.info("Starting automatic data fixes")
fixes_applied = []
try:
with transaction.atomic():
# Fix negative vote counts
negative_upvotes = StockDiscussion.objects.filter(upvotes__lt=0)
count = negative_upvotes.update(upvotes=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative upvote counts in discussions")
negative_downvotes = StockDiscussion.objects.filter(downvotes__lt=0)
count = negative_downvotes.update(downvotes=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative downvote counts in discussions")
# Fix negative comment vote counts
negative_comment_upvotes = DiscussionComment.objects.filter(upvotes__lt=0)
count = negative_comment_upvotes.update(upvotes=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative upvote counts in comments")
negative_comment_downvotes = DiscussionComment.objects.filter(downvotes__lt=0)
count = negative_comment_downvotes.update(downvotes=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative downvote counts in comments")
# Fix negative portfolio values
negative_portfolios = Portfolio.objects.filter(total_value__lt=0)
count = negative_portfolios.update(total_value=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative portfolio values")
# Fix negative stock prices
negative_prices = Stock.objects.filter(current_price__lt=0)
count = negative_prices.update(current_price=0)
if count > 0:
fixes_applied.append(f"Fixed {count} negative stock prices")
# Remove duplicate follows
duplicate_follows = Follow.objects.values('follower', 'following').annotate(
count=models.Count('id')
).filter(count__gt=1)
for duplicate in duplicate_follows:
# Keep the first one, delete the rest
follows_to_delete = Follow.objects.filter(
follower_id=duplicate['follower'],
following_id=duplicate['following']
)[1:] # Skip the first one
count = follows_to_delete.count()
follows_to_delete.delete()
if count > 0:
fixes_applied.append(f"Removed {count} duplicate follow relationships")
# Remove duplicate watchlist entries
duplicate_watchlists = Watchlist.objects.values('user', 'stock').annotate(
count=models.Count('id')
).filter(count__gt=1)
for duplicate in duplicate_watchlists:
# Keep the first one, delete the rest
watchlists_to_delete = Watchlist.objects.filter(
user_id=duplicate['user'],
stock_id=duplicate['stock']
)[1:] # Skip the first one
count = watchlists_to_delete.count()
watchlists_to_delete.delete()
if count > 0:
fixes_applied.append(f"Removed {count} duplicate watchlist entries")
except Exception as e:
logger.error(f"Error applying automatic fixes: {e}")
raise
if fixes_applied:
logger.info(f"Applied {len(fixes_applied)} automatic fixes")
return fixes_applied
else:
logger.info("No automatic fixes were needed")
return []
# Global instance
data_validation_service = DataValidationService()
