from django.urls import path
from . import views


app_name = 'library'

urlpatterns = [
  path('view/', views.library_books_list, name='library_books_list'),
  # path('add-book/', views.add_book_to_library, name='library_add_book'),
  path('change-book/<int:pk>/', views.update_library_book, name='change_library_book'),
  path('delete-book/<int:pk>/', views.delete_library_book, name='delete_library_book'),
  path('download/<int:pk>/', views.download_book, name='download_book'),
  path('total/', views.show_total_books_in_catalogue, name='total_books'),
]