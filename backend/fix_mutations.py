#!/usr/bin/env python3
"""
Quick fix for mutations.py - comment out problematic mutations
"""

import re

def fix_mutations():
    """Comment out problematic mutations"""
    file_path = 'core/mutations.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # List of problematic mutations to comment out
    problematic_mutations = [
        'CommentOnDiscussion',
        'CreatePortfolio', 
        'AddPortfolioPosition',
        'CreatePriceAlert',
        'VoteStockSentiment',
        'CreateIncomeProfile',
        'GenerateAIRecommendations',
        'SavePortfolio'
    ]
    
    for mutation in problematic_mutations:
        # Find the class definition and comment it out
        pattern = rf'^class {mutation}\(graphene\.Mutation\):'
        replacement = f'# class {mutation}(graphene.Mutation):'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Also comment out any references in the Mutation class
        pattern = rf'    {mutation.lower()}_field = {mutation}\.Field\(\)'
        replacement = f'    # {mutation.lower()}_field = {mutation}.Field()'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Commented out problematic mutations")

if __name__ == "__main__":
    fix_mutations()
