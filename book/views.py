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


class TodayBookView(View):
    def get(self, request):
        today      = date.today().strftime('%Y-%m-%d')
        today_book = Book.objects.prefetch_related(
            'review_set', 'review_set__like_set').filter(today__pick_date=today) # 오늘 날짜에 해당하는 책들 가져오기!
                                                                                 # Book Review, Like테이블 inner join!
        
        if today_book.exists():
            return JsonResponse({'message':'NO_BOOK'}, status=400)
        
        today_review = today_book.first().review_set.prefetch_related('like_set').\
                                                    values('user__nickname',          
                                                            'user__image_url',
                                                            'contents').\
                                                    annotate(count=Count('likes')).\
                                                    order_by('-count')[:1].first()     # join을 통해 컬럼들이 너무 많이 있기에 values()를 통해 사용할 것들만 명시함
                                                                                        # 반환되는 값은 딕셔너리 객체
        book = [{
            'id'            : book.id, 
            'title'         : book.title,
            'image'         : book.image_url,
            'author'        : book.author,
            'description'   : book.today_set.get(book_id=book).description,
            'reviewerName'  : today_review.get('user__nickname'), 
            'reviewerImage' : today_review.get('user__image_url')
                if today_review.get('user__image_url') is not None
                else '',
            'reviewContent' : today_review.get('contents')
        } for book in today_book]
        return JsonResponse({'todayBook':book}, status=200)


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
            return JsonResponse({'message':'SUCCESS', 
                                 'book':results}, status=200)
        return JsonResponse({'message':'INVALID_REQUEST'}, status=400)


class RecommendBookView(View):
    def get(self, request):
        keyword_id = int(request.GET.get('keyword', '2'))
        limit      = int(request.GET.get('limit', '6'))

        # isocalendar() 참고 링크 - https://devanix.tistory.com/306
        today_iso = datime.datetime.now().isocalendar() # (2021.03,26) 국제 표준에 맞는 달력 표현, 튜플로 반환
        year = today_iso[0] # iso year # 일반적 년도 표현
        week = today_iso[1] # iso week number  # 올해 몇번째 주차인지 표현 (예. 13주차 3월 21일~27일에 해당)
        day  = today_iso[2] # iso weekday # 예를들어 6이 표현되면 토요일에 해당

        week_start = date.fromisocalendar(year, week, 1) # 예. fromisocalendar(2011,22,1) 2011년 22주의 월요일 -> 2011년5월30일 월요일
        now        = datetime.datetime.now()

        books = LibraryBook.objects.prefetch_related('book').\
            filter(created_at__range=[week_start, now], book_keyword_id=keyword_id).\
            values('book_id', 'book__title', 'book__image_url', 'book__author').\
            annotate(count=Count('book_id')).\
            order_by('-count')[:limit]

        results = [{'id'    : book.get('book_id'),
                    'title' : book.get('book__title'),
                    'image' : book.get('book__image_url'),
                    'author': book.get('book__author'),
        } for book in books ]

        if not results:
            return JsonResponse({'message': 'NO_BOOKS'}, status=400)
        return JsonResponse({'message': results}, status=200)


class BookDetailView(View): 
    def get(self, request, book_id):
        try:
            data = get_reading_numeric(book_id) # 책, 카테고리별 완독 시간, 완독률 데이터 가져오기
            book = Book.objects.select_related('category').\
                                prefetch_related('review_set').get(id=book_id)
            results = {
                'title'            : book.title,
                'subtitle'         : book.subtitle,
                'image_url'        : book.image_url,
                'company'          : book.company,
                'author'           : book.author,
                'contents'         : book.contents,
                'company_review'   : book.company_review,
                'page'             : book.page,
                'publication_date' : book.publication_date,
                'description'      : book.description,
                'category'         : book.category.name,
                'review_count'     : book.review_set.count(),
                'reader'            : book.userbook_set.count(),
                'numeric'          : data,
            }
            return JsonResponse({'book_detail':results}, status=200)
        except Book.DoesNotExist:
            return JsonResponse({'message':'NOT_EXIST_BOOK'}, status=400)


