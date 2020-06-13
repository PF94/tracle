from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, PasswordResetForm, _unicode_ci_compare
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth import get_user_model, authenticate
from .models import Video, Channel

User = get_user_model()
class UserAdminCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'active', 'admin')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class SignupForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'placeholder' : 'E-MAIL'}))
    channel_name = forms.CharField(max_length=20, help_text='Required.', widget=forms.TextInput(attrs={'placeholder' : 'CHANNEL NAME'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder' : 'PASSWORD'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'placeholder' : 'CONFIRM PASSWORD'}))

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError("email is taken")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, request):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.save()
        channel = Channel.objects.create(name=self.cleaned_data.get('channel_name'), user=user)
        # Playlist.objects.create(title='History', channel=channel)
        return user

class SigninForm(forms.Form):
        
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'placeholder' : 'E-MAIL'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'type' : 'password', 'placeholder' : 'PASSWORD'}))

    class Meta:
        model = User
        fields = ('email', 'password')

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email is not None and password:
            user_cache = authenticate(username=email, password=password)
            if user_cache is None:
                raise forms.ValidationError('Invalid username or password.', code='invalid')
            if not user_cache.email_confirmed:
                raise forms.ValidationError('email address not confirmed, boi!')
        return self.cleaned_data

class ResetPasswordForm(PasswordResetForm):
    def get_users(self, email):
        email_field_name = User.get_email_field_name()
        active_users = User._default_manager.filter(**{
            '%s__iexact' % email_field_name: email
        })
        return (
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(email, getattr(u, email_field_name))
        )

class SetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder' : 'PASSWORD'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder' : 'CONFIRM PASSWORD'}),
    )

class ChangeUserForm(forms.Form):

    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'disabled' : True}))
    channel_name = forms.CharField()

    def save(self, instance):
        instance.name = self.cleaned_data['channel_name']
        instance.save()
        return instance

class ChangeAvatarForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ('avatar',)

class VideoDetailsForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'description', 'category', 'thumbnail')
