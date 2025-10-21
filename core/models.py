from django.db import models

from django.contrib.auth import get_user_model # Use this if issues are linked to a logged-in user

User = get_user_model()

# Model for the reported issue
class IssueReport(models.Model):
    # Link to the user who reported the issue (optional: depends on your app logic)
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
    ]
    issue_type = models.CharField(
        max_length=50, 
        choices=ISSUE_CHOICES,
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
        return f'{self.issue_type} reported at ({self.latitude}, {self.longitude})'

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
# Create your models here.