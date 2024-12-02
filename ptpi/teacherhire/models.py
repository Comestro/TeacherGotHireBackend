from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser

class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Teacher", "Teacher"),
    ]
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default="Teacher")

class TeachersAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('current', 'Current'),
        ('permanent', 'Permanent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES,null=True, blank=True)
    state = models.CharField(max_length=100, default='Bihar',null=True, blank=True)
    division = models.CharField(max_length=100,null=True, blank=True)
    district = models.CharField(max_length=100,null=True, blank=True)
    block = models.CharField(max_length=100,null=True, blank=True)
    village = models.CharField(max_length=100,null=True, blank=True)
    area = models.TextField(null=True, blank=True)
    pincode = models.CharField(max_length=6,null=True, blank=True)

    def __str__(self):
        return f'{self.address_type} address of {self.user.username}'

# Create your models here.
class Subject(models.Model):
    subject_name = models.CharField(max_length=100,null=True, blank=True)
    subject_description = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.subject_name

class ClassCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,null=True, blank=True,
        choices=[
            ("Nursery to U.K.G","Nursery to U.K.G"),
            ("1 to 5","1 to 5"),
            ("6 to 8","6 to 8"),
            ("9 to 10","9 to 10"),
            ("10 to 12","10 to 12")
        ]
        )
    def __str__(self):
        return self.name
class Teacher(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    fullname = models.	CharField(max_length=255,null=True, blank=True)
    gender	 = models.CharField(
        max_length=10,null=True, blank=True,
        choices=[
            ("Female","Female"),
            ("Male","Male"),
            ("other","other"),
        ])
    religion = models.	CharField(max_length=100,null=True, blank=True)
    nationality = models. CharField(
        max_length=100,null=True, blank=True,
        choices=[
            ("Indian","Indian"),
            ("other","other"),
        ]
        )
    image = models.	ImageField(upload_to='images/',null=True, blank=True)
    aadhar_no = models.CharField(max_length=12, unique=True,null=True, blank=True)
    phone = models.	CharField(max_length=15,null=True, blank=True)
    alternate_phone = models. CharField(max_length=15, null=True, blank=True)
    verified = models.	BooleanField(default=False)
    class_categories = models.ForeignKey(ClassCategory, on_delete=models.CASCADE,null=True, blank=True)
    rating = models. DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    availability_status = models.CharField(max_length=50, default='Available')
    def __str__(self):
        return self.user

class EducationalQualification(models.Model):	
   name = models.CharField(max_length=255, unique=True,null=True, blank=True)
   description = models.TextField(null=True, blank=True)

   def __str__(self):
        return self.name

class TeacherQualification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    qualification = models.ForeignKey(EducationalQualification, on_delete=models.CASCADE,null=True, blank=True)
    institution = models.CharField(max_length=225,null=True, blank=True)  
    year_of_passing = models.PositiveIntegerField(null=True, blank=True)  
    grade_or_percentage = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.user

class TeacherExperiences(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    institution = models.CharField(max_length=255,null=True, blank=True)
    role = models.CharField(max_length=255,null=True, blank=True)
    start_date	= models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    achievements = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user

class Skill(models.Model):
   name = models.CharField(max_length=255, unique=True,null=True, blank=True)
   description = models.TextField(null=True, blank=True)

   def __str__(self):
        return self.name

class Level(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)
    description =models.CharField(max_length=2000,null=True, blank=True)
    def __str__(self):
        return self.name
    
class Question(models.Model):
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE)
    level = models.ForeignKey(Level,on_delete=models.CASCADE)
    classCategory = models.ForeignKey(ClassCategory,on_delete=models.CASCADE, default=1)
    text = models.CharField(max_length=2000,)
    options = models.JSONField()
    correct_options = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        super().clean()
        if self.correct_option < 1 or self.correct_option > len(self.options):
            raise models.ValidationError({
                'correct_option': f'Correct option must be between 1 and {len(self.options)}.'
            })
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.subject.name} - {self.level.name} - {self.text[:50]}"


class TeacherSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.CharField(max_length=100, null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.user
class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_teacher = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"