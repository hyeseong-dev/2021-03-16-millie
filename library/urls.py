from django.urls     import path
from .views          import (
    MyLibraryView,
    LibraryInfoView,
    LibraryBookListView,
    StatisticsView
)

urlpatterns = [
    path('', LibraryInfoView.as_view()),
    path('/my_library', MyLibraryView.as_view()),
    path('/statistics', StatisticsView.as_view()),
    path('/books', LibraryBookListView.as_view()),
]