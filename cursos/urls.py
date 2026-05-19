from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cursos, name='lista_cursos'),
    path('perfil/', views.perfil, name='perfil'),
    path('sair/', views.fazer_logout, name='sair'),
]