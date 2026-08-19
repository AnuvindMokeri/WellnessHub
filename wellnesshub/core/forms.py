from django import forms
from django.contrib.auth.models import User

from .models import Product, Review, Complaint, Vendor, Profile


class CustomerSignupForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Full name'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Choose a username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'placeholder': '10-digit mobile number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Delivery address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('confirm_password'):
            if cleaned['password'] != cleaned['confirm_password']:
                raise forms.ValidationError('Passwords do not match.')
        return cleaned


class VendorSignupForm(forms.Form):
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Business / brand name'}))
    owner_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Owner full name'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Choose a username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'business@example.com'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'placeholder': '10-digit mobile number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Business address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('confirm_password'):
            if cleaned['password'] != cleaned['confirm_password']:
                raise forms.ValidationError('Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ProfileEditForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)


class VendorProfileEditForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['business_name', 'owner_name', 'email', 'phone', 'address']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} star{"s" if i != 1 else ""}') for i in range(5, 0, -1)]),
            'review': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your experience with this product...'}),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your issue...'}),
        }


class ReplyForm(forms.Form):
    reply = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a reply...'}))


class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    payment_method = forms.ChoiceField(choices=[
        ('Cash on Delivery', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('Card', 'Credit / Debit Card'),
    ])
