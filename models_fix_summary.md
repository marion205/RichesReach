# models.py Indentation Fixes Applied

## ✅ Fixed Issues

### 1. Line 34 - Comment indentation
```python
# FIXED:
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. Post class methods (Lines 99-110)
```python
# FIXED:
    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"
    
    @property
    def likes_count(self):
        return self.likes.count()
```

### 3. ChatSession __str__ (Line 116-117)
```python
# FIXED:
    def __str__(self):
        return f"{self.user.name} - {self.title or 'Chat Session'} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
```

### 4. ChatMessage Meta class and ROLE_CHOICES (Lines 119-133)
```python
# FIXED:
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
```

### 5. Source __str__ (Line 139-140)
```python
# FIXED:
    def __str__(self):
        return self.title
```

### 6. Like Meta class (Lines 145-149)
```python
# FIXED:
    class Meta:
        unique_together = ['user', 'post']
        db_table = 'core_like'
    
    def __str__(self):
        return f"{self.user.name} likes {self.post.content[:30]}"
```

### 7. Comment Meta class (Lines 155-161)
```python
# FIXED:
    class Meta:
        ordering = ['created_at']
        db_table = 'core_comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"
```

### 8. Follow Meta class (Lines 166-170)
```python
# FIXED:
    class Meta:
        unique_together = ['follower', 'following']
        db_table = 'core_follow'
    
    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"
```

### 9. Stock __str__ and Meta (Lines 184-187)
```python
# FIXED:
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
    
    class Meta:
        ordering = ['symbol']
```

### 10. StockData Meta class (Lines 197-199)
```python
# FIXED:
    class Meta:
        unique_together = ['stock', 'date']
        ordering = ['-date']
```

### 11. Watchlist Meta class (Lines 213-217)
```python
# FIXED:
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.stock.symbol}"
```

### 12. IncomeProfile __str__ (Line 237-238)
```python
# FIXED:
    def __str__(self):
        return f"{self.user.name} - {self.risk_tolerance} Profile"
```

### 13. IncomeProfile choices (Lines 224-234)
```python
# FIXED:
    risk_tolerance = models.CharField(max_length=20, choices=[
        ('Conservative', 'Conservative'),
        ('Moderate', 'Moderate'),
        ('Aggressive', 'Aggressive')
    ])
    investment_horizon = models.CharField(max_length=20, choices=[
        ('1-3 years', '1-3 years'),
        ('3-5 years', '3-5 years'),
        ('5-10 years', '5-10 years'),
        ('10+ years', '10+ years')
    ])
```

### 14. AIPortfolioRecommendation Meta (Lines 253-256)
```python
# FIXED:
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.risk_profile} Portfolio ({self.created_at.strftime('%Y-%m-%d')})"
```

### 15. Portfolio Meta and save method (Lines 268-280)
```python
# FIXED:
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.stock.symbol} ({self.shares} shares)"
    
    def save(self, *args, **kwargs):
        # Calculate total value if current_price is provided
        if self.current_price and self.shares:
            self.total_value = self.current_price * self.shares
        # Set average_price to current_price if not set
        if not self.average_price and self.current_price:
            self.average_price = self.current_price
        super().save(*args, **kwargs)
```

### 16. StockDiscussion Meta and properties (Lines 301-310)
```python
# FIXED:
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.user.name}"
    
    @property
    def score(self):
        return self.upvotes - self.downvotes
    
    @property
    def comment_count(self):
        return self.comments.count()
```

### 17. DiscussionComment Meta and properties (Lines 322-331)
```python
# FIXED:
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.name} on {self.discussion.title}"
    
    @property
    def score(self):
        return self.upvotes - self.downvotes
    
    @property
    def reply_count(self):
        return self.replies.count()
```

### 18. StockDiscussion VISIBILITY_CHOICES (Line 283-286)
```python
# FIXED:
    VISIBILITY_CHOICES = [
        ('public', 'Public - Everyone can see'),
        ('followers', 'Followers Only - Only followers can see'),
    ]
```

## ✅ All Indentation Issues Fixed!

All methods, properties, Meta classes, and nested structures now have proper indentation:
- Class fields: 4 spaces
- Methods: 4 spaces (def line)
- Method bodies: 8 spaces
- Meta classes: 4 spaces (class line)
- Meta content: 8 spaces
- Nested lists/choices: 8 spaces

