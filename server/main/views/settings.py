from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, render
from django.views import View


class SettingView(View):
    def get(self, request, *args, **kwargs):
        # Custom logic here
        return render(request, "settings/settings.html")
