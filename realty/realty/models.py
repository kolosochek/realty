from django.db import models
from datetime import date


class Image(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=8096, blank=False)
    thumbnail = models.CharField(max_length=8096, blank=True)
    source = models.ImageField(upload_to="salesme_images", default="noimage.jpg")
    title = models.CharField(max_length=1024, blank=True)

    def __str__(self):
        return "%s" % self.url


class RealtyAd(models.Model):
    id = models.BigAutoField(primary_key=True)
    ad_id = models.CharField(max_length=1024, blank=True)
    url = models.CharField(max_length=8096, blank=False)
    thumbnail = models.CharField(max_length=4096, blank=True)
    title = models.CharField(max_length=1024, blank=True)
    short_description = models.TextField(max_length=8096, blank=True)
    long_description = models.TextField(max_length=8096, blank=True)
    price = models.IntegerField(default=0, blank=False, null=True)
    type = models.CharField(max_length=128, blank=True)
    address = models.CharField(max_length=4096, blank=True)
    city = models.CharField(max_length=512, blank=True)
    phones = models.CharField(max_length=4096, blank=True)
    telegram = models.CharField(max_length=4096, blank=True)
    whatsapp = models.CharField(max_length=4096, blank=True)
    viber = models.CharField(max_length=4096, blank=True)
    date_posted = models.DateField(default=date.today, blank=True)
    ad_author = models.CharField(max_length=4096, blank=True)
    images = models.ManyToManyField(Image)

    class Meta:
        pass

    def __str__(self):
        return "%s" % self.title
