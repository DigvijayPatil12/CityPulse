# core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# Model for the reported issue
class IssueReport(models.Model):
    # Link to the user who reported the issue
    reporter = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # Keeps the report if user is deleted
        null=True, 
        blank=True
    )
    
    # Fields from the Issue Type step (Step 1)
    ISSUE_CHOICES = [
        ('garbage', 'Garbage'),
        ('pothole', 'Pothole'),
        ('waterlogging', 'Waterlogging'),
        ('street_light', 'Broken Streetlight'),
        # You can add the other categories here from your filter
        ('accident', 'Road Accident Zone'),
        ('crime', 'Crime Hotspot'),
        ('other', 'Other'),
    ]
    issue_type = models.CharField(
        max_length=50, 
        choices=ISSUE_CHOICES,
        default='other',
        verbose_name="Type of Issue"
    )
    sub_category = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name="Sub-Category"
    )
    
    # Fields from the Location step (Step 2)
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6
    )

    # Fields from the Details step (Step 3)
    description = models.TextField()

    # --- NEW FIELD FOR HEATMAP ---
    # This field will store the "weight" of the point for the heatmap.
    # We can set it to a default, or later use ML to change it.
    intensity = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.5')
    )
    # -----------------------------
    
    # Tracking information
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        default='Reported',
        choices=[
            ('Reported', 'Reported'),
            ('In Progress', 'In Progress'),
            ('Resolved', 'Resolved'),
        ]
    )

    def __str__(self):
        return f'{self.get_issue_type_display()} reported at ({self.latitude}, {self.longitude})'

# Model for images (since you allow multiple images per issue)
class IssueImage(models.Model):
    issue = models.ForeignKey(
        IssueReport, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='issue_photos/')
    
    def __str__(self):
        return f"Image for Issue {self.issue.id}"