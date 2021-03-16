import json
import bcrypt
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from .models import import (
    User, 
    SMSAuthRequest,
)
from .views import SMSCheckView


class UserTest(TestCase):
    def setUp(self):
        client = Client()
        SMSAuthRequest.objects.create(phone_number='01011112222')
        password = bcrypt.hashpw('12345678'.encode('utf-8'), bcrypt.gensalt())
        User.objects.create(phone_number='01011112222',
                            password=password.decode(),
                            nickname='test_user')
    
    def tearDown(self):
        User.objects.all().delete()
        SMSAuthRequest.objects.all().delete()
    
    def test_user_signup_post_success(self):
        body = {
            'phone_number' : '01012345678',
            'password'     : 'testpassword!@#1',
            'nickname'     : 'test_nickname',
        }

        response = self.client.post(
            '/user/sign_up',
            json.dumps(body),
            content_type = 'application/json'
        )

        self.assertEqual(response.status_code, 201)
        User.objects.last().delete()
    
    def test_user_signup_post_key_error(self):
        body = {
            'phone' : '01012345678',            # 키를 다르게 했음
            'password'     : 'testpassword!@#1',
            'nickname'     : 'test_nickname',
        }

        response = self.client.post(
            '/user/sign_up',
            json.dumps(body),
            content_type = 'application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'KEY_ERROR'})