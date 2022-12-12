from django.contrib import admin

# Register your models here.
from .models import SubjData, Course, Friend_Request, Study_Session, UserInfo

from import_export import resources
from import_export.admin import ImportExportModelAdmin    #added to allow importing the json list of subjects to the databasre

class SubjResource(resources.ModelResource):
   class Meta:
      model = SubjData
class SubjAdmin(ImportExportModelAdmin):
   resource_class = SubjResource

admin.site.register(SubjData,SubjAdmin)
admin.site.register(Course)
admin.site.register(Friend_Request)
admin.site.register(Study_Session)
admin.site.register(UserInfo)