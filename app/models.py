from django.db import models


class PapalStats(models.Model):

    server = models.CharField(max_length=255)
    flag = models.CharField(max_length=255)
    level = models.CharField(max_length=10)
    date = models.DateField()
    data = models.TextField()
    md5 = models.CharField(max_length=500)
