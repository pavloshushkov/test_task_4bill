from django.db import models


class Request(models.Model):
    time = models.DateTimeField()
    amount = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.id)
