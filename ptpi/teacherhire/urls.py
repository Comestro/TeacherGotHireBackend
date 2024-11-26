from django.contrib import admin
from django.urls import path, include
from teacherhire.views import *
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r"admin/teacherexperience",TeacherExperiencesViewSet)
router.register(r"admin/teacherqualification",TeacherQualificationViewSet)
router.register(r"admin/skill",SkillViewSet)
router.register(r"admin/teacherskill",TeacherSkillViewSet),
router.register(r"admin/subject",SubjectViewSet),
router.register(r"admin/classcategory",ClassCategoryViewSet),
router.register(r"admin/teacher",TeacherViewSet),
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'admin/educationalQulification', EducationalQulificationViewSet)
router.register(r'admin/teachersAddress', TeachersAddressViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/',include('rest_framework.urls',namespace='rest_framework')),
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view()),
    #subjects  
    path('admin/subject/view/', SubjectViewSet.as_view({'get': 'list'}), name='view-subject'),
    path('admin/subject/create/', SubjectCreateView.as_view(), name='subject-create'),
    path('admin/subject/<int:pk>/', SubjectDeleteView.as_view(), name='subject-delete'),
    #teacher  
    path('admin/teacher/view/', TeacherViewSet.as_view({'get': 'list'}), name='view-teacher'),
    path('admin/teacher/create/', TeacherCreateView.as_view(), name='teacher-create'),
    path('admin/teacher/<int:pk>/', TeacherDeleteView.as_view(), name='teacher-delete'),
    #classcategory
    path('admin/classcategory/view/', ClassCategoryViewSet.as_view({'get': 'list'}), name='view-classcategory'),
    path('admin/classcategory/create/', ClassCategoryCreateView.as_view(), name='classcategory-create'),
    path('admin/classcategory/<int:pk>/', ClassCategoryDeleteView.as_view(), name='classcategory-delete'),  
    #skill     
    path('admin/skill/view/', SkillViewSet.as_view({'get': 'list'}), name='skill'), 
    path('admin/skill/create/', SkillCreateView.as_view(), name='skill-create'),    
    path('admin/skill/<int:pk>/', SkillDelete.as_view(), name="skill-delete"),
    path('teacherSkill/', TeacherSkillViewSet.as_view({'get' : 'list'}), name='teacherskill'), 
    # teacherqualification
    path('admin/teacherqualification/create/', TeacherQualificationCreateView.as_view(), name='teacherqualification-create'),
    path('admin/teacherQualification/view/', TeacherQualificationViewSet.as_view({'get': 'list'}), name='view-teacherQualification'),
    path('admin/teacherQualification/<int:pk>/', TeacherQualificationDeleteView.as_view(), name='teacherQualification-delete'),

    # teacherexperiences  
    path('admin/teacherexperiences/create/',TeacherExperiencesCreateView.as_view(), name='teacherexperiences-create'),
    path('admin/teacherexperiences/view/', TeacherExperiencesViewSet.as_view({'get': 'list'}), name='view-teacherexperiences'),
    path('admin/teacherexperiences/<int:pk>/',TeacherExperiencesDeleteView.as_view(), name='teacherexperiences-delete'),

    # EducationalQulification
    # path('edQulification/view/', EducationalQulificationViewSet.as_view({'get':'list'}), name='edQulification'),    
    path('edQulification/create/', EducationalQulificationCreateView.as_view(), name='edQulification-create'),
    path('teachersAddress/view/', TeachersAddressViewSet.as_view({'get':'list'}), name='teacherAddress'),    
    path('teachersAddress/create/', TeachersAddressCreateView.as_view(), name='teacherAddress-create'),    
]
