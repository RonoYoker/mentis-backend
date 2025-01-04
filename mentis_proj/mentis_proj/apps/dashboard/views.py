from django.template.loader import render_to_string
from django.shortcuts import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,logout,authenticate
from django.views.decorators.csrf import csrf_exempt


def main(request):
    rendered_page = render_to_string('mentis/base.html')
    return HttpResponse(rendered_page)

def manage_profile(request):
    rendered_page = render_to_string('mentis/manage_profile.html')
    return HttpResponse(rendered_page)



@csrf_exempt
def register(request):
    messages = []
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/dsh/main')
        else:
            messages = [x[0] for x in form.errors.values()]
    else:
        form = UserCreationForm()
    return render(request, "mentis/register.html", {"form": form,"messages":messages})


def login_view(request):
    messages = []
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/dsh/main/')  # Redirect to Django Admin or any other page
        else:
            messages.append('Invalid username or password.')
    return render(request, 'mentis/login.html',{"messages":messages})

def logout_view(request):
    logout(request)
    return redirect('/dsh/login/')