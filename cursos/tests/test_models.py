from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from cursos.models import Curso, Inscricao, RelatorioIA


def criar_usuario(username='usuario_teste'):
    return User.objects.create_user(username=username, password='senha123')


def criar_curso(nome='Curso Teste'):
    return Curso.objects.create(
        nome=nome,
        imagem='cursos_imagens/test.jpg',
        resumo='Resumo do curso de teste',
        descricao='Descrição detalhada do curso de teste',
        preco=99.99,
    )


class CursoModelTest(TestCase):
    def test_str_retorna_nome_do_curso(self):
        curso = criar_curso('Python Avançado')
        self.assertEqual(str(curso), 'Python Avançado')


class InscricaoModelTest(TestCase):
    def setUp(self):
        self.usuario = criar_usuario()
        self.curso = criar_curso()

    def test_str_retorna_usuario_e_curso(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
        )
        esperado = f'{self.usuario.username} - {self.curso.nome}'
        self.assertEqual(str(inscricao), esperado)

    def test_dias_em_andamento_retorna_pelo_menos_um(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
        )
        self.assertGreaterEqual(inscricao.dias_em_andamento, 1)

    def test_acessado_hoje_verdadeiro_quando_interagiu_hoje(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            ultima_interacao=timezone.now().date(),
        )
        self.assertTrue(inscricao.acessado_hoje)

    def test_acessado_hoje_falso_quando_interagiu_ontem(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            ultima_interacao=timezone.now().date() - timedelta(days=1),
        )
        self.assertFalse(inscricao.acessado_hoje)

    def test_acessado_hoje_falso_quando_nunca_interagiu(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            ultima_interacao=None,
        )
        self.assertFalse(inscricao.acessado_hoje)

    def test_aplicar_strikes_marca_abandonado_por_inatividade(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=timezone.now().date() - timedelta(days=16),
        )
        Inscricao.aplicar_strikes()
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'abandonado')

    def test_aplicar_strikes_nao_altera_interacao_recente(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=timezone.now().date() - timedelta(days=5),
        )
        Inscricao.aplicar_strikes()
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'andamento')

    def test_aplicar_strikes_nao_altera_cursos_concluidos(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='concluido',
            ultima_interacao=timezone.now().date() - timedelta(days=30),
        )
        Inscricao.aplicar_strikes()
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'concluido')

    def test_aplicar_strikes_sem_interacao_e_inscricao_antiga(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='andamento',
            ultima_interacao=None,
        )
        Inscricao.objects.filter(id=inscricao.id).update(
            data_inscricao=timezone.now() - timedelta(days=20)
        )
        Inscricao.aplicar_strikes()
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'abandonado')

    def test_aplicar_strikes_nao_altera_reembolsados(self):
        inscricao = Inscricao.objects.create(
            usuario=self.usuario,
            curso=self.curso,
            status='reembolsado',
            ultima_interacao=timezone.now().date() - timedelta(days=30),
        )
        Inscricao.aplicar_strikes()
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, 'reembolsado')


class RelatorioIAModelTest(TestCase):
    def test_str_retorna_usuario_e_curso(self):
        usuario = criar_usuario()
        curso = criar_curso()
        inscricao = Inscricao.objects.create(usuario=usuario, curso=curso)
        relatorio = RelatorioIA.objects.create(
            usuario=usuario,
            curso=curso,
            inscricao=inscricao,
            categorias='conteudo, didatica',
            comentario_original='Muito bom',
            relatorio_gerado='Relatório completo aqui',
        )
        esperado = f'Relatório de {usuario.username} - {curso.nome}'
        self.assertEqual(str(relatorio), esperado)
