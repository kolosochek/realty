from django.db import models


class RealtyAd(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=4096, blank=False)
    title = models.CharField(max_length=1024, blank=True)

    class Meta:
        pass

    def __str__(self):
        return "%s" % self.title
