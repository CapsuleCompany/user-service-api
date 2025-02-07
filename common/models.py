from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Base model with commonly needed fields for all models to inherit.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for each record.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The timestamp when this record was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="The timestamp when this record was last updated."
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
