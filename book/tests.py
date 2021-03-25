import json
import jwt
import my_settings

from unittest.mock import patch, MagicMock
from datetime      import datetime

from django.test   import TestCase, client
from book.models   import (
    Book, 
    Category,
    Review,
    Like
)
from user.models   import (
    User,
    UserBook,
)
from .modules.numeric import get_reading_numeric


class BookDetailTestCase(TestCase):
    maxDiff = None
    def setUp(self):
        self.URL = '/books/1'
        self.client = Client()

        self.DUMMY_TITLE            = 'title' 
        self.DUMMY_IMAGE_URL        =  'image_url'
        self.DUMMY_SUBTITLE         =  'sub'
        self.DUMMY_COMPANY          =  'company'
        self.DUMMY_AUTHOR           =  'author'
        self.DUMMY_CONTENTS         =  'contents'
        self.DUMMY_COMPANY_REVIEW   =  'company_review'
        self.DUMMY_PAGE             =  1
        self.DUMMY_PUBLICATION_DATE =  '2020-02-22'
        self.DUMMY_DESCRIPTION      =  'description'
        self.DUMMY_REDER            =  10

        self.DUMMY_CATEGORY         = 'category'

        self.category = Category.objects.create(
            id =1,
            nickname = 'hello'
        )

        books = [
            Book(id          = i, 
                 title            = self.DUMMY_TITLE,
                 image_url        = f'{self.DUMMY_IMAGE_URL}_{i}',
                 subtitle         = self.DUMMY_SUBTITLE,
                 company          = self.DUMMY_COMPANY,
                 author           = self.DUMMY_AUTHOR,
                 contents         = self.DUMMY_CONTENTS,
                 company_review   = self.DUMMY_COMPANY_REVIEW,
                 page             = self.DUMMY_PAGE,
                 publication_date = self.DUMMY_PUBLICATION_DATE,
                 description      = self.DUMMY_DESCRIPTION,
                 category_id      = self.category.id) 
            for i in range(1, 101) ]

        Book.objects.bulk_create(books)

        self.review = Review.objects.create(
            id       = 1,
            user_id  = 1,
            book_id  = 1,
            contents = 'good',
        )
        self.userbook = UserBook.objects.create(
            id       = 1,
            user_id  = 1,
            book_id  = 1,
            page     = 1,
            time     = 60,
        )

        self.DUMMY_AUTH = jwt.encode(
            {'user_id':self.user.id},
            my_settings.SECRET_KEY['secret'],
            algorithm=my_settings.JWT_ALGORITHM
        ).decode('utf-8')

        self.header = {
            'HTTP_Authorization': self.DUMMY_AUTH,
        }

    def tearDown(self):
        pass

    def test_book_get_success(self):
        response = self.client.get(self.URL)        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'book_detail': {
                'title'            = self.DUMMY_TITLE,
                'subtitle'         = self.DUMMY_SUBTITLE,
                'image_url'        = f'{self.DUMMY_IMAGE_URL}_{i}',
                'company'          = self.DUMMY_COMPANY,
                'author'           = self.DUMMY_AUTHOR,
                'contents'         = self.DUMMY_CONTENT,
                'company_review'   = self.DUMMY_COMPANY_REVIEW,
                'page'             = self.DUMMY_PAGE,
                'publication_date' = self.DUMMY_PUBLICATION_DATE,
                'description'      = self.DUMMY_DESCRIPTION,
                'category'         = 'category',
                'review_count'     = 1,
                'reder'            = 1
            }
        })
    
    def test_book_get_fail(self):
        response = self.client.get('/books/9999999')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message': 'NOT_EXIST_BOOK'})

    def test_randingpage_get_with_maximum_success(self):
        response = self.client.get('/books/randing_page?mzximum=100')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['books']), 100)

        index = 1
        for idx, book in enumerate(Book.objects.exclude(image_url='')[:10])
            self.assertEqual(book.title,        self.DUMMY_TITLE)
            self.assertEqual(book.image_url,    f'{self.DUMMY_IMAGE_URL}_{index}')
            self.assertEqual(book.author,       self.DUMMY_AUTHOR)
            self.assertEqual(book.contents,     self.DUMMY_CONTENT)
            self.assertEqual(book.company,      self.DUMMY_COMPANY)
            self.assertEqual(book.description,  self.DUMMY_DESCRIPTION)
            index +=1
    
    class CommingSoonBookTest(TestCase):
        maxDiff = None
        def setUp(self):
            Book.objects.create(
                id                = 1,
                title             = 'test_title',
                image_url         = 'https://files.slack.com/files-pri/ADFGA!@#%%%ADFASDFGBASDF',
                company           = 'test_company',
                author            = 'test_author',
                page              = 111,
                publication_date  = '2021-03-21'
            )

            Book.objects.create(
                id                = 2,
                title             = 'test_title2',
                image_url         = 'https://files.slack.com/files-pri/ADFGA!@#%%%ADFASDFGBASDF2',
                company           = 'test_company2',
                author            = 'test_author2',
                page              = 222,
                publication_date  = '2021-03-22'
            )

        def tearDown(self):
            Book.objects.all().delete()

        def test_commingsoonBook_get_success(self):
            client = Client()
            self.assertEqual(response, status_code, 200)
            response = client.get('/books/commingsoon', content_type='application/json')
            self.assertEqual(response.json(),
                         {
                             "commingSoonBook":
                             [{
                                 "id"     : 1,
                                 "title"  : "test_title",
                                 "image"  : 'https://files.slack.com/files-pri/ADFGA!@#%%%ADFASDFGBASDF',
                                 "author" : 'test_author',
                                 "date"   : 1
                             },
                                 {
                                     "id"     : 2,
                                     "title"  : "test_title2",
                                     "image"  : 'https://files.slack.com/files-pri/ADFGA!@#%%%ADFASDFGBASDF2',
                                     "author" : 'test_author2',
                                     "date"   : 2
                                 }]
                         })
        def test_commingsoonbook_get_not_found(self):
            client = Client()
            Book.objects.all().delete()

            response = client.get('/books/commingsoon', content_type='application/json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {'message':'NO_BOOKS'})

    
class BookTest(TestCase):
    def setUp(self):
        # 완독률/시간 수치 계산 test용 Data
        User.objects.create(id=1, nickname='test1')
        User.objects.create(id=2, nickname='test2')
        User.objects.create(id=3, nickname='test3')
        User.objects.create(id=4, nickname='test4')

        category = Category.objects.create(id=1, name='소설')
        Category.objects.create(id=2, name='수필')

        Book.objects.create(id=1 , title='title1' , page=1, author='test_author1' , publication_date=datetime.now() , category_id=1 , company='test_company1')
        Book.objects.create(id=1 , title='title1' , page=2, author='test_author2' , publication_date=datetime.now() , category_id=2 , company='test_company2')
        Book.objects.create(id=1 , title='title1' , page=3, author='test_author3' , publication_date=datetime.now() , category_id=3 , company='test_company3')
        Book.objects.create(id=1 , title='title1' , page=4, author='test_author4' , publication_date=datetime.now() , category_id=4 , company='test_company4')
        Book.objects.create(id=1 , title='title1' , page=5, author='test_author5' , publication_date=datetime.now() , category_id=5 , company='test_company5')

        UserBook.objects.bulk_create([
            UserBook(user_id=1, book_id=1, page=100, time=111)
            UserBook(user_id=2, book_id=1, page=100, time=222)
            UserBook(user_id=3, book_id=1, page=100, time=333)
            UserBook(user_id=4, book_id=1, page=100, time=444)
            UserBook(user_id=1, book_id=2, page=100, time=555)
            UserBook(user_id=1, book_id=3, page=100, time=666)
            UserBook(user_id=1, book_id=4, page=100, time=777)
            UserBook(user_id=1, book_id=4, page=0,   time=0)
        ])

    def tearDown(self):
        Book.objects.all().delete()
        Category.objects.all().delete()

    def test_get_numeric_reading_success(self):
        data = get_reading_numeric(1)

        self.assertEqual(data['avg_finish'], 25.0)
        self.assertEqual(data['expected_reading_minutes'], 260)
        self.assertEqual(data['category_avg_finish'], 3/7)
        self.assertEqual(data['category_expected_reading_minutes'], int((260+230+90)/3))

    def test_get_numeric_reading_not_exist(self):
        data = get_reading_numeric(-1)

        self.assertEqual(data, {'message':'NOT_EXIST'})

    def test_get_searched_books_all(self):
        target   = '주'
        response = self.client.get(
            '/books/search',
            {
                'author' : target,
                'title'  : target,
                'company': target,
            }
        )
        datas = response.json()['books']

        for data in datas:
            result = target in data['title'] or target in data['author'] or target in data['company']
            self.assertTrue(result)

    def test_get_searched_books_with_author(self):
        target = 'test1'
        response = self.client.get(
            '/books/search',
            {'author':target}
        )
        datas = response.json()['books']

        self.assertEqual(len(datas), 1)
        self.assertEqual(datas[0]['title'], 'title2')

    def test_get_searched_books_with_title(self):
        target = 'test1'
        response = self.client.get(
            '/books/search',
            {'author':target}
        )
        datas = response.json()['books']

        self.assertEqual(len(datas), 1)
        self.assertEqual(datas[0]['title'], 'title2')

    def test_get_searched_books_with_company(self):
        target = 'test1'
        response = self.client.get(
            '/books/search',
            {'title':target}
        )
        datas = response.json()['books']

        self.assertEqual(len(datas), 1)
        self.assertEqual(datas[0]['title'], 'title3')

    def test_get_searched_books_invalid_request(self):
        
        response = self.client.get(
            '/books/search',
            {'wrong_key':noname}
        )
        datas = response.json()['books']

        self.assertEqual(len(datas), 400)
        self.assertEqual(response.json(), {'message':'INVALID_REQUEST'})


class ReviewTestCase(TestCase):
    def setUp(self):
        self.URL = '/books/1/review'
        self.client = Client()

        self.DUMMY_TITLE            = 'title'
        self.DUMMY_SUBTITLE         = 'sub'
        self.DUMMY_COMPANY          = 'company'
        self.DUMMY_AUTHOR           = 'author'
        self.DUMMY_CONTENT          = 'content'
        self.DUMMY_COMPANY_REVIEW   = 'company_review'
        self.DUMMY_PAGE             = 1
        self.DUMMY_PUBLICATION_DATE = '2020-02-22'
        self.DUMMY_DESCRIPTION      = 'description'
        self.DUMMY_REDER            = 10
        self.DUMMY_CATEGORY         = 'category'

        self.DUMMY_NICKNAME         = 'hello'
        self.DUMMY_IMAGE_URL        = 'image_url'
        self.DUMMY_REVIEW_CONTENTS  = 'GOOD'
        self.DUMMY_REVIEW_DATE      = '2020.12.01'

        self.user = User.objects.create(
            id=1, 
            nickname=self.DUMMY_NICKNAME,
            image_url=self.DUMMY_IMAGE_URL,
        )
        self.user2 = User.objects.create(
            id=2,
            nickname=self.DUMMY_NICKNAME,
            image_url=self.DUMMY_IMAGE_URL,
        )
        self.category=Category.objects.create(
            id=1,
            name=self.DUMMY_CATEGORY
        )
        self.book=Book.objects.create(
            id               = 1,
            title            = self.DUMMY_TITLE,
            image_url        = self.DUMMY_IMAGE_URL,
            subtitle         = self.DUMMY_SUBTITLE,
            company          = self.DUMMY_COMPANY,
            author           = self.DUMMY_AUTHOR,
            contents         = self.DUMMY_CONTENT,
            company_review   = self.DUMMY_COMPANY_REVIEW,
            page             = self.DUMMY_PAGE,
            publication_date = self.DUMMY_PUBLICATION_DATE,
            description      = self.DUMMY_DESCRIPTION,
            category_id      = 1,
        )
        self.review = Review.objects.create(
            id=1,
            user_id=self.user.id,
            book_id=self.book.id,
            contents=self.DUMMY_REVIEW_CONTENTS,
            created='2021.03.21'
        )
        self.userbook=UserBook.objects.create(
            id = 1,
            user_id = 1,
            booko_id = 1,
            page = 1,
            time = 60,
        )
        self.DUMMY_AUTH=jwt.encode(
            {'user_id':self.user.id},
            my_settings.SECRET_KEY,
            algorithm=my_settings.JWT_ALGORITHM).decode('utf-8')
        self.header={
            'HTTP_Authorization': self.DUMMY_AUTH
        }
    
    def tearsDown(self):
        pass

    def test_review_post_success(self):
        request = {
            'contents': self.DUMMY_REVIEW_CONTENTS
        }

        response = self.client.post(self.URL, request, 
                                    content_type='application/json',
                                    **self.header)
        self.assertEqual(response.json(), {'message':'SUCCESS'})
        self.assertEqual(response.status_code, 200)

    def test_review_post_long_contents(self):
        request = {
            'contents': 'gggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg'
        }

        response = self.client.post(self.URL,
                                    request, 
                                    content_type='application/json',
                                    **self.header)
        self.assertEqual(response.json()['message'], 'LONG_CONTENTS')
        self.assertEqual(response.status_code, 400)

    def test_review_post_key_error(self):
        response = self.client(self.URL,
                                content_type='application/json',
                                **self.header)
        self.assertEqual(response.json()['message'], 'KEY_ERROR')
        self.assertEqual(response.status_code, 400)

    def test_review_get_success(self):
        response=self.client.get(self.URL, **self.header)
        self.assertEqual(response.json(),{
            'review_list':[{
                'review_id'  : self.review.id,
                'nick_name'  : self.DUMMY_NICKNAME,
                'user_img'   : self.DUMMY_IMAGE_URL,
                'content'    : self.DUMMY_REVIEW_CONTENTS,
                'created' : self.review.created.strftime('%Y.%m.%d'),
            }]
        })
        self.assertEqual(response.status_code, 200)
    
    def test_authorbook_get_fail(self):
        response = self.client.get('/books/45678/review', **self.header)
        self.assertEqual(response.json(), {'message':'NOT_EXIST_BOOK'})
        self.assertEqual(response.status_code, 400)

    def test_review_delete_fail(self):
        response = self.client.delete('/book/1/review?review_id=200', **self.header)
        self.assertEqual(response.json(), {'message':'NOT_EXIST_REVIEW'})
        self.assertEqual(response.status_code, 400)
    
    def test_review_delete_not_this_user(self):
        access_token = jwt.encode(
                            {'user_id':User.objects.get(id=2).id}, 
                            my_settings.SECRET_KEY,
                            algorithm=my_settings.JWT_ALGORITHM
                        ).decode('utf-8')
        response = self.client.delete('/books/1/review?review_id=1', 
                                      **{'HTTP_Authorization':}:access_token)
                                      # 기존 토큰을 dlete메서드로 지워버림
        self.assertEqual(response.json(), 'UNAUTHORIZED')
        self.assertEqual(response.status_code, 400)


class ReviewLikeTestCase(TestCase):
    def setUp(self):
        self.URL = '/books/reviewlike'
        self.client = Client()


        self.DUMMY_TITLE            = 'title'
        self.DUMMY_SUBTITLE         = 'sub'
        self.DUMMY_COMPANY          = 'company'
        self.DUMMY_AUTHOR           = 'author'
        self.DUMMY_CONTENT          = 'content'
        self.DUMMY_COMPANY_REVIEW   = 'company_review'
        self.DUMMY_PAGE             = 1
        self.DUMMY_PUBLICATION_DATE = '2020-02-22'
        self.DUMMY_DESCRIPTION      = 'description'
        self.DUMMY_REDER            = 10
        self.DUMMY_CATEGORY         = 'category'

        self.DUMMY_NICKNAME         = 'hello'
        self.DUMMY_IMAGE_URL        = 'image_url'
        self.DUMMY_REVIEW_CONTENTS  = 'GOOD'
        self.DUMMY_REVIEW_DATE      = '2020.12.01'


        self.user = User.objects.create(
            id   = 1,
            nickname  = self.DUMMY_NICKNAME,
            image_url = self.DUMMY_IMAGE_URL

        )
        self.user2 = User.objects.create(
            id   = 2,
            nickname  = self.DUMMY_NICKNAME,
            image_url = self.DUMMY_IMAGE_URL

        )
        self.category = Category.objects.create(
            id   = 1,
            name = self.DUMMY_CATEGORY
        )
        self.book = Book.objects.create(
            id               = 1,
            title            = self.DUMMY_TITLE,
            image_url        = self.DUMMY_IMAGE_URL,
            subtitle         = self.DUMMY_SUBTITLE,
            company          = self.DUMMY_COMPANY,
            author           = self.DUMMY_AUTHOR,
            contents         = self.DUMMY_CONTENT,
            company_review   = self.DUMMY_COMPANY_REVIEW,
            page             = self.DUMMY_PAGE,
            publication_date = self.DUMMY_PUBLICATION_DATE,
            description      = self.DUMMY_DESCRIPTION,
            category_id      = 1,
        )
        self.reivew = Review.objects.create(
            id         = 1,
            user_id    = self.user.id,
            book_id    = self.book.id,
            contents   = self.DUMMY_REVIEW_CONTENTS,
            created = '2020.12.01'
        )

        self.userbook = UserBook.objects.create(
            id   = 1,
            user_id = 1,
            book_id = 1,
            page= 1,
            time = 60 ,
        )

        self.like = Like.objects.create(
            id         = 1,
            user_id    = self.user.id,
            review_id  = self.book.id
        )

        self.DUMMY_AUTH = jwt.encode(
            {'user_id':self.user.id},
            my_settings.SECRET_KEY['secret'],
            algorithm=my_settings.JWT_ALGORITHM
        ).decode('utf-8')

        self.header = {
            'HTTP_Authorization': self.DUMMY_AUTH
        }
    
    def tearDown(self):
        pass

    def test_reviewlike_patch_cancel(self):
        request = {
            'review_id' : 1
        }

        response = self.client.patch(self.URL,
                                     request,
                                     content_type='application/json',
                                     **self.header,
                                    )
        self.assertEqual(response.json(), {'message':'CANCEL', 'like':False})
        self.assertEqual(response.status_code, 200)

    def test_reviewlike_patch_not_exist_review(self):
        request = {
            'review_id' : None
        }
        response = self.client.patch(self.URL,
                                     request,
                                     content_type='application/json',
                                     **self.header,
        )
        self.assertEqual(response.json(), {'message':'CANCEL', 'like':False})
        self.assertEqual(response.status_code, 200)

    def test_reviewlike_patch_success(self):
        request = {
            'review_id' : 1
        }

        access_token = jwt.encode({'user_id':User.objects.get(id=2).id},
                                  my_settings.SECRET_KEY,
                                  algorithm=my_settings.JWT_ALGORITHM
                                ).decode('utf-8')
        response = self.client.patch(self.URL,
                                     request,
                                     contet_type='application/json',
                                     **{'HTTP_Authorizaion':access_token}
                                 )
        self.assertEqual(response.json(), {'message':'SUCCESS'})
        self.assertEqual(response.status_code, 200)



































































