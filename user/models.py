import time
import hmac
import base64
import hashlib
import requests
import json
import datetime
from random             import randint

from django.db          import models
from django.utils       import timezone

from model_utils.models import TimeStampedModel

import my_settings


class User(TimeStampedModel):
    nickname        = models.CharField(max_length=45)
    password        = models.CharField(max_length=45, null=True)
    email           = models.EmailField(max_length=45, null=True)
    image_url       = models.URLField(max_length=200, null=True)
    phone_number    = models.CharField(max_length=11, null=True)
    kakao_id        = models.CharField(max_length=45, null=True)
    books           = models.ManyToManyField('book.Book', through=UserBook)

    class Meta: 
        db_table = 'users'

class UserBook(TimeStampedModel):
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    book       = models.ForeignKey('book.Book', on_delete=models.CASCADE)
    page       = models.IntegerField()
    time       = models.IntegerFiepage()

    class Meta:
        db_table = 'user_books'


class SMSAuthRequest(TimeStampedModel):
    """ 휴대폰 문자 인증 서비스"""
    phone_number = models.CharField(verbose_name='휴대폰 번호', primary_key=True, max_length=50)
    auth_number  = models.IntegerField(verbose_name='인증 번호')

    class Meta:
        db_table = 'user_books'

    def save(self, *args, **kwargs): # save 메서드 오버라이딩
        self.auth_number = rendint(100000, 1000000)
        super().save(*args, **kwargs)   # 오버라이딩 하기 위해서 super메서드를 가져와야함
        self.send_sms() # DB에 저장한 이후 바로 문자를 보내는 메서드를 호출합니다.
    
    def send_sms(self):                         # 네이버 클라우드 SMS API https://apidocs.ncloud.com/ko/ai-application-service/sens/sms_v2/
        url = 'https://sens.apigw.ntruss.com'
        uri = '/sms/v2/services/ncp:sms:kr:261818325710:python/message'
        api_url = url + uri

        body = {
            'type'          : 'SMS',
            'contentType'   : 'COMM',
            'from'          : '01011112222', # 등록된 발신번호
            'content'       : '[테스트] 인증 번호 [{}]를 입력해주세요.'.format(self.auth_number),
            'messages'      : [{'to'}: self.phone_number] 
        }

        timeStamp      = str(int(time.time() * 1000)) # time 모듈의 time() 함수는 현재 Unix timestamp을 소수로 리턴, 결과로 13자리 정수 형태의 문자열로 변환
        access_key     = "IOtPwtO8ScDz19bkE6va"
        string_to_sign = 'POST' + uri + '\n' + timeStamp + '\n' + access_key
        signature      = self.make_signature(string_to_sign)

        headers = {# 4개의 키값은 필수!
            'Content-Type'             : 'application/json; charset=UTF-8',
            'x-ncp-apigw-timestamp'    : timeStamp,  # 1970년 1월 1일 00:00:00 협정 세계시(UTC)부터의 경과 시간을 밀리초(Millisecond)로 나타낸 것이다. API Gateway 서버와 시간 차가 5분 이상 나는 경우 유효하지 않은 요청으로 간주
            'x-ncp-iam-access-key'     : access_key, # 포탈 또는 Sub Account에서 발급받은 Access Key ID
            'x-ncp-apigw-signature-v2' : signature
        }
        requests.post(api_url, data=json.dumps(body), headers=headers)

    def make_signature(self, string):  # send_sms메서드 내부에서 헬퍼 메서드로 사용됨
        # 네이버 클라우드 플랫폼에서 인증을 위해 필수로 넣어야함
        secret_key  = bytes(my_settings.SECRET_KEY, 'UTF-8')
        string      = bytes(string, 'UTF-8')
        string_hmac = hmac.new(secret_key, string, digestmod=hashlib.sha256).digest()
        # 간단히 HMAC을 설명하면, 송신자와 수신자만이 공유하고 있는 Key와 Message를 혼합하여 Hash 값을 만드는 것이다.
        #채널을 통해 보낸 메시지가 훼손되었는지 여부를 확인하는데 사용할 수 있다. MAC의 특성상 역산이 불가능 하므로, 수신된 메시지와 Hash 값을 다시 계산하여,계산된 HMAC과 전송된 HMAC이 일치하는지를 확인하는 방식이다


        string_base64 = base64.b64encode(string_hmac).decode('UTF-8') # ASCII 영역의 문자들로 이루어진 문자열로 바꾸는 인코딩 방식 - 인코딩된 문자열은 알파벳 대소문자와 숫자, "+","/" 기호등 64개로 이루어짐

        return string_base64 
    
    @classmethod                                 
    def check_auth_number(cls, phone_number, auth_number): # 문자보낸 인증번호 확인 메서드
        time_limit = timezone.now() - datetime.timedelta(minutes=5)
        result     = cls.objects.filter(phone_number = phone_number,
                                        auth_number = auth_number,
                                        modified__gte = time_limit, # 문자 인증시 5분간 주어지게 만들어지는 로직
                                    )
        return result.exists() # True or False 반환

        # hmac란?
        # 간단히 HMAC을 설명하면, 송신자와 수신자만이 공유하고 있는 Key와 Message를 혼합하여 Hash 값을 만드는 것이다.
        #채널을 통해 보낸 메시지가 훼손되었는지 여부를 확인하는데 사용할 수 있다. MAC의 특성상 역산이 불가능 하므로, 수신된 메시지와 Hash 값을 다시 계산하여,계산된 HMAC과 전송된 HMAC이 일치하는지를 확인하는 방식이다.

        # 네이버 클라우드 플랫폼 API 링크 참고 https://apidocs.ncloud.com/ko/common/ncpapi/
        #  네이버 블로그 - https://m.blog.naver.com/PostView.nhn?blogId=kimnr123&logNo=221681654984&proxyReferer=https:%2F%2Fwww.google.com%2F