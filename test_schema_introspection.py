#!/usr/bin/env python3
"""
GraphQL Schema Introspection Test
"""

import requests
import json

def get_schema():
    """Get the complete GraphQL schema"""
    query = """
    query IntrospectionQuery {
        __schema {
            queryType {
                name
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
            mutationType {
                name
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
            subscriptionType {
                name
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    response = requests.post(
        "http://localhost:8000/graphql/",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]
    
    return None

def main():
    schema = get_schema()
    if schema:
        print("🔍 GRAPHQL SCHEMA ANALYSIS")
        print("=" * 50)
        
        # Queries
        if schema.get("__schema", {}).get("queryType"):
            queries = schema["__schema"]["queryType"]["fields"]
            print(f"\n📋 AVAILABLE QUERIES ({len(queries)}):")
            for query in queries:
                print(f"  • {query['name']}")
        
        # Mutations
        if schema.get("__schema", {}).get("mutationType"):
            mutations = schema["__schema"]["mutationType"]["fields"]
            print(f"\n🔄 AVAILABLE MUTATIONS ({len(mutations)}):")
            for mutation in mutations:
                print(f"  • {mutation['name']}")
        
        # Subscriptions
        if schema.get("__schema", {}).get("subscriptionType"):
            subscriptions = schema["__schema"]["subscriptionType"]["fields"]
            print(f"\n📡 AVAILABLE SUBSCRIPTIONS ({len(subscriptions)}):")
            for subscription in subscriptions:
                print(f"  • {subscription['name']}")
        
        print("\n✅ Schema introspection successful!")
    else:
        print("❌ Failed to get schema")

if __name__ == "__main__":
    main()
