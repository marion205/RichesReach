#!/bin/bash
set -e

# Install postgresql client
apt-get update && apt-get install -y postgresql-client

# Set environment variables
export PGPASSWORD="TEMP_Master_2024!ChangeMe"
HOST="riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com"
MASTER_USER="richesreach"
NEW_APP_PW="Master1984"

echo "Setting appuser password..."

# Create/update appuser with correct password
psql -h "$HOST" -U "$MASTER_USER" -d postgres -c "
DO \$\$ 
BEGIN 
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'appuser') THEN 
    CREATE ROLE appuser LOGIN PASSWORD '$NEW_APP_PW';
  ELSE 
    ALTER ROLE appuser WITH LOGIN PASSWORD '$NEW_APP_PW';
  END IF;
END\$\$;
"

# Grant connect permission
psql -h "$HOST" -U "$MASTER_USER" -d postgres -c "GRANT CONNECT ON DATABASE appdb TO appuser;"

# Grant permissions on appdb
psql -h "$HOST" -U "$MASTER_USER" -d appdb -c "
GRANT USAGE, CREATE ON SCHEMA public TO appuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO appuser;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO appuser;
"

echo "Password set successfully!"
