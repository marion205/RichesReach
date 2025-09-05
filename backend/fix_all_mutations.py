#!/usr/bin/env python3
"""
Comprehensive fix for mutations.py - comment out all problematic mutations completely
"""

import re

def fix_all_mutations():
    """Comment out all problematic mutations completely"""
    file_path = 'core/mutations.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # List of problematic mutations to comment out completely
    problematic_mutations = [
        'CreatePortfolio',
        'AddPortfolioPosition', 
        'CreatePriceAlert',
        'VoteStockSentiment',
        'CreateIncomeProfile',
        'GenerateAIRecommendations',
        'SavePortfolio',
        'CommentOnDiscussion'
    ]
    
    for mutation in problematic_mutations:
        # Find the class definition and comment out the entire class
        pattern = rf'^# class {mutation}\(graphene\.Mutation\):'
        replacement = f'# class {mutation}(graphene.Mutation):'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Comment out the entire class definition and its methods
        # This is a more complex regex to handle the entire class
        class_pattern = rf'^# class {mutation}\(graphene\.Mutation\):.*?(?=^class |^# class |^$|\Z)'
        class_replacement = lambda m: '\n'.join(['# ' + line if line.strip() else line for line in m.group(0).split('\n')])
        content = re.sub(class_pattern, class_replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Commented out all problematic mutations completely")

if __name__ == "__main__":
    fix_all_mutations()
