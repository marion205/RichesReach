-- Create or update appuser with password @Master22
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'appuser') THEN
    CREATE ROLE appuser LOGIN PASSWORD '@Master22';
  ELSE
    ALTER ROLE appuser WITH PASSWORD '@Master22';
  END IF;
END$$;

-- Grant connect to appdb
GRANT CONNECT ON DATABASE appdb TO appuser;

-- Connect to appdb and grant schema permissions
\connect appdb

GRANT USAGE ON SCHEMA public TO appuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO appuser;

-- Show success
SELECT 'appuser created/updated successfully' as status;
