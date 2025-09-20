#!/usr/bin/env python3
"""
Debug field detection
"""
import sys
sys.path.append('.')

from final_complete_server import top_level_fields

# Test field detection
query = "query { batchStockChartData { symbol } }"
fields = top_level_fields(query, None)
print(f"Query: {query}")
print(f"Detected fields: {fields}")
print(f"batchStockChartData in fields: {'batchStockChartData' in fields}")

query2 = "query { researchHub(symbol: \"AAPL\") { symbol } }"
fields2 = top_level_fields(query2, None)
print(f"\nQuery2: {query2}")
print(f"Detected fields: {fields2}")
print(f"researchHub in fields: {'researchHub' in fields2}")

query3 = "query { placeOptionOrder(input: {symbol: \"AAPL\"}) { success } }"
fields3 = top_level_fields(query3, None)
print(f"\nQuery3: {query3}")
print(f"Detected fields: {fields3}")
print(f"placeOptionOrder in fields: {'placeOptionOrder' in fields3}")
