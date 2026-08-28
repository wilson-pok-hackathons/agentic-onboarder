import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimestampedModel(models.Model):
    """Abstract base model providing creation and modification timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ResearchProfile(TimestampedModel):
    '''the profile of who a user is, what their use for the platform is, and how they
    interact with the platform.
    '''
    class ExpertiseLevel(models.TextChoices):
        '''restricts CharField choices options for expertise level'''
        GENERAL = "general", "General reader"   # Django syntax that stores db term, user facing term
        STUDENT = "student", "Student"
        RESEARCHER = "researcher", "Researcher"
        EXPERT = "expert", "Domain expert"

    class SummaryStyle(models.TextChoices):
        '''restricts CharField choices options for summary style'''
        PLAIN = "plain", "Plain language"
        TECHNICAL = "technical", "Technical"
        BALANCED = "balanced", "Balanced"

    class QuerySyncStatus(models.TextChoices):
        OK = "ok", "OK"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # every account gets exactly one ResearchProfile
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_profile",
    )
    expertise_level = models.CharField(
        max_length=20,
        choices=ExpertiseLevel.choices,
        default=ExpertiseLevel.GENERAL,
    )

    # blob of holistic context per user, captures relationships between interests
    # that discrete tags can't. Powers LLM's qualitative judgement
    research_focus = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Freeform description of the user's research interests/focus, "
            "in their own words. Fed directly to the LLM as context when "
            "judging paper relevance and ranking"
        )
    )

    summary_style = models.CharField(
        max_length=20,
        choices=SummaryStyle.choices,
        default=SummaryStyle.BALANCED,
    )
    timezone = models.CharField(max_length=64, default="UTC")
    last_paper_check_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "When we last queried Semantic Scholar for new papers for "
            "this user. Papers published after this timestamp are "
            "considered 'new' on the next check. Null until the first "
            "check ever runs."
        ),
    )
    query_sync_status = models.CharField(
        max_length=20,
        choices=QuerySyncStatus.choices,
        default=QuerySyncStatus.OK,
    )
    setup_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["user_id"]

    def __str__(self):
        return f"Research profile for {self.user}"


class UserInterest(TimestampedModel):
    '''tracks the actual interest of a user'''
    class Kind(models.TextChoices):
        '''restricts the CharField choices of kind. Decribes the type of interest a
        row is concerning
        '''
        TOPIC = "topic", "Topic"        # layer 1 filter, one of the semantic scholar API valid fields
        KEYWORD = "keyword", "Keyword"  # layer 2 filter, free entry user specified topic (e.g. bioinformatics)
        AUTHOR = "author", "Author"     # layer 2 filter, free entry user specified author
        VENUE = "venue", "Journal or conference"    # layer 2 filter, free entry user specified venue
        EXCLUDE = "exclude", "Exclude"  # layer 2 filter, free entry user specified exclusion

    class FieldOfStudy(models.TextChoices):
        '''the 23 canonical fields available via the semantic scholar API'''
        COMPUTER_SCIENCE = "Computer Science", "Computer Science"
        MEDICINE = "Medicine", "Medicine"
        CHEMISTRY = "Chemistry", "Chemistry"
        BIOLOGY = "Biology", "Biology"
        MATERIALS_SCIENCE = "Materials Science", "Materials Science"
        PHYSICS = "Physics", "Physics"
        GEOLOGY = "Geology", "Geology"
        PSYCHOLOGY = "Psychology", "Psychology"
        ART = "Art", "Art"
        HISTORY = "History", "History"
        GEOGRAPHY = "Geography", "Geography"
        SOCIOLOGY = "Sociology", "Sociology"
        BUSINESS = "Business", "Business"
        POLITICAL_SCIENCE = "Political Science", "Political Science"
        ECONOMICS = "Economics", "Economics"
        PHILOSOPHY = "Philosophy", "Philosophy"
        MATHEMATICS = "Mathematics", "Mathematics"
        ENGINEERING = "Engineering", "Engineering"
        ENVIRONMENTAL_SCIENCE = "Environmental Science", "Environmental Science"
        AGRICULTURAL_AND_FOOD_SCIENCES = "Agricultural and Food Sciences", "Agricultural and Food Sciences"
        EDUCATION = "Education", "Education"
        LAW = "Law", "Law"
        LINGUISTICS = "Linguistics", "Linguistics"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_interests",
    )

    # describes the category of this row
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.TOPIC,
    )
    label = models.CharField(max_length=160)

    # text used to filter papers AFTER layer 1
    query = models.CharField(
        max_length=500,
        help_text="Provider search query or normalized matching text.",
    )
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=1,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1),
        ],
    )
    active = models.BooleanField(default=True)

    class Meta:
        '''concerns the ordering when accessing the table and maintaining db integrity'''
        ordering = ["-weight", "label"]     # descending order by weight, then by label

        # makes sure no rows duplicate user, kind, query
        constraints = [
            models.UniqueConstraint(
                fields=["user", "kind", "query"],
                name="unique_user_interest_query",
            )
        ]

    def __str__(self):
        return self.label


class Paper(TimestampedModel):
    """Normalized scholarly-paper metadata with the original provider data."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    semantic_scholar_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )
    corpus_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
    )
    doi = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    title = models.TextField()
    abstract = models.TextField(blank=True)
    publication_date = models.DateField(null=True, blank=True)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    venue = models.CharField(max_length=300, blank=True)
    publication_types = models.JSONField(default=list, blank=True)

    url = models.URLField(max_length=1000, blank=True)
    open_access_pdf_url = models.URLField(max_length=1000, blank=True)
    is_open_access = models.BooleanField(default=False)

    citation_count = models.PositiveIntegerField(default=0)
    influential_citation_count = models.PositiveIntegerField(default=0)
    reference_count = models.PositiveIntegerField(default=0)

    journal = models.JSONField(
        default=dict,
        blank=True,
    )

    fields_of_study = models.JSONField(
        default=list,
        blank=True,
        help_text="Simple field names returned by the provider.",
    )


    class Meta:
        ordering = ["-publication_date", "-created_at"]
        indexes = [
            models.Index(fields=["publication_date"]),
            models.Index(fields=["publication_year"]),
            models.Index(fields=["citation_count"]),
        ]

    def __str__(self):
        return self.title


