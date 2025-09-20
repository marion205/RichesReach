"""
Management command to populate the database with sample data for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Stock, Portfolio, Watchlist, Post, IncomeProfile
from decimal import Decimal
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of sample users to create'
        )
        parser.add_argument(
            '--stocks',
            type=int,
            default=20,
            help='Number of sample stocks to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample users
        users = self.create_sample_users(options['users'])
        
        # Create sample stocks
        stocks = self.create_sample_stocks(options['stocks'])
        
        # Create sample portfolios
        self.create_sample_portfolios(users, stocks)
        
        # Create sample watchlists
        self.create_sample_watchlists(users, stocks)
        
        # Create sample posts
        self.create_sample_posts(users)
        
        # Create income profiles
        self.create_income_profiles(users)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {len(users)} users\n'
                f'- {len(stocks)} stocks\n'
                f'- Sample portfolios, watchlists, and posts'
            )
        )

    def create_sample_users(self, count):
        """Create sample users"""
        users = []
        for i in range(count):
            user, created = User.objects.get_or_create(
                email=f'user{i+1}@example.com',
                defaults={
                    'name': f'User {i+1}',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        return users

    def create_sample_stocks(self, count):
        """Create sample stocks"""
        stock_data = [
            ('AAPL', 'Apple Inc.', 'Technology', 3000000000000, 25.5, 0.5, 0.3, 0.15, 85),
            ('MSFT', 'Microsoft Corporation', 'Technology', 2800000000000, 28.2, 0.7, 0.25, 0.12, 90),
            ('GOOGL', 'Alphabet Inc.', 'Technology', 1800000000000, 22.1, 0.0, 0.1, 0.18, 75),
            ('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 1500000000000, 45.3, 0.0, 0.4, 0.22, 60),
            ('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 800000000000, 65.2, 0.0, 0.6, 0.35, 45),
            ('NVDA', 'NVIDIA Corporation', 'Technology', 1200000000000, 35.8, 0.1, 0.2, 0.25, 70),
            ('META', 'Meta Platforms Inc.', 'Communication Services', 700000000000, 18.5, 0.0, 0.15, 0.28, 55),
            ('BRK.B', 'Berkshire Hathaway Inc.', 'Financial Services', 750000000000, 12.3, 0.0, 0.05, 0.08, 95),
            ('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 450000000000, 11.2, 2.8, 0.8, 0.12, 80),
            ('JNJ', 'Johnson & Johnson', 'Healthcare', 420000000000, 15.6, 2.9, 0.3, 0.09, 90),
            ('V', 'Visa Inc.', 'Financial Services', 500000000000, 35.4, 0.7, 0.1, 0.11, 85),
            ('PG', 'Procter & Gamble Co.', 'Consumer Staples', 380000000000, 24.8, 2.4, 0.4, 0.07, 88),
            ('UNH', 'UnitedHealth Group Inc.', 'Healthcare', 520000000000, 22.1, 1.4, 0.2, 0.13, 82),
            ('HD', 'Home Depot Inc.', 'Consumer Discretionary', 350000000000, 20.5, 2.1, 0.5, 0.14, 75),
            ('MA', 'Mastercard Inc.', 'Financial Services', 380000000000, 32.7, 0.5, 0.15, 0.12, 87),
            ('DIS', 'Walt Disney Co.', 'Communication Services', 180000000000, 18.9, 0.0, 0.3, 0.16, 70),
            ('PYPL', 'PayPal Holdings Inc.', 'Financial Services', 200000000000, 15.2, 0.0, 0.2, 0.20, 65),
            ('NFLX', 'Netflix Inc.', 'Communication Services', 150000000000, 25.4, 0.0, 0.4, 0.30, 50),
            ('ADBE', 'Adobe Inc.', 'Technology', 250000000000, 28.6, 0.0, 0.1, 0.17, 80),
            ('CRM', 'Salesforce Inc.', 'Technology', 200000000000, 45.2, 0.0, 0.2, 0.19, 75),
        ]
        
        stocks = []
        for i, (symbol, name, sector, market_cap, pe_ratio, dividend_yield, debt_ratio, volatility, beginner_score) in enumerate(stock_data[:count]):
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'company_name': name,
                    'sector': sector,
                    'market_cap': market_cap,
                    'pe_ratio': Decimal(str(pe_ratio)),
                    'dividend_yield': Decimal(str(dividend_yield)),
                    'debt_ratio': Decimal(str(debt_ratio)),
                    'volatility': Decimal(str(volatility)),
                    'beginner_friendly_score': beginner_score,
                    'current_price': Decimal(str(random.uniform(50, 500))),
                }
            )
            stocks.append(stock)
        return stocks

    def create_sample_portfolios(self, users, stocks):
        """Create sample portfolios for users"""
        portfolio_names = ['Growth Portfolio', 'Dividend Portfolio', 'Tech Portfolio', 'Value Portfolio', 'Main Portfolio']
        
        for user in users:
            # Create 2-3 portfolios per user
            num_portfolios = random.randint(2, 3)
            selected_portfolios = random.sample(portfolio_names, num_portfolios)
            
            for portfolio_name in selected_portfolios:
                # Add 3-8 stocks to each portfolio
                num_holdings = random.randint(3, 8)
                selected_stocks = random.sample(stocks, num_holdings)
                
                for stock in selected_stocks:
                    shares = random.randint(1, 100)
                    current_price = stock.current_price or Decimal('100.00')
                    average_price = current_price * Decimal(str(random.uniform(0.8, 1.2)))
                    
                    Portfolio.objects.get_or_create(
                        user=user,
                        stock=stock,
                        defaults={
                            'shares': shares,
                            'average_price': average_price,
                            'current_price': current_price,
                            'notes': f'portfolio:{portfolio_name}',
                        }
                    )

    def create_sample_watchlists(self, users, stocks):
        """Create sample watchlists for users"""
        for user in users:
            # Add 5-10 stocks to watchlist
            num_watchlist = random.randint(5, 10)
            selected_stocks = random.sample(stocks, num_watchlist)
            
            for stock in selected_stocks:
                Watchlist.objects.get_or_create(
                    user=user,
                    stock=stock,
                    defaults={
                        'notes': f'Watching {stock.symbol} for potential investment',
                    }
                )

    def create_sample_posts(self, users):
        """Create sample social posts"""
        post_templates = [
            "Just added {stock} to my portfolio! Excited about the long-term potential.",
            "Market analysis: {stock} showing strong technical indicators. What do you think?",
            "Portfolio update: Rebalanced my holdings and added more {stock}.",
            "Educational tip: Always do your own research before investing in {stock}.",
            "Market volatility is creating opportunities. Considering {stock} for my portfolio.",
        ]
        
        stocks = Stock.objects.all()[:10]  # Get first 10 stocks for posts
        
        for user in users:
            # Create 2-5 posts per user
            num_posts = random.randint(2, 5)
            
            for _ in range(num_posts):
                template = random.choice(post_templates)
                stock = random.choice(stocks)
                content = template.format(stock=stock.symbol)
                
                Post.objects.create(
                    user=user,
                    content=content,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )

    def create_income_profiles(self, users):
        """Create income profiles for users"""
        income_brackets = ['Low', 'Medium', 'High', 'Very High']
        investment_goals_options = [
            ['Retirement', 'Wealth Building'],
            ['Education', 'Home Purchase'],
            ['Emergency Fund', 'Travel'],
            ['Business Investment', 'Real Estate'],
        ]
        
        for user in users:
            IncomeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'income_bracket': random.choice(income_brackets),
                    'age': random.randint(25, 65),
                    'investment_goals': random.choice(investment_goals_options),
                    'risk_tolerance': random.choice(['Conservative', 'Moderate', 'Aggressive']),
                }
            )
