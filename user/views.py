import jwt
import re
import bcrypt
import json
import requests
from datetime import datetime

from django.http      import JsonResponse
from django.db        import transaction
from django.views     import View
from django.shortcuts import redirect
from django.db.models import Q

from .models          import (
    User, 
    UserBook,
    SMSAuthRequest,
)

from library.models import(
    Library,
)

import my_settings


def generate_token(user_id):
    token = jwt.encode({'user_id':user_id},
        my_settings.SECRET_KEY,
        algorithm=my_settings.JWT_ALGORITHM
    ).decode('utf-8')
    return token

class SignUpView(View):
    '''회원 가입'''
    def check_password_pattern(self, password):
        check_password = re.compile(\
            '^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,}$')

        return check_password.match(password)

    def check_phone_number_pattern(self, phone_number):
        check_phone_number = re.compile('^[0-9]{11}$')
        return check_phone_number.match(phone_number)

    def proc_post(self, data):
        try:
            phone_number = data['phone_number']
            password     = data['password']
            nickname     = data['nickname']

            valid_phone_number = self.check_phone_number_pattern(phone_number)        
            valid_password     = self.check_phone_number_pattern(password)   
            
            if not valid_phone_number or not password : 
                return JsonResponse({'message':'INVALID_REQUEST'}, status=400)    

            if User.objects.filter(Q(phone_number=phone_number) | 
                                   Q(nickname=nickname)
                                ).exists():
                return JsonResponse({'message': 'INVALID_REQUEST'}, status=409) #  서버에 이미 중복된 리소스가 있을 경우 
            
            user = User.objects.create(
                    nickname     = nickname,
                    phone_number = phone_number,
                    password     = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()).decode()
                )

                
            if not Library.objects.filter(user_id=user.id).exists(): # 회원가입 시 -> 유저 개인 서재가 생성
                Library.objects.create(user_id=user.id, name=user.nickname)
            return JsonResponse({'message':'SUCCESS'}, status=201)
        except KeyError:
          return JsonResponse({'message':'KEY_ERROR'}, status=400)

    @transaction.atomic     # 유저객체와 라이브러리 객체 생성시 중간에 일부만 저장되면 아예 저장하기 전으로 빠꾸시킴. 원자성!
    def post(self, request):
        data = json.loads(request.body) # 회원가입시 유저 개인정보가 body에 담겨저 data변수에 전달됩니다. 
        return self.proc_post(data)


class SignInView(View):
    def post(self, request):
        try:
            data         = json.loads(request.body)
            phone_number = data['phone_number']
            password     = data['password']

            user = User.objects.filter(phone_number=phone_number).first() # 우선 가볍게 휴대폰이 있는지부터 확인하고 입뺀넣음

            if not user.exists(): # 디비에 찾고 있는 유저 휴대폰이 있는지 확인함.
                return JsonResponse({'message':'USER_DOES_NOT_EXIST'}, status=400)

            if not bcrypt.checkpw(password.encode('utf-8'),       # request로 받은 비번암호와
                                  user.password.encode('utf-8')): # db에서 가져온 인스턴스의 비밀번호 암호를 서로 바이트로 변환하여 비교
                return JsonResponse({'message':'USER_DOES_NOT_EXIST'}, status=400)

            access_token = generate_token(user.id)
            return JsonResponse({'message':'SUCCESS',
                                'access_token':access_token},
                                 status=200) # 201이 아닌 이유는 해당 토큰을 DB에서 만들어 저장하지 않기 때문임
        except KeyError:
            return JsonResponse({"message":"KEY_ERROR"}, status=400)


