from django.contrib import admin
from home import models

# Customize admin header and titles
admin.site.site_header = "Smartparichaya Admin"
admin.site.site_title = "Smartparichaya Admin Portal"
admin.site.index_title = "Welcome to Smartparichaya Admin Dashboard"

# Register models
admin.site.register(models.Contact)
admin.site.register(models.Blog)
admin.site.register(models.Feedback)
admin.site.register(models.Profile)
admin.site.register(models.ResumeCount)
