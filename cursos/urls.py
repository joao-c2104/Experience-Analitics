from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_cursos, name='lista_cursos'),
    path('logout/', views.fazer_logout, name='sair'),
    path('curso/<int:curso_id>/', views.detalhe_curso, name='detalhe_curso'),
    path('curso/<int:curso_id>/acao/', views.acao_curso, name='acao_curso'),
    path('perfil/', views.perfil, name='perfil'),
    path('inscricao/<int:inscricao_id>/avaliar/', views.avaliar_curso, name='avaliar_curso'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('relatorios/<int:relatorio_id>/', views.detalhe_relatorio, name='detalhe_relatorio'),
    path('admin/dashboard/', views.dashboard_financeiro, name='admin_dashboard_financeiro'),
    path('admin/reembolso/<int:order_id>/', views.processar_reembolso, name='admin_processar_reembolso'),
    path('curso/reembolso/<int:inscricao_id>/', views.solicitar_reembolso_aluno, name='solicitar_reembolso_aluno'),
]