class CommingSoonBookView(View):
    def get(self, request):
        day   = int(request.GET.get('day', 30))
        limit = int(request.GET.get('limit', 10))

        today = date.today()
        next_publication = today + timedelta(days=day)
        min_day          = today + timedelta(days=1)
        max_day          = today + timedelta(days=5)

        results = [{
            'id'     : book.id,
            'title'  : book.title,
            'image'  : book.image_url,
            'author' : book.author,
            'date'   : (book.publication_date-today).days # datetime 객체의 days 속성. 삼항연산자!
                        if min_day <= book.publication_date <= max_day
                        else book.publication_date.strftime('%m월%d')
        }for book in Book.objects.filter(
            publication_date__range=[min_day, next_publication]).\
            order_by('publication_date')[:limit] ]

        if not results:
            return JsonResponse({"message":"NO_BOOKS"}, status=400)
        return JsonResponse({"commingSoonBook":results}, status=200)


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
            return JsonResponse({'message':'KEY_ERROR'}, status=400)

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
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)    

    def get(self, request, book_id):
        try:
            results = [{
                'review_id'  : review.id,
                'nick_name'  : review.user.nickname,
                'user_img'   : review.user.image_url,
                'content'    : review.contents,
                'created_at' : review.created.strftime('%Y.%m.%d'),# The strftime() method returns a string representing date and time using date, time or datetime object.
            }for review in Book.objects.prefetch_related(
                                'review_set',
                                'review_set__user').get(id=book_id)]
            return JsonResponse({'message':'SUCCESS'}, status=200)
        except Review.DoesNotExist:
            return JsonResponse({'message':'REVIEW_NOT_EXIST'}, status=400)
        

class ReviewLikeView(View):
    @check_auth_decorator
    def patch(self, request):
        try:
            data = json.loads(request.body)
            user_id   = request.user
            review_id = data['review_id']

            if Review.objects.filter(id=review_id).exists():
                like, created = Like.objects.get_or_create(user_id=user_id, 
                                                        review_id=review_id)
                if created: 
                    return JsonResponse({'message':'SUCCESS'}, status=200)
                like.delete()
                return JsonResponse({'message':'CANCEL', 'like':False}, status=200)  
            return JsonResponse({'message':'NOT_EXIST_REVIEW'}, status=400)
        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
    

class BestSellerBookView(View):
    def get(self, request):
        keyword_id = int(request.GET.get('kewyord','1')) # 여기서 키워드란 1: 종합, 2: 고양이, 3: 사랑, etc
        limit      = int(request.GET.get('limit', '10'))

        if keyword_id in range(2,7):
            books = UserBook.objects.select_related('book').filter(
                        book__keyword_id=keyword_id).annotate( # count라는 필드 or 컬럼을 추가하는 부분
                        count=Count('book_id')).order_by('-count')[:int(limit)]
            if not books.exists():
                return JsonResponse({'message':'NO_BOOKS'}, status=400)
        
        else:
            books = UserBook.objects.select_related('book').filter(
                book__keyword_id__gte=2).annotate(
                count=Count('book_id')).order_by('-count')[:limit]
            if not books.exists():
                return JsonResponse({'message':'NO_BOOKS'}, status=400)
        
        results = [{
            'id'     : book.book.id,
            'title'  : book.book.title,
            'image'  : book.book.image_url,
            'author' : book.book.author,
        }for book in books]
        return JsonResponse({'bestSellerBook':results}, status=200)


class LandingPageView(View): # 랜딩페이지 - 링크 http://blog.wishket.com/%EB%9E%9C%EB%94%A9%ED%8E%98%EC%9D%B4%EC%A7%80-%EA%B0%9C%EB%85%90-%EC%A0%9C%EC%9E%91-%ED%8C%81-%EC%9C%84%EC%8B%9C%EC%BC%93/#:~:text=%EB%9E%9C%EB%94%A9%ED%8E%98%EC%9D%B4%EC%A7%80%EB%8A%94%20%EC%98%A8%EB%9D%BC%EC%9D%B8%20%EB%A7%88%EC%BC%80%ED%8C%85,%ED%8E%98%EC%9D%B4%EC%A7%80%EB%A5%BC%20%EC%82%AC%EC%9A%A9%ED%95%A0%20%EC%88%98%20%EC%9E%88%EC%A7%80%EC%9A%94.
    def get(self, request):
        max_cnt = int(request.GET.get('maximum', 60))

        result = [ {'id'        : book.id,
                    'image_url' : book.image_url,
        } for book in Book.objects.exclude(image_url='')[:max_cnt] ]
        return JsonResponse({"message":"SUCCESS", "books":result}, status=200)