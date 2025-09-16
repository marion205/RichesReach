#!/usr/bin/env python3
"""
Simple FastAPI server for testing authentication
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, timedelta
import hashlib

app = FastAPI(title="RichesReach Test Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "django-insecure-wk_qy339*l)1xg=(f6_e@9+d7sgi7%#0t!e17a3nkeu&p#@zq9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Simple in-memory user storage
users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": hashlib.sha256("testpass".encode()).hexdigest(),
        "name": "Test User",
        "id": "1"
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/")
async def root():
    return {"message": "RichesReach Test Server is running"}

@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    """GraphQL endpoint for authentication"""
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
    # Handle tokenAuth mutation
    if "tokenAuth" in query:
        email = variables.get("email", "")
        password = variables.get("password", "")
        
        if not email or not password:
            return {
                "errors": [{"message": "Email and password are required"}]
            }
        
        # Check user credentials
        user = users_db.get(email.lower())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Debug: email={email}, user={user}, password_hash={password_hash[:10]}...")
        if not user or user["password"] != password_hash:
            return {
                "errors": [{"message": "Please enter valid credentials"}]
            }
        
        # Create token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email.lower()}, expires_delta=access_token_expires
        )
        
        return {
            "data": {
                "tokenAuth": {
                    "token": access_token
                }
            }
        }
    
    # Handle other queries
    return {
        "data": {
            "__schema": {
                "types": [{"name": "Query"}, {"name": "Mutation"}]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
