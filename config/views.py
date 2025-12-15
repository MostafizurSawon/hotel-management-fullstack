from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

def home(request):
    # return redirect('index')
    return render(request, 'index.html')
