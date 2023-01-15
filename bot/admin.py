from django.contrib import admin

from .models import scheduler
from .models import data_api

admin.site.register(scheduler)
admin.site.register(data_api)

