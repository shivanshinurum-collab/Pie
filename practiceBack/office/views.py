from django.shortcuts import render
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from office.models import user
from django.contrib.auth.hashers import make_password , check_password

@api_view(['GET'])
def home(request):
    return Response({
        'message' : 'Hello My name is Annu'
    })

@api_view(["GET"])
def name(request):
    return Response({
        'message':"Hello My name is Shivansh",
        'status' : "TRUE",
        'ABCD':"DKSKSS"
    })

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    users = user.objects.all()

    for i in users:
        if email == i.email and check_password(password , i.password):
            return Response({
            'status':True,
            'message':'Successfully Login'
        })

    
    return Response({
        'status' : False,
        'message':'Wrong Password or Email'
    })

@api_view(["POST"])
def register(request):
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not name or not password:
        return Response({
            'status' : False,
            'message' : "Fields are required"
        })
    else:
        ab = user.objects.filter(email = email)

        if ab:
            return Response({
                'status' : False,
                'message' : "Email already exists"
            })

        new_user = user.objects.create(
            name = name,
            email = email,
            password = make_password(password)
            )
        return Response({
            'status' : True,
            'message' : "Successfully Register Account",
            'user':{
                'name' : new_user.name,
                'email' : new_user.email,
                'password' : make_password(password)
            }
        })    

@api_view(["GET"])
def allUser(request):
    all_user = user.objects.all()

    users = []

    for i in all_user:
        users.append({
            'name':i.name,
            'email':i.email,
            'password':i.password
        })
    return Response({
        'status' : True,
        'users': users
    })

@api_view(["GET"])
def deleteUser(request):
    email = request.GET.get('email')

    delete_count, _ = user.objects.filter(email = email).delete()

    if delete_count == 0 :
        return Response({
            'status':False,
            'message':'User Not Found'
        })
    return Response({
        'status':True,
        'message':"successfully Delete User"
    })

@api_view(["POST"])
def updateUser(request):
    name = request.data.get('name')
    email = request.data.get('email')

    count = user.objects.filter(email = email).update(
        name = name,
    )

    if count == 0 :
        return Response({
            'status' : False,
            'message':'User Not Found'
        })
    
    return Response({
        'status':True,
        'message':'Successfully Update User'
    })

@api_view(['POST'])
def changePassword(request):
    email = request.data.get('email')
    password = request.data.get('password')

    count = user.objects.filter(email = email).update(password = make_password(password))

    if count == 0 :
        return Response({
            'status' : False,
            'message':'User Not Found'
        })
    
    return Response({
        'status':True,
        'message':'Sucessesfully Password Change'
    })



