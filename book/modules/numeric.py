from django.db.models import(
    Sum,
    Avg,
    Q,
    F,
)

from user.models import UserBook


def get_reading_numeric(book_id): 
    user_books = UserBook.objects.select_related('book').filter(book_id=book_id) # 1:n, 1:1, no need additional query(cuz caching)
    if not user_books.exists(): # 조회한 책이 존재하지 않으면 기본 값으로 돌려줍니다.
        return {
            'avg_finish'                        : 0.0,
            'expected_reading_minutes'          : 0, 
            'category_avg_finish'               : 0.0, 
            'category_expected_reading_minutes' : 0, 
        }
    # 완독 활률 = 책 완독한 독자 / 책 전체 독자 * 100(완독여부는 읽은 page/책 총 page)
    # 완독 예상 시간 = 책 완독자 총 reading time/ 책 완독자수
    total_users    = user_books.count()
    finished_users = user_books.filter(page__gte=F('book__page')) # 파이썬을 사용하지 않고 DB에 접근 가능, 쿼리의 수를 줄여준다, race condition을 피할 수 있다. 쓰레드 의 개념과 유사!


    avg_finish = 0.0
    avg_reading_minutes = 0.0

    if finished_users.exists():
        avg_finish = finished_users.count() / total_users * 100
        avg_reading_minutes = finished_users.aggregate(read_time=Avg('time'))['read_time']

    # [카테고리] 분야 평균 확률         = [카테고리] 책 완독자 수 / [카테고리] 책 총 구독자 수
    #[카테고리] 분야 평균 완독 예상시간 = [카테고리] 책 완독자 총 reading time / [카테고리] 책들 총 완독자 수

    categoory_id = user_books.first().book.category_id
    total_users = UserBook.objects.select_related('book').filter(book__category_id=category_id) 

    finished_users = total_users.filter(page__gte=F('book__page'))

    category_avg_finish = 0.0
    category_expected_reading_minutes = 0.0

    if finished_users.exists():
        category_avg_finish = finished_users.count()/total_users.count() * 100
        category_expected_reading_minutes = finished_users.aggregate(read_time=Avg('time'))['read_time'] # 집계함수의 반환값은 키워드인자의 키값과 오른쪽의 할당하는 값으로 딕셔너리를 반환함.

    return {
        'avg_finish'                        : avg_finish,
        'expected_reading_minutes'          : int(avg_reading_minutes),
        'category_avg_finish'               : category_avg_finish,
        'category_expected_reading_minutes' : int(category_expected_reading_minutes),
    }
