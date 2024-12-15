from rest_framework import serializers
import re
from teacherhire.models import *
import random
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'password' ,'Fname', 'Lname', 'email',]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create(
            Fname=validated_data['Fname'],
            Lname=validated_data['Lname'],
            email=validated_data['email'],

        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    Fname = serializers.CharField(required=True)
    Lname = serializers.CharField(required=True)
    # email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'Fname', 'Lname']


    def create(self, validated_data):
        email = validated_data['email']
        base_username = email.split('@')[0]
        username = base_username
        Fname = validated_data['Fname']
        Lname = validated_data['Lname']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError({'email': 'Email is already in use.'})
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{random.randint(1000, 9999)}"
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=validated_data['password'],
                Fname=Fname,
                Lname=Lname
            )
        except Exception as e:
            raise ValidationError({'error': str(e)})
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(max_length=100)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise ValidationError({'email': 'Email not found.'})

        if not user.check_password(password):
            raise ValidationError({'password': 'Incorrect password.'})
        
        is_admin = user.is_staff
        is_recruiter = user.is_recruiter
        if is_admin and is_recruiter:
            is_admin = True
            
        data["is_admin"] = True if user.is_staff else False
        data["is_recruiter"] = True if user.is_recruiter else False
        data["user"] = user
        return data

class TeacherExperiencesSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    institution = serializers.CharField(max_length=255, required=False, allow_null=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    achievements = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = TeacherExperiences
        fields = "__all__"

    def validate_institution(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Institution name must be at least 3 characters long.")
        return value

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("End date cannot be earlier than start date.")

        return data

    def validate_achievements(self, value):
        if value:
            value = value.strip()
            if len(value) < 10:
                raise serializers.ValidationError("Achievements must be at least 10 characters long.")
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.user:
            representation['user'] = UserSerializer(instance.user).data
            representation['role'] = RoleSerializer(instance.role).data
        return representation

#subject serializer 
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'subject_name', 'subject_description']

    def validate_subject_name(self, value):
        if Subject.objects.filter(subject_name=value).exists():
            raise serializers.ValidationError("A subject with this name already exists.")
        return value


class ClassCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassCategory
        fields = ['id', 'name']

    def validate_name(self, value):
        if ClassCategory.objects.filter(name=value).exists():
            raise serializers.ValidationError("A classcategory with this name already exists.")
        return value

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['name','description']
    
    def validate_name(self, value):
        if Level.objects.filter(name=value).exists():
            raise serializers.ValidationError("A level with this name already exists.")
        return value

class SkillSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=20, required=False, allow_null=True)

    class Meta:
        model = Skill
        fields = "__all__"

    def validate_name(self, value):
        if value is not None:
            if len(value) < 3:
                raise serializers.ValidationError("Skill name must be at least 3 characters.")
        return value
    
    def validate_name(self, value):
        if Skill.objects.filter(name=value).exists():
            raise serializers.ValidationError("A skill with this name already exists.")
        return value
    

class TeachersAddressSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    pincode = serializers.CharField(max_length=6, required=False, allow_null=True)
    class Meta:
        model = TeachersAddress
        fields = '__all__'

    def validate_pincode(self, value):
        if value and (len(value) != 6 or not value.isdigit()):
            raise serializers.ValidationError("Pincode must be exactly 6 digits.")
        return value
   
class TeacherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    aadhar_no = serializers.CharField(max_length=12, required=False, allow_null=True)
    fullname = serializers.CharField(max_length=20, required=False, allow_null=True)
    phone = serializers.CharField(max_length=10, required=False, allow_null=True)
    alternate_phone = serializers.CharField(max_length=10, required=False, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    address = serializers.SerializerMethodField()
    teacher_experience = serializers.SerializerMethodField()
    teacherQualification = serializers.SerializerMethodField()
    teacherSkill = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            'id', 'user', 'fullname', 'gender', 'religion', 'nationality',
            'aadhar_no', 'phone', 'alternate_phone', 'verified',
            'class_categories', 'rating', 'date_of_birth',
            'availability_status', 'address', 'teacher_experience', 'teacherQualification', 'teacherSkill'
        ]

    def validate_fullname(self, value):
        if value is not None:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError("Full name must be at least 3 characters.")
        return value

    def validate_phone(self, value):
        return self.validate_phone_number(value)

    def validate_alternate_phone(self, value):
        return self.validate_phone_number(value)

    def validate_phone_number(self, value):
        if value:
            cleaned_value = re.sub(r'[^0-9]', '', value)
            if len(cleaned_value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits.")
            # if Teacher.objects.filter(phone=value).exists():
            #     raise serializers.ValidationError("This Phone no. is alreary exist.")
            if not cleaned_value.startswith(('6', '7', '8', '9')):
                raise serializers.ValidationError("Phone number must start with 6, 7, 8, or 9.")
            return cleaned_value
        return value

    def validate_aadhar_no(self, value):
        if value:
            if not re.match(r'^\d{12}$', value):
                raise serializers.ValidationError("Aadhar number must be exactly 12 digits.")
            # if Teacher.objects.filter(aadhar_no=value).exists():
            #     raise serializers.ValidationError("This Aadhar no. is alreary exist.")
        return value
    
    # def validate(self, data):
    #     user = data.get('user')
    #     if user and Teacher.objects.filter(user=user).exists():
    #         raise serializers.ValidationError({"user": "A teacher entry for this user already exists."})
    #     return data 

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        return representation

    def get_address(self, obj):
        addresses = TeachersAddress.objects.filter(user=obj.user)
        return TeachersAddressSerializer(addresses, many=True).data

    def get_teacher_experience(self, obj):
        teacher_experiences = TeacherExperiences.objects.filter(user=obj.user)
        return TeacherExperiencesSerializer(teacher_experiences, many=True).data

    def get_teacherQualification(self, obj):
        teacherQualifications = TeacherQualification.objects.filter(user=obj.user)
        return TeacherQualificationSerializer(teacherQualifications, many=True).data

    def get_teacherSkill(self, obj):
        teacherSkills = TeacherSkill.objects.filter(user=obj.user)
        return TeacherSkillSerializer(teacherSkills, many=True).data



class QuestionSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), required=True)
    level = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), required=True)
    classCategory = serializers.PrimaryKeyRelatedField(queryset=ClassCategory.objects.all(), required=True)
    text = serializers.CharField(max_length=2000, allow_null=True, required=False)
    options = serializers.JSONField(required=False, allow_null=True)
    class Meta:
        model = Question
        fields = "__all__"

    def validate_text(self, value):
        if value is not None and len(value)< 5:
            raise serializers.ValidationError("Text must be at least 5 characters.")
        if Question.objects.filter(text=value).exists():
            raise serializers.ValidationError("This question is already exists.")
        return value

    # def validate_options(self, value):
    #     if value is not None:
    #         if not isinstance(value, list):
    #             raise serializers.ValidationError("Options must be a list.")
    #         if len(value) != 4:
    #             raise serializers.ValidationError("Options must contain exactly 4 items.")
    #     return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['subject'] = SubjectSerializer(instance.subject).data
        representation['level'] = LevelSerializer(instance.level).data
        representation['classCategory'] = ClassCategorySerializer(instance.classCategory).data
        return representation


class TeacherSkillSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), required=False)
    class Meta:
        model = TeacherSkill
        fields = ['id', 'user', 'skill', 'proficiency_level', 'years_of_experience']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        representation['skill'] = SkillSerializer(instance.skill).data
        return representation
 
    def validate(self, attrs):
        user = attrs.get('user')
        skill = attrs.get('skill')
        # This user have skill already exists
        if TeacherSkill.objects.filter(user=user, skill=skill).exists():
            raise serializers.ValidationError('This user already has this skill.')
        return attrs

class EducationalQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationalQualification
        fields = '__all__'


class TeacherQualificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    qualification = serializers.PrimaryKeyRelatedField(queryset=EducationalQualification.objects.all(), required=True)

    class Meta:
        model = TeacherQualification
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        representation['qualification'] = EducationalQualificationSerializer(instance.qualification).data
        return representation
    
    
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id','jobrole_name']

class PreferenceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)    
    job_role = serializers.SlugRelatedField(
        queryset=Role.objects.all(), slug_field='jobrole_name'
    )
    
    class_category = serializers.SlugRelatedField(
        queryset=ClassCategory.objects.all(), slug_field='name',
        required=False
    )
    
    prefered_subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), many=True,
        required=False
    )
    
    teacher_job_type = serializers.PrimaryKeyRelatedField(
        queryset=TeacherJobType.objects.all(), many=True,
        required=False
    )
    
    class Meta:
        model = Preference
        fields = ['user', 'job_role', 'class_category', 'prefered_subject', 'teacher_job_type']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        representation['user'] = UserSerializer(instance.user).data
        
        representation['job_role'] = RoleSerializer(instance.job_role).data
        
        representation['class_category'] = ClassCategorySerializer(instance.class_category).data        
        
        representation['prefered_subject'] = None
        if instance.prefered_subject.exists():
            representation['prefered_subject'] = SubjectSerializer(instance.prefered_subject.first()).data
        
        representation['teacher_job_type'] = None
        if instance.teacher_job_type.exists():
            representation['teacher_job_type'] = TeacherJobTypeSerializer(instance.teacher_job_type.first()).data
        
        return representation

class TeacherSubjectSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), required=True)
    class Meta:
        model = TeacherSubject
        fields = '__all__'

        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        representation['subject'] = SubjectSerializer(instance.subject).data
        return representation
    
class TeacherClassCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassCategory
        fields = '__all__'

class TeacherExamResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherExamResult
        fields = '__all__'

    def validate(self, data):
        user = data.get('user')
        if user and TeacherExamResult.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user": "A teacherexamresult entry for this user already exists."})
        return data 
        
class JobPreferenceLocationSerializer(serializers.ModelSerializer):
    preference = serializers.PrimaryKeyRelatedField(queryset=Preference.objects.all(), required=False)
    class Meta:
        model = JobPreferenceLocation
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['preference'] = PreferenceSerializer(instance.preference).data
        return representation
    
    def validate_area(self, value):
        if JobPreferenceLocation.objects.filter(area=value).exists():
            raise serializers.ValidationError("A area with this name already exists.")
        return value   

class BasicProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False)
    bio = models.CharField(max_length=100, blank=True, null=True)    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    religion = models.CharField(max_length=15, blank=True, null=True)
    class Meta:
        model = BasicProfile
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        return representation

    def validate_mobile(self, value):
        if value:
            cleaned_value = re.sub(r'[^0-9]', '', value)
            if len(cleaned_value) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits.")
            if not cleaned_value.startswith(('6', '7', '8', '9')):
                raise serializers.ValidationError("Phone number must start with 6, 7, 8, or 9.")
            return cleaned_value
        return value
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'last_login', 'is_superuser', 'email', 'username',
            'Fname', 'Lname', 'is_staff', 'is_active', 'is_recruiter',
            'is_teacher', 'groups', 'user_permissions']

class TeacherJobTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherJobType
        fields = ['id', 'teacher_job_name']

