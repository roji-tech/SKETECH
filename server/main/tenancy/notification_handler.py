from notification.models import Notification
from django.db.models.signals import post_save
from django.dispatch import receiver

# class Actions:
#     TEACHER_ADDED = "A new teacher has been added."
#     TEACHER_UPDATED = "Teacher details have been updated."
#     STUDENT_ADDED = "A new student has been added."
#     STUDENT_UPDATED = "Student details have been updated."
#     GMEET_CLASS_CREATED = "A new Google Meet class has been created."
#     GMEET_CLASS_UPDATED = "Google Meet class details have been updated."
#     NOTE_ADDED = "A new class note has been added."
#     NOTE_UPDATED = "Class note has been updated."
#     NOTE_DELETED = "Classnote has b"

#     '''LESSON PLAN NOTIFICATIONS'''
#     LESSON_PLAN_ADDED = "Class note has been updated."
#     LESSON_PLAN_UPDATED = "Class note has been updated."
#     LESSON_PLAN_DELETED = "Class note has been updated."

class NotificationManager:
  
  @staticmethod
  def create_notification(user, action, object_instance):
    # user = request.user
    title, message, icon = NotificationManager.get_notification_content(action, object_instance) 
    Notification.objects.create(user=user, title=title, message=message, icon=icon)

    post_save.connect(get_notification_content, sender=user)

    @staticmethod
    def get_notification_content(action, object_instance):
      if action == 'added':
        title = f"New {object_instance.__class__.__name__} added"
        message = f"{object_instance} has been added."
        icon = "add_circle"

      elif action == "updated":
        title = f"{object_instance.__class__.__name__} updated"
        message = f"{object_instance} has been updated."
        icon = "edit"

      elif action == "deleted":
        title = f"{object_instance.__class__.__name__} deleted"
        message = f"{object_instance} has been deleted."
        icon = "delete"

      else:
        title = f"{object_instance.__class__.__name__} action performed "
        message = f"{object_instance} has undergone {action}."
        icon = "info"

    return title, message, icon






