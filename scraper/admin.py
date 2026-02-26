# scraper/admin.py
from django.contrib import admin
from .models import Opportunity

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'university', 'source_type', 'created_at')
    
    # This adds a search bar and filters
    search_fields = ('title', 'university', 'description')
    list_filter = ('university', 'source_type', 'created_at')