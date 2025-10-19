#!/usr/bin/env python3
"""
Simple test server with just authentication
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime, timedelta
import jwt
import hashlib
import re
from typing import Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Auth Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Mock user database
users_db = {
    "test@example.com": {
        "id": "user_123",
        "name": "Test User",
        "email": "test@example.com",
        "password": hashlib.sha256("testpass".encode()).hexdigest(),
        "hasPremiumAccess": True,
        "subscriptionTier": "premium"
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/")
async def root():
    return {"message": "Auth Test Server", "status": "running"}

# GraphQL helpers
FIELD_RE = re.compile(r'\b(query|mutation|subscription)\b.*?\{(?P<body>.*)\}\s*$', re.DOTALL)

def top_level_fields(query: str) -> Set[str]:
    """Return set of top-level GraphQL field names"""
    q = (query or "").strip()
    q = re.sub(r'#.*', '', q)
    q = re.sub(r'\s+', ' ', q)

    m = FIELD_RE.search(q)
    if not m:
        if q.startswith('{'):
            body = q[1:q.rfind('}')].strip()
        else:
            return set()
    else:
        body = m.group('body').strip()

    fields = set()
    depth = 0
    token = []
    for ch in body:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif ch in ' \t\n(' and depth == 0:
            if token:
                fields.add(''.join(token))
                token = []
            continue
        if depth == 0:
            if ch not in '{})':
                token.append(ch)
    if token:
        fields.add(''.join(token))
    
    cleaned = set()
    for f in fields:
        if ':' in f:
            cleaned.add(f.split(':', 1)[1].strip())
        else:
            cleaned.add(f.strip())
    return {f for f in cleaned if f}

@app.post("/graphql")
@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    query = request_data.get("query", "") or ""
    variables = request_data.get("variables", {}) or {}
    response_data = {}

    logger.info("=== QUERY DEBUG ===")
    logger.info("Raw query: %s", query)
    logger.info("Variables: %s", variables)

    # Detect top-level fields once
    fields = top_level_fields(query)
    logger.info("Top-level fields detected: %s", fields)

    # Authentication handler
    if "tokenAuth" in fields:
        logger.info("→ Handling tokenAuth")
        print(f"DEBUG: tokenAuth handler reached! Fields: {fields}")
        email = variables.get("email", "")
        password = variables.get("password", "")
        if not email or not password:
            # Try to extract from query string
            email_match = re.search(r'email:\s*"([^"]+)"', query)
            password_match = re.search(r'password:\s*"([^"]+)"', query)
            if email_match: email = email_match.group(1)
            if password_match: password = password_match.group(1)
        
        if not email or not password:
            return {"errors": [{"message": "Email and password are required"}]}
        
        user = users_db.get(email.lower())
        if not user or user["password"] != hashlib.sha256(password.encode()).hexdigest():
            return {"errors": [{"message": "Invalid credentials"}]}
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": email.lower()}, expires_delta=access_token_expires)
        response_data["tokenAuth"] = {
            "token": access_token,
            "refreshToken": access_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "hasPremiumAccess": user["hasPremiumAccess"],
                "subscriptionTier": user["subscriptionTier"],
                "__typename": "User"
            },
            "__typename": "TokenAuth"
        }
        return {"data": response_data}

    # Default response
    logger.info("📝 Using default response (no handlers matched)")
    return {"data": {"message": "Default response"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
