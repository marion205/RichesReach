#!/bin/bash
# Update .env file with Yodlee credentials

ENV_FILE=".env"

# Backup existing .env
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    echo "✅ Backed up existing .env to .env.backup"
fi

# Update Yodlee credentials
sed -i '' 's|YODLEE_CLIENT_ID=.*|YODLEE_CLIENT_ID=Ml1fZQA5VV2Gg0kqfVmQy1SjdY0nKCVPVK4r8YMJUGFVtAAf|g' "$ENV_FILE"
sed -i '' 's|YODLEE_SECRET=.*|YODLEE_SECRET=LXE1UQClWmf470g5BxVVI6eJXFjplOhZAxPwuYpMWzUGUUuWDI7f6HcMERY7J3m6|g' "$ENV_FILE"
sed -i '' 's|YODLEE_FASTLINK_URL=.*|YODLEE_FASTLINK_URL=https://fl4.sandbox.yodlee.com/authenticate/restserver/fastlink|g' "$ENV_FILE"
sed -i '' 's|YODLEE_BASE_URL=.*|YODLEE_BASE_URL=https://sandbox.api.yodlee.com/ysl|g' "$ENV_FILE"
sed -i '' 's|BANK_TOKEN_ENC_KEY=.*|BANK_TOKEN_ENC_KEY=8UC7PJS2hj8T86HOG0aS3MNtEbc8P1O-6VA5eMQyGdo=|g' "$ENV_FILE"

echo "✅ Updated .env file with Yodlee credentials"
