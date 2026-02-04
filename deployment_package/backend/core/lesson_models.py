"""
Lesson model for the lesson library and daily brief.
Content is stored in DB; lesson_id in UserProgress/DailyBrief references Lesson.id.
"""
from django.db import models


class Lesson(models.Model):
    """Single lesson (2–5 min read). id is string for compatibility with lesson_id in progress/brief."""

    id = models.CharField(max_length=100, primary_key=True, help_text="Stable ID for progress tracking")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=2)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
    )
    category = models.CharField(max_length=50, db_index=True)
    concepts = models.JSONField(default=list, help_text="List of concept tags")
    content = models.TextField()
    key_takeaways = models.JSONField(default=list, help_text="List of takeaway strings")
    order = models.PositiveIntegerField(default=0, help_text="Display order in library")

    class Meta:
        db_table = "core_lessons"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({self.id})"
