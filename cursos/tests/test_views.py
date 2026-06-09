from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from cursos.models import Curso, Inscricao, RelatorioIA


# --- Helpers ---

def criar_usuario(username='usuario_teste', is_staff=False):
    return User.objects.create_user(
        username=username, password='senha123', is_staff=is_staff
    )


def criar_curso(nome='Curso Teste'):
    return Curso.objects.create(
        nome=nome,
        imagem='cursos_imagens/test.jpg',
        resumo='Resumo teste',
        descricao='Descrição teste',
        preco=99.99,
    )


# --- Lista de Cursos ---

class ListaCursosViewTest(TestCase):
    def setUp(self):
        self.url = reverse('lista_cursos')

    def test_redireciona_usuario_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_retorna_200_para_usuario_autenticado(self):
        criar_usuario()
        self.client.login(username='usuario_teste', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_cursos_aparecem_no_contexto(self):
        criar_usuario()
        criar_curso('Django para Iniciantes')
        criar_curso('JavaScript Moderno')
        self.client.login(username='usuario_teste', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.context['cursos'].count(), 2)


# --- Detalhe do Curso ---

class DetalheCursoViewTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.curso = criar_curso()
        self.url = reverse('detalhe_curso', args=[self.curso.id])

    def test_retorna_200_para_usuario_anonimo(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_retorna_200_para_usuario_autenticado(self):
        self.client.login(username='usuario_teste', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_atualiza_dias_seguidos_na_primeira_visita_do_dia(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=timezone.now().date() - timedelta(days=1),
            dias_seguidos=3,
        )
        self.client.login(username='usuario_teste', password='senha123')
        self.client.get(self.url)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.dias_seguidos, 4)
        self.assertEqual(inscricao.ultima_interacao, timezone.now().date())

    def test_reinicia_streak_quando_dia_pulado(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=timezone.now().date() - timedelta(days=3),
            dias_seguidos=5,
        )
        self.client.login(username='usuario_teste', password='senha123')
        self.client.get(self.url)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.dias_seguidos, 1)

    def test_nao_atualiza_streak_se_ja_acessou_hoje(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=timezone.now().date(),
            dias_seguidos=7,
        )
        self.client.login(username='usuario_teste', password='senha123')
        self.client.get(self.url)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.dias_seguidos, 7)


# --- Ação no Curso (inscrição / conclusão) ---

class AcaoCursoViewTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.curso = criar_curso()
        self.url = reverse('acao_curso', args=[self.curso.id])
        self.client.login(username='usuario_teste', password='senha123')

    def test_cria_inscricao_quando_usuario_nao_inscrito(self):
        self.client.post(self.url)
        self.assertTrue(
            Inscricao.objects.filter(usuario=self.usuario, curso=self.curso).exists()
        )

    def test_nova_inscricao_tem_status_andamento(self):
        self.client.post(self.url)
        inscricao = Inscricao.objects.get(usuario=self.usuario, curso=self.curso)
        self.assertEqual(inscricao.status, 'andamento')

    def test_conclui_curso_quando_ja_inscrito(self):
        Inscricao.objects.create(
            usuario=self.usuario, curso=self.curso, status='andamento'
        )
        self.client.post(self.url)
        inscricao = Inscricao.objects.get(usuario=self.usuario, curso=self.curso)
        self.assertEqual(inscricao.status, 'concluido')

    def test_redireciona_para_detalhe_do_curso(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse('detalhe_curso', args=[self.curso.id]),
            fetch_redirect_response=False,
        )

    def test_redireciona_nao_autenticado(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)


# --- Perfil ---

class PerfilViewTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.url = reverse('perfil')

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_retorna_200_para_usuario_autenticado(self):
        self.client.login(username='usuario_teste', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_cursos_corretos(self):
        curso_a = criar_curso('Curso A')
        curso_b = criar_curso('Curso B')
        Inscricao.objects.create(usuario=self.usuario, curso=curso_a, status='andamento')
        Inscricao.objects.create(usuario=self.usuario, curso=curso_b, status='concluido')
        self.client.login(username='usuario_teste', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.context['cursos_andamento'].count(), 1)
        self.assertEqual(response.context['cursos_concluidos'].count(), 1)
        self.assertEqual(response.context['total_comprados'], 2)
        self.assertEqual(response.context['total_concluidos'], 1)


# --- Avaliação de Curso ---

class AvaliarCursoViewTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.curso = criar_curso()
        self.inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='concluido',
        )
        self.url = reverse('avaliar_curso', args=[self.inscricao.id])
        self.client.login(username='usuario_teste', password='senha123')

    def test_get_com_alterar_limpa_nota(self):
        self.inscricao.nota = 9
        self.inscricao.save()
        self.client.get(self.url + '?alterar=true')
        self.inscricao.refresh_from_db()
        self.assertIsNone(self.inscricao.nota)

    @patch('cursos.views.GeminiService')
    def test_post_salva_nota_e_pensamento(self, mock_gemini_class):
        mock_servico = MagicMock()
        mock_servico.gerar_relatorio.return_value = 'Relatório gerado pelo Gemini'
        mock_gemini_class.return_value = mock_servico

        self.client.post(self.url, {
            'nota': '8',
            'categorias': ['conteudo'],
            'pensamento': 'Excelente curso, aprendi muito!',
        })

        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.nota, 8)
        self.assertEqual(self.inscricao.pensamento, 'Excelente curso, aprendi muito!')

    @patch('cursos.views.GeminiService')
    def test_post_cria_relatorio_ia(self, mock_gemini_class):
        mock_servico = MagicMock()
        mock_servico.gerar_relatorio.return_value = 'Relatório gerado'
        mock_gemini_class.return_value = mock_servico

        self.client.post(self.url, {
            'nota': '7',
            'categorias': ['didatica'],
            'pensamento': 'Bom conteúdo mas poderia ser mais prático',
        })

        self.assertTrue(RelatorioIA.objects.filter(inscricao=self.inscricao).exists())

    @patch('cursos.views.GeminiService')
    def test_post_sem_categoria_exibe_erro(self, mock_gemini_class):
        response = self.client.post(self.url, {
            'nota': '8',
            'pensamento': 'Ótimo curso',
        }, follow=True)
        self.assertFalse(RelatorioIA.objects.filter(inscricao=self.inscricao).exists())

    @patch('cursos.views.GeminiService')
    def test_post_sem_pensamento_exibe_erro(self, mock_gemini_class):
        response = self.client.post(self.url, {
            'nota': '8',
            'categorias': ['conteudo'],
        }, follow=True)
        self.assertFalse(RelatorioIA.objects.filter(inscricao=self.inscricao).exists())


