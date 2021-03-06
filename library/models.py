from django.db import models


class Library(models.Model):
    user       = models.ForeignKey('user.User', on_delete=models.CASCADE)
    name       = models.CharField(max_length=45)
    image_url  = models.URLField(max_length=200, null=True, blank=True)
    books      = models.ManyToManyField('book.Book', through='LibraryBook')

    class Meta:
        db_table = 'libraries'


class LibraryBook(models.Model):
    library     = models.ForeignKey(Library, on_delete=models.CASCADE) # Library 정참조
    book        = models.ForeignKey('book.Book', on_delete=models.CASCADE) # Book 정참조
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'library_books'