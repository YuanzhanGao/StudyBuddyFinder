from django.db import models
from datetime import datetime
from django.conf import settings #Foreign Key?
from django_resized import ResizedImageField
# Create your models here.


class SubjData(models.Model):
    subject = models.CharField(max_length=4) #Added to store all possible subjects in the database
    def __str__(self):
        return self.subject

class UserInfo(models.Model):
    user_name = models.CharField(max_length = 255)
    user_email = models.EmailField(max_length = 255)
    correspond_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE)
    slug = models.SlugField(null=True, max_length = 255)
    friends = models.ManyToManyField("self", blank = True)
    avatar = models.ImageField(default = "default.jpg", blank=True, null=True)
    year = models.CharField(max_length = 255, blank = True)
    major = models.CharField(max_length = 255, blank = True)


    def __str__(self):
        return self.user_name


class Friend_Request(models.Model):
    from_user = models.ForeignKey(UserInfo, related_name = 'from_user', on_delete= models.CASCADE)
    to_user = models.ForeignKey(UserInfo, related_name='to_user', on_delete=models.CASCADE)

    def __str__(self):
        return "From" + self.from_user.user_name + " to " + self.to_user.user_name


class Course(models.Model):
    instructor = models.CharField(max_length=255, blank = True, null = True)
    course_number = models.CharField(max_length=255, blank = True, null = True)
    subject = models.CharField(max_length=255, blank = True, null = True)
    catalog_number = models.CharField(max_length=255, blank = True, null = True)
    description = models.CharField(max_length=255, blank = True, null = True)
    course_section = models.CharField(max_length=255, blank = True, null = True)
    meetings = models.CharField(max_length=255, blank = True, null = True)
    component = models.CharField(max_length=255, blank = True, null = True)
    users = models.ManyToManyField(UserInfo)

    def __str__(self):
        representation_list = str(list(self.users.all())) + "|" + str(self.subject) + " " + str(self.catalog_number) + " " +str(self.description) + "|" + str([user.pk for user in self.users.all()])

        return representation_list

class Study_Session(models.Model):
    title = models.CharField(max_length=255, blank = True, null = True)
    description = models.CharField(max_length=255, blank = True, null = True)
    time = models.TimeField()
    date = models.DateTimeField('date proposed')
    exact_time = models.DateTimeField('Exact time proposed') # exact time of the proposal by combing the previous two together
    users = models.ManyToManyField(UserInfo)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['exact_time']

class Study_Session_Request(models.Model):
    study_session = models.ForeignKey(Study_Session, on_delete= models.CASCADE)
    to_user = models.ForeignKey(UserInfo, related_name='to_user_ss', on_delete=models.CASCADE)

class Message(models.Model):
    time = models.DateTimeField('time sent')
    from_user = models.ForeignKey(UserInfo, related_name='from_user_message', on_delete=models.CASCADE)
    to_user = models.ForeignKey(UserInfo, related_name='to_user_message', on_delete=models.CASCADE)
    message_body = models.CharField(max_length=1000, blank = True, null = True)

    class Meta:
        ordering = ['time']
