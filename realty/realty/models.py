from django.db import models


class RealtyAd(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=4096, blank=False)
    thumbnail = models.CharField(max_length=4096, blank=True)
    title = models.CharField(max_length=1024, blank=True)
    short_description = models.TextField(max_length=8096, blank=True)
    price = models.IntegerField(default=0, blank=False)
    type = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=512, blank=True)

    class Meta:
        pass

    def __str__(self):
        return "%s" % self.title
