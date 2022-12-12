from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views import generic
from django.utils import timezone
from datetime import datetime
from django.contrib import messages

from .models import SubjData, Course
from django.contrib import admin
from .models import UserInfo, Friend_Request, Study_Session, Study_Session_Request, Message
import json
import requests
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import datetime


class IndexView(generic.ListView):
    template_name = 'SBfinder/index.html'

    def get_queryset(self):
        """Return the last five published questions."""
        return 0;


def getClasses(request):
    # model = Course // I don't think this is needed here
    data = None
    classes = []

    if 'subjSearch' in request.GET and len(request.GET['subjSearch']) > 0:  # Check if the inputed search is a valid class subject
        subj = request.GET['subjSearch'].upper()
        url = "http://luthers-list.herokuapp.com/api/dept/" + subj + "?format=json"  # If subj is valid create the api link
        response = requests.get(url)  # for the cooresponding department
        data = response.json() # if there is nothing is subSearch, data variable will remain None


    if 'numSearch' in request.GET:# Check if the inputed search is a valid class number
        if len(request.GET['numSearch']) > 0 and len(request.GET['subjSearch']) == 0:
            messages.error(request, 'Please enter a valid department number for us to search!')
            return HttpResponseRedirect(reverse('SBfinder:class'))
        else:
            catNumb = request.GET['numSearch']
            if catNumb != "":
                for i in data:
                    num = i['catalog_number']
                    if num == catNumb:
                        classes.append(i)
            else:
                if data is not None:
                    for i in data:
                        classes.append(i)
                else: # if data is None, it means the user didn't input anything to the subjSearch, but the user is still able to get here,
                     # which means the user also did not input anything to the numSearch (otherwise ln46 will handle it). Note that we can
                     # therotically also handle this exception at ln47 by adding a elif statement to redirect to the double-no-entry scenerio.
                    messages.error(request, 'Please input something for us to search!')
                    return HttpResponseRedirect(reverse('SBfinder:class'))



    return render(request, 'SBfinder/class.html',
                      {"test": classes})  # Update their website with the subjects classes, changed url to class from /index





def create_user(request):
    # get the user only based on their user model and email and nothing else
    obj, created = UserInfo.objects.get_or_create(
        user_email=request.user.email,
        correspond_user=request.user,
    )

    # if this is a newly created user, we add slug and user name based on their userModel's user name,
    # but do not modify if this is not a newly created user model
    if created:
        obj.user_name = request.user.username
        obj.slug = request.user.username
        obj.save()

    return HttpResponseRedirect(reverse('SBfinder:class'))


def add_to_schedule(request):
    # load the context variable via POST; replace single quotation with double quotation
    class_added = json.loads(request.POST['class'].replace("\'", "\""))

    obj, created = Course.objects.get_or_create(
        instructor=class_added['instructor'],
        subject=class_added['subject'],
        course_number=class_added['course_number'],
        catalog_number=class_added['catalog_number'],
        description=class_added['description'],
        course_section=class_added['course_section'],
        meetings=class_added['meetings'],
        component=class_added['component'],

    )

    current_userInfo = UserInfo.objects.get(correspond_user=request.user)

    if obj in current_userInfo.course_set.all():
        messages.error(request, 'The class is alrady in your schedule!')
        return HttpResponseRedirect(reverse('SBfinder:class'))

    obj.users.add(current_userInfo)

    messages.success(request, 'The class has been successfully added!')
    return HttpResponseRedirect(reverse('SBfinder:class'))


def delete_from_schedule(request, id):
    c = Course.objects.get(id=id)
    current_userInfo = UserInfo.objects.get(correspond_user=request.user)
    c.users.remove(current_userInfo)
    messages.success(request, 'The class has been successfully deleted!')
    return HttpResponseRedirect(reverse('SBfinder:profile', args=(current_userInfo.slug,)))


def generate_SB(request):
    result_nameDic = {}

    SB_class_list = request.POST.getlist('checks')  # get all classes that have been checked

    # Get the current user to make sure we are not adding the current user to our SB list
    current_userInfo = UserInfo.objects.get(correspond_user=request.user)

    for SB in SB_class_list:
        Splitted = SB.split("|")
        idList = Splitted[2]
        idList = idList.replace("[", "")
        idList = idList.replace("]", "")
        idList = idList.split(",")
        for i in range(len(Splitted[0].split(","))):
            name = Splitted[0].split(",")[i]
            name = name.replace("[", "")
            name = name.replace("]", "")
            name = name.replace("<UserInfo: ", "")
            name = name.replace(">", "")

            # don't want to fetch a user you already fetched
            if str(name) + ","+idList[i] not in result_nameDic.keys():
                # prevents you from getting current user as a friend
                if str(name) != current_userInfo.user_name and int(idList[i]) != current_userInfo.pk:
                    result_nameDic[str(name) + "," +idList[i]] = []

            # get all the classes
            if str(name) != current_userInfo.user_name and int(idList[i]) != current_userInfo.pk:
                result_nameDic[str(name) + "," + idList[i]].append(Splitted[1])

    return render(request, 'SBfinder/SB_list.html', {"SB_Dic": result_nameDic})


