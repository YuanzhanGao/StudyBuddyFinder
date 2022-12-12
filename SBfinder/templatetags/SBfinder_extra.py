from django import template
from ..models import UserInfo
from datetime import datetime
from django.utils import timezone
from ..models import Friend_Request, Message
import random

register = template.Library()


@register.filter
def IndexAccess(userKey, arg):
    return userKey[arg]


@register.filter
def rangeAccess2(userKey, arg):
    return userKey[:arg]


@register.filter
def getcurrentUser(userKey):
    return UserInfo.objects.get(correspond_user=userKey)


@register.filter
def checkAlreadyFriend(userKey, arg):
    current_user = UserInfo.objects.get(correspond_user=userKey)
    friend_idList = [friend.pk for friend in current_user.friends.all()]

    if int(arg) in friend_idList:
        return True
    else:
        return False


@register.filter
def checkFriendRequest(userKey, arg):
    current_user = UserInfo.objects.get(correspond_user=userKey)
    to_friend = UserInfo.objects.get(pk=arg)
    friend_request = Friend_Request.objects.filter(from_user=current_user, to_user=to_friend).first()
    if friend_request is not None:
        return True
    else:
        return False


@register.filter
def checkFriendRequest_fromFriend(userKey, arg):
    current_user = UserInfo.objects.get(correspond_user=userKey)
    to_friend = UserInfo.objects.get(pk=arg)
    friend_request = Friend_Request.objects.filter(from_user=to_friend, to_user=current_user).first()
    if friend_request is not None:
        return True
    else:
        return False


# This simple_tag is created because I cannot figure out how to pass the result of a filter (i.e. IndexAccess) to
# another filter (i.e. checkAlreadyFriend).I came in contact with the concept of "tag" after already creating "filter"
# functions here, and I am not sure what's the exact advantages and disadvantages of each. I decide not to remove
# the "IndexAccess" filter above because I don't want to modify existing codes that are supposedly already working
# and risk introducing unexpected problems. I might do it near the end of the project for optimization purposes, but
# I decide to stick with both the tag function below and the filter function above at this time even though they are
# doing effectively the same thing. (10/30/2022 -- Yuanzhan Gao)
@register.simple_tag
def accessLastElement(userName):
    userName_splitted = userName.split(",")

    return userName_splitted[-1]


@register.simple_tag
def instructorParse_Name(instructor):
    instructor = instructor.replace("{", "")
    instructor = instructor.replace("}", "")
    instructor_parsed = instructor.split(",")
    name_parsed = instructor_parsed[0].split(":")
    name = name_parsed[1].replace("'", "")
    return name


@register.simple_tag
def instructorParse_Email(instructor):
    instructor = instructor.replace("{", "")
    instructor = instructor.replace("}", "")
    instructor_parsed = instructor.split(",")

    email_parsed = instructor_parsed[1].split(":")
    email = email_parsed[1].replace("'", "")

    return email


@register.simple_tag
def passed_due_date(exact_time):
    if exact_time <= timezone.now():
        return True
    else:
        return False


@register.simple_tag
def check_SS_number(SS_set, current_user):
    has_Any = False
    for SS in SS_set:
        if SS.to_user == current_user:
            has_Any = True
            break

    return has_Any


@register.simple_tag
def get_current_user_tag(userKey):
    return UserInfo.objects.get(correspond_user=userKey)


@register.simple_tag
def recommend_random_friend(userKey):
    random_dic = {}
    current_user = UserInfo.objects.get(correspond_user=userKey)
    for user in UserInfo.objects.all():
        from_user_to_current = Friend_Request.objects.filter(from_user=user,
                                                             to_user=current_user).first()  # return None if not found, which is the ideal case
        from_current_to_user = Friend_Request.objects.filter(from_user=current_user,
                                                             to_user=user).first()  # return None if not found, which is the ideal case

        if (user.pk != current_user.pk) and (user not in current_user.friends.all()) and (
                from_user_to_current is None) and (
                from_current_to_user is None):  # don't want to recommend the current user as a friend to himself
            common_course = []
            for course in user.course_set.all():
                if course in current_user.course_set.all():
                    course_rep = str(course.subject) + " " + str(course.catalog_number)
                    common_course.append(course_rep)
            if len(common_course) > 0:  # since our database is small, as long as there is a commonly shared class, we recommend the user as a friend
                random_dic[user.user_name + "," + str(
                    user.pk)] = common_course  # very faulty algorithm, O(n) for big user base but suitable for this project; optimize later

    cap = 5

    if len(random_dic) <= cap:
        return random_dic
    else:
        result_dic = {}
        random_dic = random.sample(random_dic.items(), cap)  # break dictionary into a list of tuples
        for tuple in random_dic:
            result_dic[tuple[0]] = tuple[1]  # re-organize the dicionary

        return result_dic


@register.simple_tag
def get_user_by_id(id):
    return UserInfo.objects.get(pk=int(id))


@register.simple_tag
def count_message_number(other_user, current_user):
    counter = 0
    current_user = UserInfo.objects.get(correspond_user=current_user)
    for message in Message.objects.all():
        if (message.to_user == current_user and message.from_user == other_user) or (
                message.from_user == current_user and message.to_user == other_user):
            counter += 1

    return counter
