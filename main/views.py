from django.shortcuts import render, redirect

from django.core.exceptions import SuspiciousOperation

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from django.urls import reverse
from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect
from .models import Note
import sqlite3
import os.path
import datetime


# FIX TO RATELIMIT FLAW:
# Checks IP and username being used for login to ratelimit
#@ratelimit(key='user_or_ip', rate='30/h')
@csrf_protect
def login(request):
    
    if request.user.is_authenticated:
        return redirect('home')
    
    # Logic from here:https://stackoverflow.com/questions/62548264/overriding-django-loginview
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username,password=password)
        if user:
            if user.is_active:
                auth_login(request,user)
                return redirect(reverse('home'))
        else:
            messages.error(request,'Username or password not correct!')
            
            return redirect(reverse('login'))          
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password == password2:
            user = get_user_model().objects.create_user(username = username, password=password)
            user.save()
            messages.success(request, 'User registered!')
            render(request, "login.html")
        else:
            messages.error(request, "Passwords didn't match!")
    
    return render(request, 'register.html')

@login_required
def add_note(request):
    newTitle = request.POST.get("title")
    newContent = request.POST.get("content")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "../db.sqlite3")
    
    sqlConnection = sqlite3.connect(db_path)
    
    try:
        cursor = sqlConnection.cursor()
        ownerId = request.user.id
        createdTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(type(newTitle), type(newContent), type(ownerId))
        
        # FLAW: Very bad way to do SQL queries, RAW SQL
        queryString = f"INSERT INTO main_note (title, content, owner_id, created_time) VALUES ('{newTitle}', '{newContent}', '{str(ownerId)}', '{createdTime}');"
        cursor.execute(queryString)
        
        # FIX TO SQL INJECTION FLAW (With SQL clause) (parametrized query to minimize or remove the vulnerability):
        #queryString = 'INSERT INTO main_note (title, content, owner_id, created_time) VALUES (?, ?, ?, ?);'
        #cursor.execute(queryString, (newTitle, newContent, str(ownerId), createdTime))
        
        sqlConnection.commit()
    except Exception as ex:
        print(f"Connection failed: {ex}")
    finally:
        print("Insert OK")
        sqlConnection.close()
    
    # FLAW FIXED, BEST WAY: Correct way to accomplish the database insertions using ORM: 
    # newNote = Note(owner=request.user, title=newTitle, content=newContent)
    # newNote.save()
    
    #return render(request, 'home.html')
    return redirect("home")

@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    username = request.user.username
    
    notes = []
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "../db.sqlite3")
    
    sqlConnection = sqlite3.connect(db_path) #check if path needed
    
    try:
        sqlConnection.cursor()
        sqlConnection.row_factory = sqlite3.Row
        cursor = sqlConnection.cursor()
        ownerId = request.user.id
        queryString = 'SELECT n.title, n.content FROM main_note n WHERE owner_id = ' + str(ownerId)
        rawNotes = cursor.execute(queryString).fetchall()
        
        # This logic from here: https://nickgeorge.net/programming/python-sqlite3-extract-to-dictionary/
        # Workaround to get the template work with both raw SQL and ORM
        notes = [{k: note[k] for k in note.keys()} for note in rawNotes]
        print(notes)
    except Exception as ex:
        print("Connection failed: " + ex)
    finally:
        sqlConnection.close()
    
    print(rawNotes)
    
    
    # Vulnerability fixed: Using ORM to retrieve the notes for a specific user
    # try:
    #     notes = Note.objects.filter(owner=request.user)
    #     print("Notes: ", notes)
    # except Note.DoesNotExist:
    #     notes = []
    
    
    if notes == []:
        print("No notes..")
    else:
        print("Notes not empty!")
        # print("Notes: ", notes)
    
    return render(request, 'home.html', {'notes' : notes, "username" : username})

@login_required
def logout_view(request):
    request.logout.success = True
    
    logout(request)
    return render(request, 'login.html')

# https://nickgeorge.net/programming/python-sqlite3-extract-to-dictionary/
# Example:
# def sql_data_to_list_of_dicts(path_to_db, select_query):
#     """Returns data from an SQL query as a list of dicts."""
#     try:
#         con = sqlite3.connect(path_to_db)
#         con.row_factory = sqlite3.Row
#         things = con.execute(select_query).fetchall()
#         unpacked = [{k: item[k] for k in item.keys()} for item in things]
#         return unpacked
#     except Exception as e:
#         print(f"Failed to execute. Query: {select_query}\n with error:\n{e}")
#         return []
#     finally:
#         con.close()
