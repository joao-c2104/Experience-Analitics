from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Curso, Inscricao, RelatorioIA


class AcessoRelatoriosIATests(TestCase):
    def setUp(self):
        self.aluno = User.objects.create_user(username="aluno", password="senha-teste")
        self.admin = User.objects.create_superuser(username="admin", password="senha-teste")
        self.curso = Curso.objects.create(nome="Curso teste")
        self.inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="concluido",
        )
        self.relatorio = RelatorioIA.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            inscricao=self.inscricao,
            categorias="Conteúdo do curso",
            comentario_original="Gostei do curso.",
            relatorio_gerado="Relatório privado.",
        )

    def test_aluno_nao_ve_link_para_relatorios(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("lista_cursos"))

        self.assertNotContains(resposta, reverse("relatorios"))

    def test_aluno_nao_acessa_lista_de_relatorios(self):
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("relatorios"))

        self.assertRedirects(
            resposta,
            f"{reverse('admin:login')}?next={reverse('relatorios')}",
            fetch_redirect_response=False,
        )

    def test_aluno_nao_acessa_detalhe_de_relatorio(self):
        self.client.force_login(self.aluno)
        url = reverse("detalhe_relatorio", args=[self.relatorio.id])

        resposta = self.client.get(url)

        self.assertRedirects(
            resposta,
            f"{reverse('admin:login')}?next={url}",
            fetch_redirect_response=False,
        )

    def test_administrador_acessa_relatorio(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("detalhe_relatorio", args=[self.relatorio.id]))

        self.assertContains(resposta, "Relatório privado.")
