# models.py Indentation Fix Guide

## Issues Found

### Issue 1: Line 34 - Comment not indented
```python
# Line 34 (WRONG):
# Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

# Should be:
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
```

### Issue 2: Post class methods (Lines 99-110)
```python
# Lines 99-110 (WRONG):
    def __str__(self):
    return f"{self.user.name}: {self.content[:30]}"
    @property
    def likes_count(self):
    return self.likes.count()

# Should be:
    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"
    
    @property
    def likes_count(self):
        return self.likes.count()
```

### Issue 3: ChatSession __str__ (Lines 116-117)
```python
# Lines 116-117 (WRONG):
    def __str__(self):
    return f"{self.user.name} - {self.title or 'Chat Session'} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

# Should be:
    def __str__(self):
        return f"{self.user.name} - {self.title or 'Chat Session'} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
```

### Issue 4: ChatMessage Meta class (Lines 130-133)
```python
# Lines 130-133 (WRONG):
class Meta:
ordering = ['created_at']
def __str__(self):
return f"{self.role}: {self.content[:50]}..."

# Should be:
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
```

### Issue 5: Source __str__ (Lines 139-140)
```python
# Lines 139-140 (WRONG):
    def __str__(self):
    return self.title

# Should be:
    def __str__(self):
        return self.title
```

### Issue 6: Like Meta class (Lines 145-149)
```python
# Lines 145-149 (WRONG):
class Meta:
unique_together = ['user', 'post']
db_table = 'core_like'
def __str__(self):
return f"{self.user.name} likes {self.post.content[:30]}"

# Should be:
    class Meta:
        unique_together = ['user', 'post']
        db_table = 'core_like'
    
    def __str__(self):
        return f"{self.user.name} likes {self.post.content[:30]}"
```

### Issue 7: Comment Meta class (Lines 155-161)
```python
# Lines 155-161 (WRONG):
class Meta:
ordering = ['created_at']
db_table = 'core_comment'
verbose_name = 'Comment'
verbose_name_plural = 'Comments'
def __str__(self):
return f"{self.user.name}: {self.content[:30]}"

# Should be:
    class Meta:
        ordering = ['created_at']
        db_table = 'core_comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"{self.user.name}: {self.content[:30]}"
```

### Issue 8: Follow Meta class (Lines 166-170)
```python
# Lines 166-170 (WRONG):
class Meta:
unique_together = ['follower', 'following']
db_table = 'core_follow'
def __str__(self):
return f"{self.follower.name} follows {self.following.name}"

# Should be:
    class Meta:
        unique_together = ['follower', 'following']
        db_table = 'core_follow'
    
    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"
```

### Issue 9: Stock __str__ and Meta (Lines 184-187)
```python
# Lines 184-187 (WRONG):
    def __str__(self):
    return f"{self.symbol} - {self.company_name}"
class Meta:
ordering = ['symbol']

# Should be:
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
    
    class Meta:
        ordering = ['symbol']
```

## Pattern to Fix

**Rule**: All content inside a class must be indented 4 spaces from the class definition.

**Examples**:
- Field definitions: `4 spaces` (e.g., `    email = models.EmailField(...)`)
- Methods: `4 spaces` (e.g., `    def __str__(self):`)
- Method body: `8 spaces` (e.g., `        return self.email`)
- Nested classes (Meta): `4 spaces` (e.g., `    class Meta:`)
- Meta class content: `8 spaces` (e.g., `        ordering = [...]`)

