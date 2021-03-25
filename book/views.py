import json
import datetime
from datetime             import timedelta, date

from django.views       import View
from django.db          import transaction
from django.db.models   import Q, Count
from django.http        import JsonResponse

from .models            import  (
    Book,
    Category,
    Keyword,
    Today,
    Review,
    Like,
)

from library.models     import (
    Library,
    LibraryBook,
)
from .modules.numeric   import get_reading_numeric
from share.decorators   import check_auth_decorator

class RecentlyBookView(View):
    def get(self, request):
        day   = request.GET.get('day', '30')   
        limit = request.GET.get('limit', '10') # query parameter로 값을 가져오고 만약 value값이 없다면 기본 10개 던져줌

        today        = day.today()
        previous_day = today - timedelta(days=int(day)) # 오늘-과거 몇일 = 과거 어느 특정 시점

        books = [{
            "id"     : book.id,
            "title"  : book.title,
            "image"  : book.image_url,
            "author" : book.author,
        }for book in Book.objects.filter(publication_date__range=[previous_days, today])\
            .order_by('-publication_date')[:int(limit)]] # 내림차순으로 정렬하여 몇건을 보여줄지 limit으로 받은 변수로 가장 최근 데이터를 뿌려줌

        if not book:
            return JsonResponse({"message": "NO_BOOKS"}, status=400)
        return JsonResponse({'message':books}, status=200)


class SearchBookView(View):
    def get(self, request):
        conditions = {
            'author__icontains'   : request.GET.get('author', ''),
            'title__icontains'    : request.GET.get('title',''),
            'company__icontains'  : request.GET.get('company',''),
        }

        q = Q() # Q객체 연결하기 - https://bradmontgomery.net/blog/adding-q-objects-in-django/
                #               - https://velog.io/@kho5420/Django-ORM%EC%9C%BC%EB%A1%9C-Where%EC%A0%88%EC%97%90-or%EB%AC%B8-%EC%82%AC%EC%9A%A9%ED%95%98%EA%B8%B0-Q
        for key, value in conditions.items():
            if value:
                q.add(Q(**{key:value}), q.OR)
        if q:
            results = list(Book.objects.filter(q).values( # 
                            'id',
                            'author',
                            'title',
                            'image_url',
                            'company'
                            )
                        )
            return JsonResponse({'message':'SUCCESS', 'book':results}, status=200)
        return JsonResponse({'message':'INVALID_REQUEST'}, status=400)


class ReviewView(View):
    @check_auth_decorator # 글 작성 기능은 로그인 한 유저만 가능!
    def post(self, request, book_id):
        try:
            data = json.loads(request.body)
            user_id  = request.user
            contents = data['contents']

            if len(contents) < 200: # 199자까지 작성 가능
                review = Review.objects.create(
                    user_id =user_id,
                    book_id =book_id,
                    contents=contents
                )
                return JsonResponse({'message':'SUCCESS'}, status=200)
            return JsonResponse({'message':'CONTENTS_TOO_LONG'}, status=400)
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=200)

    @check_auth_decorator # 글 삭제는 작성자만 가능!
    def delete(self, request, book_id):
        try:
            review_id = request.GET('review_id')
            review    = Review.objects.get(id=review_id)
            if review.user_id == request.user: # 로그인 한 유저와 리뷰 작성자가 같은지 판단
                review.delete()
                return JsonResponse({'message':'SUCCESS'}, status=200)
            return JsonResponse({'message':'UNAUTHORIZED'}, status=403)
        except Review.DoesNotExist:
            return JsonResponse({'message':'REVIEW_NOT_EXIST'}, status=400)
    
    def get(self, request, book_id):
        try:
            results = [{
                'review_id'  : review.id,
                'nick_name'  : review.user.nickname,
                'user_img'   : review.user.image_url,
                'content'    : review.contents,
                'created_at' : review.created.strftime('%Y.%m.%d'),# The strftime() method returns a string representing date and time using date, time or datetime object.
            }for review in Book.objects.prefetch_related('review_set','review_set__user').filter(id=book_id)]
            return JsonResponse({'message':'SUCCESS'}, status=200)
        except Review.DoesNotExist:
            return JsonResponse({'message':'REVIEW_NOT_EXIST'}, status=400)