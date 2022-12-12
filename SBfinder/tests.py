from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.urls import reverse
from SBfinder.models import Course, Friend_Request, UserInfo, Study_Session_Request, Study_Session, Message
from .views import send_friend_request
from .views import accept_friend_request
from .views import add_to_schedule
from .views import getClasses


# Create your tests here.
class GoogleLoginTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email='test@example.com')
        self.client = Client()
        self.user.save()

    def test_correct(self):
        # user = authenticate(username='test', password='12test12')
        # self.assertTrue((user is not None) and user.is_authenticated)
        self.client.login(username='test', password='12test12')

    '''def test_incorrect(self):
        #user = authenticate(username='test', password='12test12')
        #self.assertTrue((user is not None) and user.is_authenticated)
        self.client.login(username='test', password='wrongpass')
        self.assertFalse(user.is_authenticated)'''

    def test_successful_login(self):
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_correct_user_info(self):
        self.assertEquals(self.user.username, 'test')
        # don't include password because django doesn't store raw password but rather the hash of it
        self.assertEquals(self.user.email, 'test@example.com')


def create_course(instructor, course_number, subject, catalog_number, description, course_section,
                  meetings, component):
    return Course.objects.create(instructor=instructor, course_number=course_number,
                                 subject=subject, catalog_number=catalog_number, description=description,
                                 course_section=course_section, meetings=meetings, component=component)


def create_user_info(user_name, user_email, correspond_user, slug):
    return UserInfo.objects.create(user_name=user_name, user_email=user_email, correspond_user=correspond_user,
                                   slug=slug)


class SearchTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email='test@example.com')
        self.client = Client()
        self.user.save()
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)

    def test_no_courses(self):
        response = self.client.get(reverse('SBfinder:class'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Oops!")

    def test_course_added(self):
        course = create_course(instructor="Paul McBurney", course_number="3240", subject="CS", catalog_number="123",
                               description="testd", course_section="testc", meetings="testm", component="test")
        response = self.client.get(reverse('SBfinder:class'), secure=True)
        course.save()
        courses = Course.objects.all()
        self.assertTrue(courses)
        self.assertEqual(response.status_code, 200)

    def test_incorrect_coursenumber(self):
        course2 = create_course(instructor="Paul McBurney", course_number="1110", subject="CS", catalog_number="123",
                                description="testd", course_section="testc", meetings="testm", component="test")
        response = self.client.get(reverse('SBfinder:class'), secure=True)
        course2.save()
        courses = Course.objects.all()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Class Number: CS 3240")
        self.assertContains(response, "Oops! We haven't found any classes that match your description :(")

    def correct_instructor(self):
        course = create_course(instructor="Paul McBurney", course_number="3240", subject="CS", catalog_number="123",
                               description="testd", course_section="testc", meetings="testm", component="test",
                               toggle=True, users="user")
        response = self.client.get(reverse('SBfinder:class'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instructor: Paul McBurney")

    # def test_CourseViews(self):
    #     course2 = create_course(instructor = "Paul McBurney", course_number = "1110", subject = "CS", catalog_number = "123",
    #     description = "testd", course_section = "testc", meetings = "testm", component = "test")
    #     response = self.client.get(reverse('SBfinder:class'), secure = True )
    #     course2.save()
    #     courses = Course.objects.all()
    #     self.assertTemplateUsed(response, 'SBfinder/class.html')


class GenerateSBList(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email='test@example.com')
        self.client = Client()
        self.user.save()
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        self.user1 = create_user_info(user_name='testuser', user_email='test@gmail.com',
                                      correspond_user=self.user, slug='slug')

    def test_GenerateSBListViews(self):
        course = create_course(instructor="Paul McBurney", course_number="3240", subject="CS", catalog_number="123",
                               description="testd", course_section="testc", meetings="testm", component="test")
        course.users.add(self.user1)
        response = self.client.get(reverse('SBfinder:generate_SB'), secure=True)
        self.assertTemplateUsed(response, 'SBfinder/SB_list.html')

    def test_empty_SBList(self):
        course = create_course(instructor="Paul McBurney", course_number="3240", subject="CS", catalog_number="123",
                               description="testd", course_section="testc", meetings="testm", component="test")
        course.users.add(self.user1)
        response = self.client.get(reverse('SBfinder:generate_SB'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We have found the following users who are in the same classes as you")
        self.assertNotContains(response, "Username")  # list doesn't contain any other users (empty)


def create_friend_request(from_user, to_user):
    return Friend_Request.objects.create(from_user=from_user, to_user=to_user)


class FriendRequest(TestCase):
    # 2 users
    # create 1 user from another
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email='test@example.com')
        self.client = Client()
        self.user.save()
        # self.client.login(username='test', password='12test12')
        # user = auth.get_user(self.client)

        self.user2 = get_user_model().objects.create_user(username='test2', password='12test12',
                                                          email='test@example.com')
        self.client = Client()
        self.user2.save()
        # self.client.login(username='test2', password='12test12')
        # user2 = auth.get_user(self.client)

        self.user3 = create_user_info(user_name='testuser', user_email='test@gmail.com',
                                      correspond_user=self.user, slug='slug')

        self.user4 = create_user_info(user_name='testuser2', user_email='test@gmail.com',
                                      correspond_user=self.user2, slug='slug')

    def test_friend_request_load(self):
        self.user3.friends.add(self.user4)
        self.user4.friends.add(self.user3)
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        response = self.client.get(reverse('SBfinder:friend_request'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Friend Requests")

    def test_friend_request_created(self):
        friendrequest = create_friend_request(self.user3, self.user4)
        friendrequest.save()
        friendrequests = Friend_Request.objects.all()
        self.user3.friends.add(self.user4)
        self.user4.friends.add(self.user3)
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        response = self.client.get(reverse('SBfinder:friend_request'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(friendrequests)

    def test_friend_request_views(self):
        self.user3.friends.add(self.user4)
        self.user4.friends.add(self.user3)
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        response = self.client.get(reverse('SBfinder:friend_request'), secure=True)
        self.assertTemplateUsed(response, 'SBfinder/friend_request.html')


def create_study_session(title, description, time, date, exact_time):
    return Study_Session.objects.create(title=title, description=description, time=time, date=date,
                                        exact_time=exact_time)


def create_study_session_request(study_session, to_user):
    return Study_Session_Request.objects.create(study_session=study_session, to_user=to_user)


class StudySession(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email='test@example.com')
        self.client = Client()
        self.user.save()

        self.user2 = get_user_model().objects.create_user(username='test2', password='12test12',
                                                          email='test@example.com')
        self.client = Client()
        self.user2.save()

        self.user3 = create_user_info(user_name='testuser', user_email='test@gmail.com',
                                      correspond_user=self.user, slug='slug')

        self.user4 = create_user_info(user_name='testuser2', user_email='test@gmail.com',
                                      correspond_user=self.user2, slug='slug')

    def test_request_load(self):
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        response = self.client.get(reverse('SBfinder:study_session'), secure=True)
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "Pending Study Session Proposal")

    def test_request_template(self):
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        response = self.client.get(reverse('SBfinder:study_session'), secure=True)
        self.assertTemplateUsed(response, 'SBfinder/study_session.html')

    def test_request_created(self):
        self.client.login(username='test', password='12test12')
        user = auth.get_user(self.client)
        self.user3.friends.add(self.user4)
        self.user4.friends.add(self.user3)
        studysess = create_study_session("request", "3240", "3:30", '2022-10-25 14:30:59', '2022-10-25 14:30:59')
        ssrequest = create_study_session_request(studysess, self.user4)
        ssrequest.save()
        ssrequests = Study_Session_Request.objects.all()
        response = self.client.get(reverse('SBfinder:study_session'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ssrequests)