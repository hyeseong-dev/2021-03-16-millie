import json
import bcrypt
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from .models import import (
    User, 
    SMSAuthRequest,
)
from .views import SMSCheckView


SIGNUP_URL       = reverse('user:sign_up') # create `user create` URL 
SIGNIN_URL       = reverse('user:sign_in') 
KAKAO_SIGNIN_URL = reverse('user:kakao_sign_in') 
AUTH_SMS_URL     = reverse('user:authSMS') 

class UserTest(TestCase):

    def setUp(self):
        client = Client() # 웹브라우저와 비슷한 기능 구현을 위해 클라이언트 객체를 생성

        SMSAuthRequest.objects.create(phone_number='01011112222')
        password = bcrypt.hashpw('12345678'.encode('utf-8'), bcrypt.gensalt())
        User.objects.create(phone_number='01011112222',
                            password=password.decode(),
                            nickname='test_user')
    
    def tearDown(self): # testDB 에 저장한 객체들 모두삭제
        User.objects.all().delete()             
        SMSAuthRequest.objects.all().delete()
    
    def test_user_signup_post_success(self): # 회원가입 성공 테스트
        body = {  # 바디에 3가지 키-벨류를 담아 보냄
            'phone_number' : '01012345678',
            'password'     : 'testpassword!@#1',
            'nickname'     : 'test_nickname',
        }

        response = self.client.post( # ㅔpost request객체 생성
            SIGNUP_URL,
            json.dumps(body), # json화 시켜서 보냄
            content_type = 'application/json'
        )

        self.assertEqual(response.status_code, 201) # ㅔpost 요청에 대한 성공은 201
        User.objects.last().delete()
    
    def test_user_signup_post_key_error(self):
        body = {
            'phone'        : '01012345678',            # 키를 다르게 했음, 의도적 키오류 발생
            'password'     : 'testpassword!@#1',
            'nickname'     : 'test_nickname',
        }

        response = self.client.post(
            SIGNUP_URL,
            json.dumps(body),
            content_type = 'application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'KEY_ERROR'})

    def test_user_signup_post_invalid_request_phone_number(self):
        body = {
            'phone_number' : '010-1213-7654', # 중간에 특수 문자가 삽입되어 유효하지 않음
            'password'     : 'testpassword!@#1',
            'nickname'     : 'test_nickname',
        }

        response = self.client.post(
            SIGNUP_URL,
            json.dumps(body),
            content_type = 'application/json',
        )

        selfassertEqual(response.status_code, 400)
        selfassertEqual(response.json(), {'mesasage':'INVALID_REQUEST'})
    
    def test_user_signup_post_invalid_request_password(self):
        body = {
            'phone_number' : '01012345678',   
            'password'     : 'tes', # 비밀번호를 짧게 작성하여 오류 발생 유발
            'nickname'     : 'test_nickname',
        }

        response = self.client.post(
            SIGNUP_URL,
            json.dumps(body),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'INVALID_REQUEST'})

    def test_user_signup_post_invalid_request_duplicate(self):
        User.objects.create(
            phone_number = '01012345678',
            password='testpassword!@#1',
            nickname='test_nickname'
        )
        body = {
            phone_number : '01012345678',
            password     : 'testpassword!@#1',
            nickname     : 'test_nickname'
        )

        response = self.client.post(
            SIGNUP_URL,
            json.dumps(body),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'INVALID_REQUEST'})
        User.objects.last().delete()

    def test_user_siginin_post_success(self):
        body = {
            'phone_number' : '01012345678',
            'password'     : '12345678',
        }

        response = self.client.post(
            SIGNIN_URL,
            json.dumps(body),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        

    def test_user_siginin_post_key_error(self):
        body = {
            'phone_number' : '01012345678',
            'pass'     : '12345678', # key error  유발
        }

        response = self.client.post(
            SIGNIN_URL,
            json.dumps(body),
            content_type = 'application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'KEY_ERROR'})

    def test_user_signin_post_user_not_exist(self):
        body = {
            'phone_number': '01012345678',
            'password'    : 'testpassword!@#1'
        }

        response = self.client.post(
            SIGNIN_URL,
            json.dumps(body),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'USER_NOT_EXIST'})
    

 
    def test_user_signin_post_invalid_password(self):
        body = {
            'phone_number': '01011112222',
            'password'    : '12345678'
        }

        response = self.client.post(
            SIGNIN_URL,
            json.dumps(body),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'USER_NOT_EXIST'})
           
    def test_user_sign_with_invalid_token(self):
        headers={'HTTP_Authorization':'invalidtoken!@#'}

        response = self.client.post(
            KAKAO_SIGNIN_URL,
            content_type='application/json',
            **headers   
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'INVALID_TOKEN'})
    
    def test_user_signin_with_key_error(self):
        headers={'HTTP_token':'invalidtoken!@#'}

        response = self.client.post(
            KAKAO_SIGNIN_URL,
            content_type='application/json',
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'KEY_ERROR'})

    @patch('user.views.requests')
    def test_user_sigin_with_kakao_success(self, mocked_request):
        class FakeResponse:
            def json(self):
                return {
                    'id'            : 12345,
                    'kakao_account' : {
                        'profile'  :  {
                            'nickname'           : 'test_nickname',
                            'thumbnail_image_url': 'image_url_info',
                            'email'              : 'test@example.com'
                            }
                    }
                }
        mocked_request.post = MagicMock(return_value=FakeResponse())

        headers = {'HTTP_Authorization' : 'fake_token.1234'}
        response = self.client.post(
                                KAKAO_SIGNIN_URL,
                                content_type='application/json',
                                **headers
                            )
        self.assertEqual(response.status_code, 200)

    def test_user_smscheck_get_success(self):
        sms_info = SMSAuthRequest.objects.get(phone_number='01012345678')
        response = self.client.get(AUTH_SMS_URL
                                    {'phone_number':'01012345678',
                                     'auth_number' : 'sms_info.auth_number',
                                    })
        self.assertEqual(response.json(), {'message':'SUCCESS', 'result':True})
        self.assertEqual(response.status_code, 200)