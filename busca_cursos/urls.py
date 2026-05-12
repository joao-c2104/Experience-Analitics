from django.urls import path
from . import views

urlpatterns = [
    path('buscar/', views.buscar_cursos, name='buscar_cursos'),
]
