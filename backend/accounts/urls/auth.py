from django.urls import path
from accounts.views import auth

urlpatterns = [
    path('sign_up/', auth.sign_up, name='sign_up'),
    path('sign_in/', auth.sign_in, name='sign_in'),
    path('google_login/', auth.google_login, name='google_login'),
    path('send_passcode/', auth.send_passcode, name='send_passcode'),
    path('verify_passcode_and_reset_password/', auth.verify_passcode_and_reset_password, name='verify_passcode_reset'),
    path('update_password/', auth.update_password, name='update_password'),
    path('validate_token/', auth.validate_token, name='validate_token'),
]

from accounts.views.profile import me_profile  # noqa: E402

urlpatterns += [
    path('me/profile/', me_profile, name='me-profile'),
]