# Send Friend Request
@login_required
def send_friend_request(request, userID):
    userID = int(userID)
    from_user = UserInfo.objects.get(correspond_user=request.user)
    to_user = UserInfo.objects.get(pk=userID)
    friend_request, created = Friend_Request.objects.get_or_create(from_user=from_user, to_user=to_user)

    # Ideally redirect users to a fancier page
    if created:
        messages.success(request, 'The friend request has been sent! Please wait for the other user to respond...')
        return HttpResponseRedirect(reverse('SBfinder:friend_request'))
    else:
        messages.error(request, 'The friend request was already sent!')
        return HttpResponseRedirect(reverse('SBfinder:friend_request'))


# Accept Friend Request
@login_required
def accept_friend_request(request, requestID):
    friend_request = Friend_Request.objects.get(pk=requestID)
    if friend_request.to_user == UserInfo.objects.get(correspond_user=request.user):
        friend_request.to_user.friends.add(friend_request.from_user)
        friend_request.from_user.friends.add(friend_request.to_user)
        friend_request.delete()

        # if the other user has sent a request to you as well, delete that request too
        from_me_to_others = Friend_Request.objects.filter(from_user = friend_request.to_user, to_user = friend_request.from_user).first()
        if from_me_to_others is not None:
            from_me_to_others.delete()

        messages.success(request, 'Friend request accepted.')
        return HttpResponseRedirect(reverse('SBfinder:friend_request'))

    else:
        messages.error(request, 'Friend request not accepted.')
        return HttpResponseRedirect(reverse('SBfinder:friend_request'))

def delete_friend(request, id):
    to_user = UserInfo.objects.get(id=id)
    current_userInfo = UserInfo.objects.get(correspond_user=request.user)
    to_user.friends.remove(current_userInfo)
    current_userInfo.friends.remove(to_user)

    for message in Message.objects.all():
        if (message.to_user == current_userInfo and message.from_user == to_user) or (message.from_user == current_userInfo and message.to_user == to_user):
            message.delete()

    messages.success(request, str(to_user.user_name) + ' has been removed from your friend list!')
    return HttpResponseRedirect(reverse('SBfinder:profile', args=(current_userInfo.slug,)) + '#friend')

# create the Study session object
@login_required()
def create_SS(request):
    # if the created ss has a date and time earlier than the current date and time, delete it
    # and return an error message

    if datetime.strptime(request.POST['study_session_date'] + " " + request.POST['study_session_time'],
                         '%Y-%m-%d %H:%M') <= datetime.now():
        messages.error(request, "Oops! A time in the past won't work!")
        return HttpResponseRedirect(reverse('SBfinder:generate_SS'))

    # proceed to create if not
    study_session, created = Study_Session.objects.get_or_create(
        title=request.POST['study_session_title'],
        description=request.POST['study_session_description'],
        date=request.POST['study_session_date'],
        time=request.POST['study_session_time'],
        exact_time=request.POST['study_session_date'] + " " + request.POST['study_session_time']
    )

    # add the current user  (the user who proposed this study session) to study_session.users
    current_userInfo = UserInfo.objects.get(correspond_user=request.user)
    study_session.users.add(current_userInfo)

    # get the id list of all friends whom we want to send this proposal to
    id_list = request.POST.getlist('study_session_checks')
    id_list = [int(id) for id in id_list]

    # send proposal request to all users who are checked
    for id in id_list:
        user = UserInfo.objects.get(pk=id)
        study_session_request, created = Study_Session_Request.objects.get_or_create(
            study_session=study_session,
            to_user=user,
        )

    messages.success(request, 'Your new study session has been created! Go to the study session section to check it out.')
    # redirect the user to his/her profile where all study sessions are displayed
    return HttpResponseRedirect(reverse('SBfinder:study_session'))


