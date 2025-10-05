from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from main.models import School

# Create your models here.


User = get_user_model()


class Library(models.Model):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='library')
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    publication_date = models.DateField()
    isbn = models.CharField(max_length=20, unique=True)
    available_copies = models.IntegerField(default=1)

    def __str__(self):
        return self.title


class LibraryBook(models.Model):
    title_with_author = models.CharField(max_length=100)
    book = models.FileField(upload_to='library/catalogue/books')
    book_image = models.ImageField(
        upload_to='library/catalogue/images/', blank=True, null=True)
    available_copies = models.IntegerField(default=1)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    limit_choices_to={'role__in': ['teacher', 'admin', 'owner']}, related_name='books'
                                    ),

    class Meta:
        ordering = ['title_with_author']

    def __str__(self):
        return self.title_with_author
