#!/usr/bin/env python3
"""
Debug GraphQL Endpoint
"""

import requests
import json

def test_simple_query():
    """Test a simple GraphQL query"""
    query = """
    query {
        __schema {
            queryType {
                name
            }
        }
    }
    """
    
    response = requests.post(
        "http://localhost:8000/graphql/",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"JSON Data: {json.dumps(data, indent=2)}")
        except:
            print("Failed to parse JSON")

def test_me_query():
    """Test the me query specifically"""
    query = """
    query {
        me {
            id
            name
            email
        }
    }
    """
    
    response = requests.post(
        "http://localhost:8000/graphql/",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nMe Query Status: {response.status_code}")
    print(f"Me Query Response: {response.text}")

def test_stocks_query():
    """Test stocks query"""
    query = """
    query {
        stocks {
            symbol
            name
        }
    }
    """
    
    response = requests.post(
        "http://localhost:8000/graphql/",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStocks Query Status: {response.status_code}")
    print(f"Stocks Query Response: {response.text}")

if __name__ == "__main__":
    print("🔍 DEBUGGING GRAPHQL ENDPOINT")
    print("=" * 40)
    
    test_simple_query()
    test_me_query()
    test_stocks_query()