# --- Solicitação de Reembolso pelo Aluno ---

class SolicitarReembolsoAlunoViewTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.curso = criar_curso()
        self.inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
        )
        self.url = reverse('solicitar_reembolso_aluno', args=[self.inscricao.id])
        self.client.login(username='usuario_teste', password='senha123')

    def test_get_exibe_pagina_de_confirmacao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_redireciona_se_status_nao_e_andamento(self):
        self.inscricao.status = 'concluido'
        self.inscricao.save()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('perfil'), fetch_redirect_response=False)

    def test_post_muda_status_para_reembolsado(self):
        self.client.post(self.url)
        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.status, 'reembolsado')

    def test_post_redireciona_para_perfil(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('perfil'), fetch_redirect_response=False)


# --- Dashboard Financeiro (Staff) ---

class DashboardFinanceiroViewTest(TestCase):
    def setUp(self):
        self.url = reverse('admin_dashboard_financeiro')
        self.staff = criar_usuario('admin_user', is_staff=True)
        self.aluno = criar_usuario('aluno_user')

    def test_redireciona_usuario_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_usuario_nao_staff(self):
        self.client.login(username='aluno_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_retorna_200_para_staff(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_metricas(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertIn('taxa_abandono', response.context)
        self.assertIn('taxa_retencao', response.context)
        self.assertIn('taxa_cancelamento', response.context)

    def test_aplicar_strikes_e_chamado_ao_carregar_dashboard(self):
        curso = criar_curso()
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=curso,
            status='andamento',
            ultima_interacao=timezone.now().date() - timedelta(days=20),
        )
        self.client.login(username='admin_user', password='senha123')
        self.client.get(self.url)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'abandonado')


# --- Processar Reembolso (Staff) ---

class ProcessarReembolsoViewTest(TestCase):
    def setUp(self):
        self.staff = criar_usuario('admin_user', is_staff=True)
        self.aluno = criar_usuario('aluno_user')
        self.curso = criar_curso()
        self.inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status='andamento',
        )
        self.url = reverse('admin_processar_reembolso', args=[self.inscricao.id])

    def test_redireciona_nao_staff(self):
        self.client.login(username='aluno_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_exibe_confirmacao_para_staff(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_processa_reembolso(self):
        self.client.login(username='admin_user', password='senha123')
        self.client.post(self.url)
        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.status, 'reembolsado')

    def test_post_redireciona_para_dashboard(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse('admin_dashboard_financeiro'),
            fetch_redirect_response=False,
        )


# --- Relatórios de IA (Staff) ---

class RelatoriosViewTest(TestCase):
    def setUp(self):
        self.url = reverse('relatorios')
        self.staff = criar_usuario('admin_user', is_staff=True)
        criar_usuario('aluno_user')

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redireciona_nao_staff(self):
        self.client.login(username='aluno_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_retorna_200_para_staff(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# --- Detalhe de Relatório (Staff) ---

class DetalheRelatorioViewTest(TestCase):
    def setUp(self):
        self.staff = criar_usuario('admin_user', is_staff=True)
        self.aluno = criar_usuario('aluno_user')
        self.curso = criar_curso()
        self.inscricao = Inscricao.objects.create(
            usuario=self.aluno, curso=self.curso, status='concluido'
        )
        self.relatorio = RelatorioIA.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            inscricao=self.inscricao,
            categorias='conteudo',
            comentario_original='Bom curso',
            relatorio_gerado='Relatório detalhado aqui',
        )
        self.url = reverse('detalhe_relatorio', args=[self.relatorio.id])

    def test_redireciona_nao_staff(self):
        self.client.login(username='aluno_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_retorna_200_para_staff(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_relatorio_correto(self):
        self.client.login(username='admin_user', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.context['relatorio'], self.relatorio)
