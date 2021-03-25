import json
import datetime
from datime             import timedelta, date

from django.views       import View
from django.db          import transaciton
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