from django.urls import path

from .views import (
        SignInView,
        SignUpView,
        SMSCheckView,
        SignInWithKakaoView,
)

urlpatterns = [
        path('/sign_in',       SignInView.as_view()),
        path('/sign_up',       SignUpView.as_view()),
        path('/kakao_sign_in', SignInWithKakaoView.as_view()),
        path('/authSMS',       SMSCheckView.as_view()), # 네이버 클라우드 플랫폼을 통해 SMS 인증 진행
]