from django.db import models


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    last_modify = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
