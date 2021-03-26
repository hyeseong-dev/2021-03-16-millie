import json, requests
from datetime           import date

from django.http        import JsonResponse
from django.views       import View
from django.db.models   import (
    Sum,
    Count,
    Max,
)

from .models            import (
    Library, 
    LibraryBook
)
from user.models        import (
    User,
    UserBook
)
from book.models        import Book
from share.decorators   import check_auth_decorator


class MyLibraryView(View):  # 내 서재 
    @check_auth_decorator
    def post(self,request):
        data = json.loads(request.body)
        try :
            user      = request.user
            book_id   = data['book_id']
            nickname  = User.objects.get(id=user).nickname
            library   = Library.objects.filter(user_id=user)

            if not library:
                library = Library.objects.create(
                    user_id = user,
                    name    = nickname
                )
                return JsonResponse({'message':'CREATED_LIBRARY'}, status=200)
            if LibraryBook.objects.filter(book_id=book_id, library_id=library.first().id).exists(): #  
                return JsonResponse({'message':'ALREADY_EXIST'}, status=400) # 책장 안에 이미 책이 존재하는 경우
            book_save  = LibraryBook.objects.create(
                book_id    = book_id,
                library_id = library.first().id
            )
            return JsonResponse({'bookSave':'SUCCESS'}, status=200)
        except KeyError:
            return JsonResponse({'message':'INVAILD_KEYS'}, status=400)


class LibraryBookListView(View):
    @check_auth_decorator
    def get(self, request):
        user_id = request.user
        ordering = int(request.GET.get('ordering',1))

        conditions = {
            1 : '-created_at',
            2 : 'book__title',
            3 : 'book__author',
            4 : 'book__publication_date',
        }

        books = LibraryBook.objects.select_related('book','library').filter( 
            library__user_id=user_id).order_by(conditions[ordering])
        
        results = [{
            'id'     : library.book.id,
            'title'  : library.book.title,
            'image'  : library.book.image_url,
            'author' : library.book.author,
        } for library in books ]
        return JsonResponse({'message':results}, status=200)


class StatisticsView(View):
    @check_auth_decorator
    def get(self, request):
        result = {}

        # 사용자의 총 독서권수, 총 독서시간
        userbook = UserBook.objects.select_related('user', 'book')\
                                    .filter(user_id=request.user)

        result['total_book_count'] = userbook.count() # 읽은 책 권수
        result['total_read_time']  = userbook.aggregate(total_read_time=Sum('time'))['total_read_time'] # 읽은 책 권수
                                                                                  # aggregate를 통해서 가상의 필드 생성
        # 추천 책 선정
        if not result['total_read_time']: # userbook  인스턴스에서 유저가 읽은 책의 시간이 없는 경우
            result['recommand_book'] = Book.objects.order_by('-publication_date')\
                                        .values('id', 
                                                'title', 
                                                'image_url', 
                                                'author')\
                                        .first()
        else: # userbook 인스턴스가 비어 있는 경우
            count_of_category = list(userbook.values(book__category_id)\
                                        .annotate(count=Count('book__category_id')))
            target = max(count_of_category, key=lambda x : x['count']) # 딕셔너리에서는 키를 이용하여 value의 max를 찾을때 사용, x의 count는 바로 윗줄 annotate에의해서 field가 생성된것                            
            category_id = target['book__category_id']

            books = Book.objects.filter(category_id=category_id).order_by('-publication_date')
            if books.exists():
                result['recommand_book'] = list(books.values('id', 'title', 'image_url', 'author')).first()
        return JsonResponse({"message":"SUCCESS", "data":result}, status=200)


class LibraryInfoView(View):
    @check_auth_decorator
    def get(self, request):
        user_id = request.user

        results=[{
            'libraryName' : library.name,
            'libraryImage': library.image_url,
            'userName'    : library.user.nickname,
            'userImage'   : library.user.image_url 
                                if library.user.image_url is not None
                                else '',
        } for library in Library.objects.select_related('user').filter(user_id=user_id) ]
        return JsonResponse({'message':results}, status=200)
