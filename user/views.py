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

