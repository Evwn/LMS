from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


NEWS = _("News")
EVENTS = _("Event")

POST = (
    (NEWS, _("News")),
    (EVENTS, _("Event")),
)

FIRST = _("First")
SECOND = _("Second")
THIRD = _("Third")

SEMESTER = (
    (FIRST, _("First")),
    (SECOND, _("Second")),
    (THIRD, _("Third")),
)


class NewsAndEventsQuerySet(models.query.QuerySet):
    def search(self, query):
        lookups = (
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(posted_as__icontains=query)
        )
        return self.filter(lookups).distinct()


class NewsAndEventsManager(models.Manager):
    def get_queryset(self):
        return NewsAndEventsQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(
            id=id
        )  # NewsAndEvents.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().search(query)


class NewsAndEvents(models.Model):
    title = models.CharField(max_length=200, null=True)
    summary = models.TextField(max_length=200, blank=True, null=True)
    posted_as = models.CharField(choices=POST, max_length=10)
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    objects = NewsAndEventsManager()

    def __str__(self):
        return f"{self.title}"


class Session(models.Model):
    session = models.CharField(max_length=200, unique=True)
    is_current_session = models.BooleanField(default=False, blank=True, null=True)
    next_session_begins = models.DateField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.session}"
    
    def get_progress(self):
        """Calculate session progress as a percentage."""
        from datetime import datetime
        today = datetime.now().date()
        
        # Use exactly the database fields for start and end dates
        start_date = self.created_at  # When the session started
        end_date = self.next_session_begins  # When the session will end
        
        # If missing end date, can't calculate progress
        if not end_date:
            return 0
            
        # If we're past the end date, progress is 100%
        if today >= end_date:
            return 100
            
        # Calculate total session days and days elapsed
        total_days = (end_date - start_date).days
        days_elapsed = (today - start_date).days
        
        # Handle edge cases
        if total_days <= 0 or days_elapsed < 0:
            return 0
            
        # Calculate percentage completed
        progress = min(100, max(0, (days_elapsed / total_days) * 100))
        return int(progress)
    
    def get_days_remaining(self):
        """Calculate days remaining in the session."""
        from datetime import datetime
        today = datetime.now().date()
        end_date = self.next_session_begins  # When the session will end
        
        # If no end date set, can't calculate days remaining
        if not end_date:
            return 0
            
        # If we're past the end date, no days remaining
        if today >= end_date:
            return 0
            
        # Calculate and return days remaining
        return (end_date - today).days


class Semester(models.Model):
    semester = models.CharField(max_length=10, choices=SEMESTER, blank=True)
    is_current_semester = models.BooleanField(default=False, blank=True, null=True)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=True, null=True
    )
    next_semester_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.semester}"


class ActivityLog(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.created_at}]{self.message}"