class Author(TimestampedModel):
    """Represents an author returned by a scholarly metadata provider."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semantic_scholar_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=300)
    affiliations = models.JSONField(default=list, blank=True)
    homepage_url = models.URLField(max_length=1000, blank=True)

    papers = models.ManyToManyField(
        Paper,
        through="PaperAuthor",
        related_name="authors",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PaperAuthor(models.Model):
    """Ordered many-to-many relationship between papers and their authors."""

    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="author_links",
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="paper_links",
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["paper", "author"],
                name="unique_paper_author",
            ),
            models.UniqueConstraint(
                fields=["paper", "position"],
                name="unique_paper_position",
            ),
        ]

class UserPaper(TimestampedModel):
    """Tracks a user's current relationship with a discovered paper."""

    class State(models.TextChoices):
        UNREAD = "unread", "Unread"
        READ = "read", "Read"
        SAVED = "saved", "Saved"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paper_states",
    )
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="user_states",
    )
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.UNREAD,
    )
    latest_relevance_score = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1),
        ]
    )

    source_query = models.CharField(max_length=500, blank=True)
    source_item_id = models.CharField(max_length=255, blank=True)

    latest_rationale = models.TextField(blank=True)
    first_recommended_at = models.DateTimeField(null=True, blank=True)
    last_recommended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "paper"],
                name="unique_user_paper",
            )
        ]


class Digest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class DigestItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    digest = models.ForeignKey(
        Digest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField()
    summary = models.TextField()

    class Meta:
        ordering = ["rank"]
        constraints = [
            models.UniqueConstraint(
                fields=["digest", "paper"],
                name="unique_digest_paper",
            ),
            models.UniqueConstraint(
                fields=["digest", "rank"],
                name="unique_digest_rank",
            ),
        ]


class FeedbackEvent(models.Model):
    """Records an immutable user reaction used to improve future ranking."""

    class Action(models.TextChoices):
        RELEVANT = "relevant", "Relevant"
        NOT_RELEVANT = "not_relevant", "Not relevant"
        SAVE = "save", "Save"
        UNSAVE = "unsave", "Unsave"
        READ = "read", "Read"
        DISMISS = "dismiss", "Dismiss"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_feedback",
    )
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="feedback_events",
    )
    digest_item = models.ForeignKey(
        DigestItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_events",
    )
    action = models.CharField(max_length=24, choices=Action.choices)
    reason = models.CharField(
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ProcessingRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=20, default="pending")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
        ]
