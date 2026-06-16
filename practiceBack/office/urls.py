from django.urls import path
from office.views import home , name , login , register , allUser, deleteUser , updateUser , changePassword

urlpatterns = [
    path('home/',home),
    path('',name),
    path('login/' , login),
    path('register/',register),
    path('all/',allUser),
    path('delete/',deleteUser),
    path('update/',updateUser),
    path('changePassword/',changePassword),
]


