from django.contrib import admin
from home import models

# Register your models here.


admin.site.register(models.Contact)
admin.site.register(models.Blog)
admin.site.register(models.Feedback)
admin.site.register(models.Profile)
admin.site.register(models.ResumeCount)
