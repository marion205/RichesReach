#!/usr/bin/env python3
"""
Production Database Setup Script for RichesReach
This script helps configure production database settings
"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

class ProductionDatabaseSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        
        # Load environment variables
        env_file = self.backend_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def test_database_connection(self):
        """Test database connection"""
        print("🔌 Testing database connection...")
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432)
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connection successful!")
            print(f"📊 PostgreSQL version: {version[0]}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def run_migrations(self):
        """Run Django migrations"""
        print("🔄 Running Django migrations...")
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            # Run migrations
            result = os.system("python manage.py migrate")
            if result == 0:
                print("✅ Migrations completed successfully!")
                return True
            else:
                print("❌ Migrations failed!")
                return False
        except Exception as e:
            print(f"❌ Error running migrations: {e}")
            return False

    def create_superuser(self):
        """Create Django superuser"""
        print("👤 Creating Django superuser...")
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            # Run createsuperuser
            result = os.system("python manage.py createsuperuser")
            if result == 0:
                print("✅ Superuser created successfully!")
                return True
            else:
                print("❌ Superuser creation failed!")
                return False
        except Exception as e:
            print(f"❌ Error creating superuser: {e}")
            return False

    def collect_static_files(self):
        """Collect static files for production"""
        print("📁 Collecting static files...")
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            # Collect static files
            result = os.system("python manage.py collectstatic --noinput")
            if result == 0:
                print("✅ Static files collected successfully!")
                return True
            else:
                print("❌ Static files collection failed!")
                return False
        except Exception as e:
            print(f"❌ Error collecting static files: {e}")
            return False

    def setup_database_permissions(self):
        """Setup database permissions and indexes"""
        print("🔐 Setting up database permissions...")
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432)
            )
            cursor = conn.cursor()
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_email ON core_user(email);",
                "CREATE INDEX IF NOT EXISTS idx_stock_symbol ON core_stock(symbol);",
                "CREATE INDEX IF NOT EXISTS idx_portfolio_user ON core_portfolio(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_watchlist_user ON core_watchlist(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_discussion_stock ON core_stockdiscussion(stock_id);",
            ]
            
            for index in indexes:
                cursor.execute(index)
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database permissions and indexes set up successfully!")
            return True
        except Exception as e:
            print(f"❌ Error setting up database permissions: {e}")
            return False

    def run_setup(self):
        """Run the complete database setup process"""
        print("🚀 RichesReach Production Database Setup")
        print("=" * 50)
        
        # Check if environment variables are set
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease run setup_production_env.py first!")
            return False
        
        try:
            # Test database connection
            if not self.test_database_connection():
                return False
            
            # Run migrations
            if not self.run_migrations():
                return False
            
            # Setup database permissions
            if not self.setup_database_permissions():
                return False
            
            # Collect static files
            if not self.collect_static_files():
                return False
            
            # Create superuser (optional)
            create_superuser = input("\nDo you want to create a Django superuser? (y/N): ")
            if create_superuser.lower() == 'y':
                self.create_superuser()
            
            print("\n🎉 Production Database Setup Complete!")
            print("=" * 50)
            print("Your database is now ready for production use.")
            return True
        except Exception as e:
            print(f"\n❌ Error during database setup: {e}")
            return False

if __name__ == "__main__":
    setup = ProductionDatabaseSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)