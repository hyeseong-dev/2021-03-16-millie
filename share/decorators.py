import json
import jwt
import my_settings

from django.http import JsonResponse

from user.models import User

def check_auth_decorator(func):
    def wrapper(self, request, *args, **kwargs):
        try:
            access_token = request.headers['Authorization']
            user_data = jwt.decode(
                access_token,
                my_settings.SECRET_KEY['secret'],
                algorithms=my_settings.JWT_ALGORITHM,
            )
            request.user = user_data['user_id']
            return  request.user = user_data['user_id']
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
        except jwt.exceptions.InvalidTokenError:
            return JsonResponse({'message':'INVALID_ACCESS_TOKEN'}, status=400)
    return wrapper