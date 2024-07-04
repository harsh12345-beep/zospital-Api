from django.urls import path
from .views import *

urlpatterns = [
    path('api/create_pdf/', create_pdf_api, name='create_pdf_api'),
    path('', pdf_form, name='pdf_form'),
]