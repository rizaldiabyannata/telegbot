from django.db import models

# Create your models here.
class scheduler(models.Model):
    Matkul = models.CharField(max_length=225)
    Dateline = models.DateTimeField()
    Keterangan = models.TextField()
    STATUS_CHOICES = [(1, "SELESAI"), (0, "TIDAK SELESAI")]
    Status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    
    def __str__(self):
        return "{}".format(self.Matkul)

class data_api(models.Model):
    telegram_api = models.CharField(max_length=255)
    openai_api = models.CharField(max_length=255)
    chatId_telegram = models.CharField(max_length=100)