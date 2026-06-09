from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaCursosView.as_view(), name='lista_cursos'),
    path('logout/', views.FazerLogoutView.as_view(), name='sair'),
    path('curso/<int:curso_id>/', views.DetalheCursoView.as_view(), name='detalhe_curso'),
    path('curso/<int:curso_id>/acao/', views.AcaoCursoView.as_view(), name='acao_curso'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('inscricao/<int:inscricao_id>/avaliar/', views.AvaliarCursoView.as_view(), name='avaliar_curso'),
    path('relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
    path('relatorios/<int:relatorio_id>/', views.DetalheRelatorioView.as_view(), name='detalhe_relatorio'),
    path('admin/dashboard/', views.DashboardFinanceiroView.as_view(), name='admin_dashboard_financeiro'),
    path('admin/reembolso/<int:order_id>/', views.ProcessarReembolsoView.as_view(), name='admin_processar_reembolso'),
    path('curso/reembolso/<int:inscricao_id>/', views.SolicitarReembolsoAlunoView.as_view(), name='solicitar_reembolso_aluno'),
]
