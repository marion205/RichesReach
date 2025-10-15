#!/usr/bin/env python3

import re

# Read the file
with open('screens/PremiumAnalyticsScreen.tsx', 'r') as f:
    content = f.read()

# Fix the problematic patterns
# 1. Fix orphaned object properties in useEffect
content = re.sub(r'useEffect\(\(\) => \{\s*metricsLoading,\s*hasMetricsData: !!metricsData,\s*hasPortfolioMetrics: !!metricsData\?\.portfolioMetrics\s*\}\);', 
                'useEffect(() => {\n  // Debug logging\n}, [metricsLoading, metricsData]);', content)

# 2. Fix orphaned object properties in functions
content = re.sub(r'const handleDiscussionComment = \(discussionId: string\) => \{\s*discussionId: discussionId,\s*discussionsData: discussionsData,\s*stockDiscussions: discussionsData\?\.stockDiscussions\s*\}\);', 
                'const handleDiscussionComment = (discussionId: string) => {\n  // Debug logging\n  // Open discussion detail instead of comment modal (X-style)', content)

# 3. Fix orphaned object properties in try blocks
content = re.sub(r'try \{\s*discussionId: selectedDiscussionId,\s*content: commentContent\.trim\(\)\s*\}\);', 
                'try {\n  // Debug logging', content)

# 4. Fix orphaned object properties in other functions
content = re.sub(r'totalStrategies: strategies\.length,\s*marketOutlook,\s*strategies: strategies\.map\(s => \(\{ name: s\.strategyName, outlook: s\.marketOutlook, type: s\.strategyType \}\)\)\s*\}\);', 
                '// Debug logging\n  // If no specific outlook is selected, show all strategies', content)

# Write the fixed content back
with open('screens/PremiumAnalyticsScreen.tsx', 'w') as f:
    f.write(content)

print("Syntax errors fixed!")
