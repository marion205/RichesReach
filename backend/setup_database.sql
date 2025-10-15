-- Create appuser role if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'appuser') THEN
    CREATE ROLE appuser LOGIN PASSWORD 'AppUser2025Secure!';
  END IF;
END$$;

-- Create appdb database if it doesn't exist
SELECT 'CREATE DATABASE appdb OWNER appuser TEMPLATE template1'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'appdb')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;

-- Connect to appdb and set up schema permissions
\c appdb
GRANT ALL ON SCHEMA public TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO appuser;

-- Verify the setup
SELECT 'Database and user created successfully' as status;
