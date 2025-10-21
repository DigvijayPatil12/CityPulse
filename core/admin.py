from django.contrib import admin
from .models import IssueReport, IssueImage

class IssueImageInline(admin.TabularInline):
    model = IssueImage
    extra = 0 # Don't show extra empty forms by default

@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('issue_type', 'latitude', 'longitude', 'status', 'reported_at', 'reporter')
    list_filter = ('status', 'issue_type')
    search_fields = ('description', 'reporter__username')
    inlines = [IssueImageInline]