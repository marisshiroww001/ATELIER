from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import CustomerRegistrationForm, CustomerProfileForm
from .login_forms import CustomerLoginForm
from django.contrib.auth.decorators import login_required

def register(request):

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')

    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {
        'form': form
    })


def customer_login(request):

    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(
                request,
                username=email,
                password=password
            )

            if user is not None:
                login(request, user)
                return redirect('home')

            form.add_error(
                None,
                'Incorrect email address or password.'
            )

    else:
        form = CustomerLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form
    })


def customer_logout(request):
    logout(request)
    return redirect('home')
@login_required
@login_required
def customer_profile(request):

    if request.method == 'POST':
        form = CustomerProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('accounts:profile')

    else:
        form = CustomerProfileForm(instance=request.user)

    return render(
        request,
        'accounts/profile.html',
        {'form': form}
    )