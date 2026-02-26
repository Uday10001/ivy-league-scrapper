from django.db import models

class Opportunity(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField(unique=True)
    university = models.CharField(max_length=200)
    source_type = models.CharField(max_length=100) # events, careers, etc.
    deadline = models.CharField(max_length=200, null=True, blank=True)
    content_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.university} - {self.title}"