from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from teacherhire.models import *
from rest_framework.exceptions import NotFound
from teacherhire.serializers import *
from .authentication import ExpiringTokenAuthentication  
from rest_framework.decorators import action
from .permissions import IsRecruiterPermission, IsAdminPermission 
import uuid  
from .models import Level, Subject, Question, ClassCategory
from .serializers import QuestionSerializer

    
class RecruiterView(APIView):
    permission_classes = [IsRecruiterPermission]
    def get(self, request):
        return Response({"message": "You are a recruiter!"}, status=status.HTTP_200_OK)

class AdminView(APIView):
    permission_classes = [IsAdminPermission]

    def get(self, request):
        return Response({"message": "You are an admin!"}, status=status.HTTP_200_OK)


def check_for_duplicate(model_class, **kwargs):
    return model_class.objects.filter(**kwargs).exists()

def create_object(serializer_class, request_data, model_class):
    serializer = serializer_class(data=request_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# for authenticated teacher
def create_auth_data(serializer_class, request_data, model_class, user, *args, **kwargs):
    if not user or not user.is_authenticated:
        return Response(
            {'message': 'Authentication required to perform this action.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = serializer_class(data=request_data)
    if serializer.is_valid():
        serializer.save(user=user)  
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def update_auth_data(serialiazer_class, instance, request_data, user):
    serializer = serialiazer_class(instance, data=request_data, partial=False)
    if serializer.is_valid():
        serializer.save(user=user)
        return Response({"detail": "Data updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_single_object(viewset):
    queryset = viewset.get_queryset()
    profile = queryset.first()
    serializer = viewset.get_serializer(profile)
    return Response(serializer.data)

def get_count(model_class):
    return model_class.objects.count()

class RegisterUser(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'error': serializer.errors,
                # Todo
                'message': 'Something went wrong'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer.save()
        user = CustomUser.objects.get(email=serializer.data['email'])
        token_obj, __ = Token.objects.get_or_create(user=user)

        return Response({
            'payload': serializer.data,
            'token': str(token_obj),
            'message': 'Your data is saved'
        },status=status.HTTP_200_OK)
    

def generate_refresh_token():
    return str(uuid.uuid4())

class LoginUser(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
            
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check password validity
        if user.check_password(password):
            # Delete old token if it exists
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)


            refresh_token = generate_refresh_token()
      
            is_admin =  user.is_staff and user.is_recruiter            
            roles = {                
                'is_admin': is_admin,
                'is_admin': user.is_staff,
                'is_recruiter': user.is_recruiter,
                'is_user': True
                
            }
            return Response({
                'access_token': token.key,
                'refresh_token': refresh_token,
                'Fname':user.Fname, 
                'email':user.email, 
                'roles': roles,
                # 'refresh_expires_at': refresh_expires_at,  
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
class LogoutUser(APIView):
    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({"success": "Logout successful"}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    


#TeacerAddress GET ,CREATE ,DELETE 
class TeachersAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    serializer_class = TeachersAddressSerializer
    queryset = TeachersAddress.objects.all().select_related('user')

    # def create(self, request, *args, **kwargs):
    #     print(f"User: {request.user}")
    #     return create_auth_data(self, TeachersAddressSerializer, request.data, TeachersAddress)

    @action(detail=False, methods=['get'])
    def count(self, request):
        print(f"User: {request.user}")
        count = get_count(TeachersAddress)
        return Response({"count": count})
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "TeacherAddress deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
class SingleTeachersAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    serializer_class = TeachersAddressSerializer 
    queryset = TeachersAddress.objects.all().select_related('user')

    def create(self, request, *args, **kwargs):
        print("Request data:", request.data)
        data = request.data.copy()  
        address_type = data.get('address_type')  

        # Validate the `address_type`
        if not address_type or address_type not in ['current', 'permanent']:
            return Response(
                {"detail": "Invalid or missing 'address_type'. Expected 'current' or 'permanent'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Check if the address already exists for the user
        if TeachersAddress.objects.filter(address_type=address_type, user=request.user).exists():
            return Response(
                {"detail": f"{address_type.capitalize()} address already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Associate the address with the authenticated user
        data['user'] = request.user.id  
        # Serialize and validate data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        address = TeachersAddress.objects.filter(user=request.user).first()

        if address:
           return update_auth_data(
               serialiazer_class=self.get_serializer_class(),
               instance=address,
               request_data=data,
               user=request.user
           )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeachersAddress
            )
    def get_queryset(self):
        return TeachersAddress.objects.filter(user=self.request.user)

    # def list(self, request, *args, **kwargs):
    #     return self.retrieve(request, *args, **kwargs)
    
    # def get_object(self):
    #  try:
    #     return TeachersAddress.objects.get(user=self.request.user)
    #  except TeachersAddress.DoesNotExist:
    #     return Response({"detail": "This address not found."}, status=status.HTTP_404_NOT_FOUND)


class EducationalQulificationViewSet(viewsets.ModelViewSet):   
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication] 
    serializer_class = EducationalQualificationSerializer 
    queryset = EducationalQualification.objects.all()

    def create(self, request):
        return create_object(EducationalQualificationSerializer, request.data, EducationalQualification)


    @action(detail=False, methods=['get'])
    def count(self, request):
        count = get_count(EducationalQualification)
        return Response({"count": count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Educationqulification deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class LevelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication]     
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    
    @action(detail=False, methods=['get'])
    def count(self):
        count = get_count(Level)
        return Response({"Count": count})
    
    @action(detail=True, methods=['get'], url_path=r'classes/(?P<class_category_id>[^/.]+)/?subject/(?P<subject_id>[^/.]+)/?questions')
    def level_questions(self, request, pk=None, subject_id=None, class_category_id=None):
        """
        Custom action to fetch questions by level, optional subject, and optional class category.
        """
        try:
            level = Level.objects.get(pk=pk)
        except Level.DoesNotExist:
            return Response({"error": "Level not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Start with filtering by level
        questions = Question.objects.filter(level=level)
        
        # Filter by subject if provided
        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id)
            except Subject.DoesNotExist:
                return Response({"error": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
            questions = questions.filter(subject=subject)

        # Filter by class category if provided
        if class_category_id:
            try:
                class_category = ClassCategory.objects.get(pk=class_category_id)
            except ClassCategory.DoesNotExist:
                return Response({"error": "Class Category not found"}, status=status.HTTP_404_NOT_FOUND)
            questions = questions.filter(classCategory=class_category)  # Use 'classCategory' instead of 'classes'

        # Serialize the questions
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    def destroy(self, request, *args, **kwargs):    
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Level deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    
class SkillViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset = Skill.objects.all()    
    serializer_class = SkillSerializer

    @action(detail=False, methods=['get'])
    def count(self, request):
        count = get_count(Skill)
        return Response({"Count": count})    
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Skill deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
  
    
class TeacherSkillViewSet(viewsets.ModelViewSet):
    queryset = TeacherSkill.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    serializer_class = TeacherSkillSerializer
    
    def create(self, request):
        return create_object(TeacherSkillSerializer, request.data, TeacherSkill)
    @action(detail=False, methods=['get'])    
    def count(self, request):
        count = get_count(TeacherSkill)
        return Response({"Count": count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "TeacherSkill deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class SingleTeacherSkillViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    serializer_class = TeacherSkillSerializer
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeacherSkill)
    
    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        skill = TeacherSkill.objects.filter(user=request.user).first()

        if skill:
            return update_auth_data(
               serialiazer_class=self.get_serializer_class(),
               instance=skill,
               request_data=data,
               user=request.user
           )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeacherSkill
            )

    def get_queryset(self):
        return TeacherSkill.objects.filter(user=self.request.user)

    # def list(self, request, *args, **kwargs):
    #     return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        try:
            return TeacherSkill.objects.get(user=self.request.user)
        except TeacherSkill.DoesNotExist:
            raise Response({"detail": "this user skill not found."}, status=status.HTTP_404_NOT_FOUND)

class SubjectViewSet(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated] 
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(Subject)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "subject deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class TeacherViewSet(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset= Teacher.objects.all().select_related('user')
    serializer_class = TeacherSerializer

    # def create(self,request):
    #     return create_object(TeacherSerializer,request.data,Teacher)
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(Teacher)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teacher deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class SingleTeacherViewSet(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    serializer_class = TeacherSerializer

    def create(self,request,*args, **kwargs):
        return create_auth_data(self, TeacherSerializer, request.data, Teacher)
    
    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        teacher = Teacher.objects.filter(user=request.user).first()

        if teacher:
           return update_auth_data(
               serialiazer_class=self.get_serializer_class(),
               instance=teacher,
               request_data=data,
               user=request.user
           )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=Teacher
            )

    def get_queryset(self):
        return Teacher.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        try:
            return Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            raise Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    
    
    
class ClassCategoryViewSet(viewsets.ModelViewSet):    
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [ExpiringTokenAuthentication] 
    queryset= ClassCategory.objects.all()
    serializer_class = ClassCategorySerializer

    def create(self,request):
        return create_object(ClassCategorySerializer,request.data,ClassCategory)
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(ClassCategory)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "ClassCategory deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    
class TeacherQualificationViewSet(viewsets.ModelViewSet): 
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = TeacherQualification.objects.all()
    serializer_class = TeacherQualificationSerializer

    @action(detail=False, methods=['get'])
    def count(self, request):
        count = get_count(TeacherQualification)
        return Response({"count": count})
    def create(self, request, *args, **kwargs):
        return create_object(TeacherQualificationSerializer, request.data, TeacherQualification)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teacherqualification deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class SingleTeacherQualificationViewSet(viewsets.ModelViewSet): 
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = TeacherQualification.objects.all()
    serializer_class = TeacherQualificationSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeacherQualification
            )
    
    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        teacher_qualification = TeacherQualification.objects.filter(user=request.user).first()

        if teacher_qualification:
           return update_auth_data(
               serialiazer_class=self.get_serializer_class(),
               instance=teacher_qualification,
               request_data=data,
               user=request.user
           )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeacherQualification
            )

    def get_queryset(self):
        return TeacherQualification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        try:
            return TeacherQualification.objects.get(user=self.request.user)
        except TeacherQualification.DoesNotExist:
            raise Response({"detail": "Qualification not found."}, status=status.HTTP_404_NOT_FOUND)

    
class TeacherExperiencesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset = TeacherExperiences.objects.all()
    serializer_class = TeacherExperiencesSerializer

    def create(self,request,*args, **kwargs):
        return create_object(TeacherExperiencesSerializer,request.data,TeacherExperiences)
   
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(TeacherExperiences)
        return Response({"Count":count}) 
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teacherexperience deleted successfully"}, status=status.HTTP_204_NO_CONTENT)  

class SingleTeacherExperiencesViewSet(viewsets.ModelViewSet): 
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = TeacherExperiences.objects.all()
    serializer_class = TeacherExperiencesSerializer

    def create(self, request, *args, **kwargs):
        return create_auth_data(self, TeacherExperiencesSerializer, request.data, TeacherExperiences)
    def get_queryset(self):
        return TeacherExperiences.objects.filter(user=self.request.user)
    def list(self, request, *args, **kwargs):
        return get_single_object(self)
    
    
class QuestionViewSet(viewsets.ModelViewSet): 
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
   

    # def create(self,request):
    #     return create_object(QuestionSerializer,request.data,Question)
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(Question)
        return Response({"Count":count})
    
    # def get_queryset(self):
    #     queryset = Level.objects.all() def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)
    #     level_filter = self.request.query_params.get('level', None)
    #     if level_filter is not None:
    #         level_filter = int(level_filter)
    #         if level_filter == 1:
    #             queryset = queryset.filter(question__level=1)
    #         else:
    #             queryset = queryset.filter(question__level=level_filter)
    #     return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message":" Question deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class RoleViewSet(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset= Role.objects.all()
    serializer_class = RoleSerializer
    def create(self,request):
        return create_object(RoleSerializer,request.data,Role)
    
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(Role)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Role deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class PreferenceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = Preference.objects.all()
    serializer_class = PreferenceSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        # Check if the user already has a preference
        if Preference.objects.filter(user=request.user).exists():
            return Response({"detail": "Preference already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        # Check if the user has an existing preference
        profile = Preference.objects.filter(user=request.user).first()

        if profile:
            return self.update_auth_data(
                serializer_class=self.get_serializer_class(),
                instance=profile,
                request_data=data,
                user=request.user
            )
        else:
            return self.create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=Preference
            )

    def get_queryset(self):
        return Preference.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        # Retrieve the preference object for the current user
        try:
            return Preference.objects.get(user=self.request.user)
        except Preference.DoesNotExist:
            raise NotFound({"detail": "Preference not found."})

    def update_auth_data(self, serializer_class, instance, request_data, user):
        """Handle updating preference data."""
        serializer = serializer_class(instance, data=request_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_auth_data(self, serializer_class, request_data, user, model_class):
        """Handle creating preference data."""
        serializer = serializer_class(data=request_data)
        if serializer.is_valid():
            serializer.save(user=user)  # Assign the user to the new preference object
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   
class TeacherSubjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication]     
    queryset = TeacherSubject.objects.all()
    serializer_class = TeacherSubjectSerializer
    def create(self,request):
        return create_object(TeacherSubjectSerializer,request.data,TeacherSubject)
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(TeacherSubject)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teachersubject deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class SingleTeacherSubjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = TeacherSubject.objects.all()
    serializer_class = TeacherSubjectSerializer

    def get_queryset(self):
        return TeacherSubject.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
            data = request.data.copy()
            data['user'] = request.user.id
            if TeacherSubject.objects.filter(user=request.user).exists():
                return Response({"detail": "SingleTeacherSubject already exists. "}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # def list(self, request, *args, **kwargs):
    #     return self.retrieve(request, *args, **kwargs)
    def get_object(self):
        try: 
            return TeacherSubject.objects.get(user=self.request.user)
        except TeacherSubject.DoesNotExist:
            raise NotFound({"detail": "TeacherSubject not found."})
    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        SingleTeacherSubject = TeacherSubject.objects.filter(user=request.user).first()

        if SingleTeacherSubject:
            return update_auth_data(
                serializer_class=self.get_serializer_class(),
                instance=SingleTeacherSubject,
                request_data=data,
                user=request.user
            )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=TeacherSubject
            )
    def delete(self, request, *args, **kwargs):
        try:
            profile = TeacherSubject.objects.get(user=request.user)
            profile.delete()
            return Response({"detail": "TeacherSubject deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except TeacherSubject.DoesNotExist:
            return Response({"detail": "TeacherSubject not found."}, status=status.HTTP_404_NOT_FOUND)

class TeacherClassCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication]     
    queryset = TeacherClassCategory.objects.all()
    serializer_class = TeacherClassCategorySerializer
    def create(self,request):
        return create_object(TeacherClassCategorySerializer,request.data,TeacherClassCategory)
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(TeacherClassCategory)
        return Response({"Count":count})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teacherclasscategory deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class TeacherExamResultViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication]     
    queryset = TeacherExamResult.objects.all()
    serializer_class = TeacherExamResultSerializer

    def create(self, request, *args, **kwargs):
        # Add the authenticated user to the request data
        data = request.data.copy()
        data['user'] = request.user.id  # Set user to the currently authenticated user

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    
    @action (detail=False,methods=['get'])
    def count(self,request):
        count = get_count(TeacherExamResult)
        return Response({"Count":count}) 
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Teacher exam result deleted successfully"}, status=status.HTTP_204_NO_CONTENT)   

class JobPreferenceLocationViewSet(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication] 
    queryset= JobPreferenceLocation.objects.all()
    serializer_class = JobPreferenceLocationSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Job preference location deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class BasicProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = BasicProfile.objects.all()
    serializer_class = BasicProfileSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        if BasicProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        profile = BasicProfile.objects.filter(user=request.user).first()

        if profile:
            return update_auth_data(
                serialiazer_class=self.get_serializer_class(),
                instance=profile,
                request_data=data,
                user=request.user
            )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=BasicProfile
            )

    def get_queryset(self):
        return BasicProfile.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def get_object(self):
        """
        Fetch the BasicProfile object for the logged-in user. 
        If it doesn't exist, create one or return an appropriate response.
        """
        profile = BasicProfile.objects.filter(user=self.request.user).first()
        if profile:
            return profile
        else:
            # Option 1: Automatically create a profile for the user
            data = {"user": self.request.user.id}
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return serializer.instance  # Return the newly created profile
            
            # Option 2: Raise an error response if creation fails
            raise Response({"detail": "Profile not found and could not be created."}, status=status.HTTP_400_BAD_REQUEST)


    # def get_object(self):
    #     try:
    #         return BasicProfile.objects.get(user=self.request.user)
    #     except BasicProfile.DoesNotExist:
    #         raise Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    def delete(self, request):
        try:
            profile = BasicProfile.objects.get(user=request.user)            
            profile.delete()            
            return Response({"detail": "Profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except BasicProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        

class CustomUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]    
    authentication_classes = [ExpiringTokenAuthentication]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
   
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        if CustomUser.objects.filter(username=request.user.username).exists():

            return Response({"detail": "Customuser already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        
        profile = CustomUser.objects.filter(username=request.user.username).first()

        if profile:
           return update_auth_data(
               serialiazer_class=self.get_serializer_class(),
               instance=profile,
               request_data=data,
               user=request.user
           )
        else:
            return create_auth_data(
                serializer_class=self.get_serializer_class(),
                request_data=data,
                user=request.user,
                model_class=CustomUser
            )

    def get_queryset(self):
        return CustomUser.objects.filter(username=self.request.user.username)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        try:
           return CustomUser.objects.get(id=self.request.user.id)

        except CustomUser.DoesNotExist:
            raise Response({"detail": "Customuser not found."}, status=status.HTTP_404_NOT_FOUND)
    def delete(self, request):
        try:
            profile = CustomUser.objects.get(user=request.user)            
            profile.delete()            
            return Response({"detail": "Customuser deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Customuser not found."}, status=status.HTTP_404_NOT_FOUND)
    
class TeacherJobTypeViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]    
    # authentication_classes = [ExpiringTokenAuthentication]
    queryset = TeacherJobType.objects.all()
    serializer_class = TeacherJobTypeSerializer


      

    