from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cursos, name='lista_cursos'),
    path('perfil/', views.perfil, name='perfil'),
    path('sair/', views.fazer_logout, name='sair'),
    path('curso/<int:curso_id>/', views.detalhe_curso, name='detalhe_curso'),
    path('curso/<int:curso_id>/acao/', views.acao_curso, name='acao_curso'),
    path('inscricao/<int:inscricao_id>/avaliar/', views.avaliar_curso, name='avaliar_curso'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('relatorios/<int:relatorio_id>/', views.detalhe_relatorio, name='detalhe_relatorio'),
]
