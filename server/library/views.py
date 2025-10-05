from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import View

from main.forms import LibraryBookForm
from main import mydecorators
from .models import Library, LibraryBook




def library_books_list(request):
    if request.method == "POST":
        form = LibraryBookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Book uploaded successfully.")
            return redirect('library:library_books_list')  # Redirect to avoid resubmission
    else:
        form = LibraryBookForm()

    library_books = LibraryBook.objects.all()
    return render(request, 'library.html', {
        'library_books': library_books,
        'form': form
    })




def update_library_book(request, pk):
    book = get_object_or_404(LibraryBook, pk=pk)
    if request.method == "POST":
        form = LibraryBookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated successfully.")
            return redirect('library:library_books_list')
    else:
        form = LibraryBookForm(instance=book)
    
    return render(request, 'library.html', {'form': form, 'book': book})



def delete_library_book(request, pk):
    book = get_object_or_404(LibraryBook, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book deleted successfully.")
        return redirect('library:library_books_list')
    return render(request, 'library.html', {'book': book})


def download_book(request, pk):
    book = get_object_or_404(LibraryBook, pk=pk)
    response = HttpResponse(book.book, content_type='application/octet-stream')
    response['content-disposition'] = f'attachment; filename="{book.book.name}"'
    return response



def show_total_books_in_catalogue(request):
    total_books = LibraryBook.objects.count()
    context = {
        'total_books' : total_books
    }

    return render(request, 'catalogue.html', context)