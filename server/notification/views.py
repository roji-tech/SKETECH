# views.py
from django.shortcuts import render
from .models import Notification
from django.http import JsonResponse,HttpResponse
from django.core.serializers import serialize


def notification_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    data = serialize("json", notifications, fields=('title', 'message', 'timestamp'))
    print(data)
    return HttpResponse(data, content_type='application/json')
