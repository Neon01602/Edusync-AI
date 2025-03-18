from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken
from django.shortcuts import render
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from .forms import ClassroomForm
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Classroom, Classwork
from django.http import JsonResponse, HttpResponseRedirect
import json
from django.middleware.csrf import get_token
from .forms import ClassworkForm
from django.http import HttpResponse

@login_required
def view_classroom(request, class_code):
    print("Received class code:", class_code)  # Debugging

    try:
        classroom = Classroom.objects.get(unique_code=class_code)
        print("Classroom found:", classroom.name)  # Confirm it exists
    except Classroom.DoesNotExist:
        print("Classroom does not exist!")  # Should not happen
        return HttpResponse("Classroom not found!", status=404)

    is_teacher = request.user == classroom.teacher  

    return render(request, 'classroom_list.html', {
        'classroom': classroom,
        'is_teacher': is_teacher
    })
    
    
def get_class_students(request, class_code):
    try:
        classroom = Classroom.objects.get(unique_code=class_code)
        students = classroom.students.all().values('id', 'username', 'first_name', 'last_name', 'profile_picture')
        
        return JsonResponse({'students': list(students)}, safe=False)
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Classroom not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_account(request):
    if request.method == "POST":
        try:
            user = request.user
            user.delete()
            return JsonResponse({"message": "Account deleted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request."}, status=400)


@login_required
def leave_class(request, class_code):  # Accept class_code from URL
    classroom = get_object_or_404(Classroom, unique_code=class_code)
    user = request.user

    if user in classroom.students.all():
        classroom.students.remove(user)  # Remove user from the class
        
        # Redirect to home page after leaving the class
        return redirect('home')  # Make sure 'home' is a valid URL name in urls.py

    return JsonResponse({"error": "You are not a member of this class."}, status=400)

@login_required
def add_classwork(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if request.user != classroom.teacher:
        return JsonResponse({'error': 'You are not allowed to add work!'}, status=403)

    if request.method == "POST":
        form = ClassworkForm(request.POST, request.FILES)
        if form.is_valid():
            classwork = form.save(commit=False)
            classwork.classroom = classroom
            classwork.teacher = request.user
            classwork.save()
            return JsonResponse({'message': 'Classwork added successfully!'})
        else:
            return JsonResponse({'error': form.errors}, status=400)
    
    form = ClassworkForm()
    return render(request, 'classroom_list.html', {'form': form, 'classroom': classroom})


@login_required
def view_classwork(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.user != classroom.teacher and request.user not in classroom.students.all():
        return JsonResponse({'error': 'Unauthorized access!'}, status=403)

    classworks = Classwork.objects.filter(classroom=classroom).order_by('-created_at')
    
    # ✅ Return JSON response for AJAX
    data = {
        "classworks": [
            {
                "title": work.title,
                "description": work.description,
                "created_at": work.created_at.strftime("%B %d, %Y %H:%M"),
                "file_url": request.build_absolute_uri(work.file.url) if work.file else None
            }
            for work in classworks
        ]
    }
    return JsonResponse(data)


def join_class(request):
    if request.method == "POST":
        class_code = request.POST.get("class_code", "").strip()
        classroom = Classroom.objects.filter(unique_code=class_code).first()

        if classroom:
            user = request.user
            print(f"DEBUG: User {user.username} is attempting to join {classroom.name}")  # Debug

            if user in classroom.students.all():
                print("DEBUG: User already joined this class")  # Debug
                return JsonResponse({"exists": True, "already_joined": True})
            else:
                classroom.students.add(user)
                classroom.save()  # Ensure the save() method is called

                print(f"DEBUG: {user.username} has been added to {classroom.name}")  # Debug

                return JsonResponse({"exists": True, "already_joined": False, "name": classroom.name, "subject": classroom.subject, "unique_code": class_code})
        else:
            print("DEBUG: Invalid class code entered")  # Debug
            return JsonResponse({"exists": False})

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_joined_classes(request):
    user = request.user
    joined_classes = Classroom.objects.filter(students=user).values("name", "subject", "unique_code")

    print(f"DEBUG: {user.username} has joined these classes:", list(joined_classes))  # Debug

    return JsonResponse({"joined_classes": list(joined_classes)})


@login_required
def create_classroom(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            subject = data.get("subject")

            if not name or not subject:
                return JsonResponse({"error": "Both name and subject are required."}, status=400)

            classroom = Classroom.objects.create(
                teacher=request.user, 
                name=name, 
                subject=subject
            )

            return JsonResponse({
                "message": "Class created successfully!",
                "class_id": classroom.id,
                "name": classroom.name,
                "subject": classroom.subject,
                "unique_code": classroom.unique_code
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def get_user_classes(request):
    """Fetch classes created by the logged-in user along with the teacher's name"""
    teacher = request.user
    user_classes = Classroom.objects.filter(teacher=teacher).values(
        "id", "name", "subject", "unique_code"
    )

    return JsonResponse({"classes": list(user_classes), "teacher_name": teacher.get_full_name() or teacher.username})

# CSRF Token View (optional)
def get_csrf_token(request):
    return JsonResponse({'csrftoken': get_token(request)})

@login_required
def edit_classroom(request, class_id):
    """ Allows only the class creator (teacher) to edit details """
    classroom = get_object_or_404(Classroom, id=class_id)

    if request.user != classroom.teacher:
        messages.error(request, "You do not have permission to edit this class.")
        return redirect("classroom_list")

    if request.method == "POST":
        classroom.name = request.POST.get("name", classroom.name)
        classroom.subject = request.POST.get("subject", classroom.subject)
        classroom.save()
        messages.success(request, "Class updated successfully!")

    return redirect("classroom_detail", class_id=class_id)


@login_required
def join_classroom(request, unique_code):
    """ Allows students to join a class using the unique link """
    classroom = get_object_or_404(Classroom, unique_code=unique_code)

    if request.user not in classroom.students.all():
        classroom.students.add(request.user)
        messages.success(request, f"You have joined {classroom.name} successfully!")
    else:
        messages.warning(request, "You are already a member of this class.")

    return redirect("classroom_list")


@login_required
def classroom_list(request):
    """ Displays the classes the user created and the ones they joined """
    created_classes = Classroom.objects.filter(teacher=request.user)
    joined_classes = Classroom.objects.filter(students=request.user)

    return render(request, "classroom_list.html", {
        "created_classes": created_classes,
        "joined_classes": joined_classes
    })

    
    return render(request, 'create_class.html', {'form': form})

def classroom_courses(request):
    token = SocialToken.objects.get(account__user=request.user, account__provider='google')
    headers = {"Authorization": f"Bearer {token.token}"}
    response = requests.get("https://classroom.googleapis.com/v1/courses", headers=headers)
    data = response.json()
    return render(request, 'classroom.html', {'courses': data.get("courses", [])})

@login_required
def get_user_profile(request):
    user = request.user
    return JsonResponse({
        "first_name": user.first_name,  # ✅ Add first name
        "last_name": user.last_name,    # ✅ Add last name
        "username": user.username,
        "profile_picture": user.profile_picture if user.profile_picture else None,
    })


@never_cache
def main(request):
    return render(request, 'new.html')
# Create your views here.


def home(request):
    return render(request, 'home.html') 

def custom_logout(request):
    logout(request) 
    request.session.flush()# Logs out the user
    return redirect('/') 