class SignInWithKakaoView(View):
    @transaction.atomic         # 카카오톡 처음 로그인 유무에 따라 User, Library 클래스의 인스턴스가 DB에서 생성될지 아닐지 판단하고 이를 한방에 저장하거나 혹은 삑사리 나면 모두 롤백시키듯이 취소해버림
    def post(self, request):
        try:
            access_token = request.headers['Authorization'] #header에서 token값을 가져옴
            profile      = request.post(
                            'https://kapi.kakao.com/v2/user/me',
                            headers = {'Authorization':f'Bearer {access_token}'},
                            data='property_keys=["kakao_account.email"]' # 카카오계정의 이메일 소유 여부 |이메일 값, 이메일 인증 여부, 이메일 유효 여부
                            )
            # kakao API 링크 참고 : https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#req-user-info
            profile = profile.json() # json -> python 객체로 변환
            kakao_id = profile.get('id',None)

            if not kakao_id: # 토큰이 올바르지 않으면 None을 반환하겠조?
                return JsonResponse({'message':'INVALID_TOKEN'}, status=400)
            
            kakao_account = profile.get('kakao_account')
            nickname      = kakao_account['profile'].get('nickname', '')            # 카톡에 닉네임|이미지|이메일등이 없을 경우 db에 빈문자열로 저장하게함
            thumbnail     = kakao_account['profile'].get('thumbnail_image_url', '')
            email         = kakao_account.get('email','')
            obj, created  = User.objects.update_or_create(      # update_or_create(조건, 기본값), 여기서 get_or_create를 사용하지 않은 것은 카톡의 변경된 정보를 우리 디비에도 그대로 반영해서 변경하려는 의도임
                                                            email = email,                  # 조건이 있으면 해당 인자만 바꾸고 없으면 2번째 인자인 default키워드 인자를 기준으로 모두 db에 데이터를 새롭게 생성함
                                                            defaults = {                    # 반환된 첫번째 obj는 인스턴스이며 db에 새롭게 만들었으면 True, update만 했으면 False가 create 변수에 할당됨
                                                                'kakao_id'  : str(kakao_id), # 즉, created가 True인 경우는 처음 사이트에 kakao로 로그인 시도를 한 유저의 경우 created가 True로 진행됨
                                                                'nickname'  : nickname,
                                                                'image_url' : thumbnail,
                                                                'modified'  : datetime.now(), # 로그인 할 때 마다 매변 변경됨
                                                                'email'     : email,
                                                            }
                                                        )
            user = None
            if obj : 
                user = obj # update_or_create로 반환 받은 인스턴스를 user에 할당
            elif created:  # 처음 웹사이트 방문한 경우 True가 되겠조. 
                user = created
            access_token = generate_token(user.id)

            # 처음 로그인한 경우이거나 회원가입한 경우라면 User클래스의 인스턴스가 db에 생성되면 바로~! Library를 만들어준다. 
            if not Library.objects.filter(user__kakao_id=str(kakao.id)): # 현재 카톡에서 넘겨주는 id는 int이지만 추후 str으로 바뀔 변동성을 생각하여 애초에 모델에서 컬럼 타입을 문자로 잡아 언제든 유용하게 대응할수 있도록함.
                Library.objects.create(user_id=user.id, name=user.nickname, image_url='')
            return JsonResponse({'message':'SUCCESS', 'access_token':access_token}, status=200)
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)


class SMSCheckView(View): 
    @transaction.atomic
    def post(self, requst):
        try:
            data = json.loads(request.body)
            phone_number = data['phone_number']
            SMSAuthRequest.objects.update_or_create(phone_number=phone_number) # 휴대폰호 입력후 DB와 확인후  
            return JsonResponse({'message':'SUCCESS'}, status=200)
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
    
    def get(self, request):
        try:
            phone_number = request.GET.get('phone_number','')
            auth_number = request.GET.get('auth_number', 0)
            result = SMSAuthRequest.check_auth_number(phone_number, auth_number) # 입력한 휴대폰 번호와 인증번호를 근거로 DB에서 조회하여 True or False반환
            return JsonResponse({'message':'SUCCESS', 'result':result}, status=200)
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)