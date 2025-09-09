#!/usr/bin/env python3

import re

# Read the HomeScreen file
with open('mobile/screens/HomeScreen.tsx', 'r') as f:
    content = f.read()

# Find the start of the old financial knowledge database
start_pattern = r'  const openChat = \(\) => \{\s*\'etf\': \{'
end_pattern = r'Feel free to ask about any of these topics or try one of the quick prompts above!\`;\s*  \};'

# Find the start and end positions
start_match = re.search(start_pattern, content, re.DOTALL)
end_match = re.search(end_pattern, content, re.DOTALL)

if start_match and end_match:
    # Replace the old code with just the openChat function
    old_code = content[start_match.start():end_match.end()]
    new_code = '''  const openChat = () => {
    setChatOpen(true);
    if (chatMessages.length === 0) {
      setChatMessages([
        {
          id: String(Date.now()),
          role: 'assistant',
          content:
            ' Welcome to your Financial AI Assistant!\\n\\nI can help you with:\\n• Investment basics (ETFs, index funds, stocks)\\n• Retirement planning (IRAs, 401(k)s)\\n• Budgeting strategies (50/30/20 rule)\\n• Risk management and diversification\\n• Financial terminology and concepts\\n\\n This is educational information only. For personalized financial advice, consult a qualified financial advisor.\\n\\nTry a quick prompt below or ask me anything about personal finance!',
        },
      ]);
    }
  };'''
    
    # Replace the old code
    new_content = content[:start_match.start()] + new_code + content[end_match.end():]
    
    # Write the fixed content
    with open('mobile/screens/HomeScreen.tsx', 'w') as f:
        f.write(new_content)
    
    print("HomeScreen.tsx has been fixed!")
else:
    print("Could not find the old code to replace")