@login_required
def accept_SS_request(request, requestID):
    SS_request = Study_Session_Request.objects.get(pk=requestID)
    if SS_request.to_user == UserInfo.objects.get(correspond_user=request.user):
        SS_request.study_session.users.add(UserInfo.objects.get(correspond_user=request.user))
        SS_request.delete()

        messages.success(request, 'You have accepted this study session proposal.')
        return HttpResponseRedirect(reverse('SBfinder:study_session'))

    else:
        messages.success(request, 'You did not accept this study session proposal.')
        return HttpResponseRedirect(reverse('SBfinder:study_session'))


def leave_study_session(request, id):
    SS = Study_Session.objects.get(id=id)
    current_userInfo = UserInfo.objects.get(correspond_user=request.user)
    SS.users.remove(current_userInfo)
    messages.success(request, 'You have successfully left this study session!')
    return HttpResponseRedirect(reverse('SBfinder:study_session'))


# redirect users to the message page where all messages are contained
def message_log(request, id):
    to_user = UserInfo.objects.get(pk=id)
    from_user = UserInfo.objects.get(correspond_user = request.user)
    message_model = []  # list containing all messages between specified users
    for message in Message.objects.all():
        if (message.to_user == to_user and message.from_user == from_user) or (
                message.from_user == to_user and message.to_user == from_user):
            message_model.append(message)

    messages.success(request, 'All messages from the stream have been fetched and updated!')
    return render(request, 'SBfinder/send_message.html',
                  {"other_user": to_user, "message_model": message_model})


def generate_message(request, id):
    message, created = Message.objects.get_or_create(
        from_user=UserInfo.objects.get(correspond_user = request.user),
        to_user=UserInfo.objects.get(pk=id),
        message_body=request.POST['message_body'],
        time=timezone.now(),
    )

    return HttpResponseRedirect(reverse('SBfinder:message_log', args=(id, )))

@login_required
def upload_pic(request):
    current_user = UserInfo.objects.get(correspond_user = request.user)

    try:
        current_user.avatar = request.FILES['img']
        current_user.save()
        messages.success(request, 'Profile picture successfully uploaded!')
        return HttpResponseRedirect(reverse('SBfinder:setting', args=(current_user.pk, )))
    except MultiValueDictKeyError:
        messages.error(request, "Please upload a picture! We cannot save an empty picture.")
        return HttpResponseRedirect(reverse('SBfinder:setting', args=(current_user.pk,)))
    except ValueError:
        messages.error(request, "Please upload a picture in valid format (jpg, jpeg, png etc)!")
        return HttpResponseRedirect(reverse('SBfinder:setting', args=(current_user.pk,)))


@login_required
def update_profile(request):
    current_user = UserInfo.objects.get(correspond_user=request.user)
    if len(request.POST['user_name']) > 0:
        current_user.user_name = request.POST['user_name']

    current_user.year = request.POST['year']

    if len(request.POST['major']) > 0:
        current_user.major = request.POST['major']

    current_user.save()

    messages.success(request, 'Profile successfully updated!')
    return HttpResponseRedirect(reverse('SBfinder:setting', args=(current_user.pk,)))





# generic views -----------------------------------------------------------------------

@method_decorator(login_required, name='dispatch')
class UserProfileView(generic.DetailView):
    model = UserInfo

    # the currently logged-in user cannot switch to other user profiles by changing the url because we are obly getting the
    # userInfo objects that correspond to the currently logged in user
    def get_object(self, queryset=None):
        return get_object_or_404(UserInfo, correspond_user=self.request.user)

    template_name = 'SBfinder/userProfile.html'
    context_object_name = "userInfo"


class friendView(generic.ListView):
    template_name = 'SBfinder/friend_request.html'
    model = Friend_Request
    context_object_name = "friend_request"


# View of all upcoming study sessions the user has
class studyView(generic.ListView):
    template_name = 'SBfinder/study_session.html'
    model = Study_Session_Request
    context_object_name = "study_session_request"

# a seperate html page where user can submit a form to generate a Study session with his/her friends
class generateSSView(generic.DetailView):
    template_name = 'SBfinder/generateSS.html'
    model = UserInfo

    def get_object(self, queryset=None):
        return get_object_or_404(UserInfo, correspond_user=self.request.user)

    context_object_name = "userInfo"


# Similar to profile page
@method_decorator(login_required, name='dispatch')
class settingView(generic.DetailView):
    model = UserInfo

    # the currently logged-in user cannot switch to other user profiles by changing the url because we are obly getting the
    # userInfo objects that correspond to the currently logged in user
    def get_object(self, queryset=None):
        return get_object_or_404(UserInfo, correspond_user=self.request.user)

    template_name = 'SBfinder/setting.html'
    context_object_name = "userInfo"