from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

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

    def test_relatorio_remove_marcadores_markdown_na_exibicao(self):
        self.relatorio.relatorio_gerado = "**1. Identificação**\n- **Aluno:** aluno"
        self.relatorio.save()
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("detalhe_relatorio", args=[self.relatorio.id]))

        self.assertContains(resposta, "1. Identificação")
        self.assertContains(resposta, "Aluno: aluno")
        self.assertNotContains(resposta, "**Aluno:**")


class FuncionalidadesCursosTests(TestCase):
    def setUp(self):
        self.aluno = User.objects.create_user(username="aluno_funcional", password="senha-teste")
        self.admin = User.objects.create_superuser(username="admin_funcional", password="senha-teste")
        self.curso = Curso.objects.create(
            nome="Curso de Vendas",
            resumo="Aprenda vendas na pratica.",
            descricao="Descricao completa do curso de vendas.",
            preco=99.90,
        )
        self.outro_curso = Curso.objects.create(
            nome="Curso de Gestao",
            resumo="Gestao para pequenos negocios.",
            descricao="Descricao completa do curso de gestao.",
            preco=149.90,
        )

    def test_lista_e_detalhe_exibem_cursos_com_preco_e_descricao(self):
        self.client.force_login(self.aluno)

        resposta_lista = self.client.get(reverse("lista_cursos"))
        resposta_detalhe = self.client.get(reverse("detalhe_curso", args=[self.curso.id]))

        self.assertContains(resposta_lista, "Curso de Vendas")
        self.assertContains(resposta_lista, "Aprenda vendas na pratica.")
        self.assertContains(resposta_lista, "R$")
        self.assertContains(resposta_detalhe, "Descricao completa do curso de vendas.")

    def test_usuario_pode_se_inscrever_em_varios_cursos(self):
        self.client.force_login(self.aluno)

        self.client.get(reverse("acao_curso", args=[self.curso.id]))
        self.client.get(reverse("acao_curso", args=[self.outro_curso.id]))

        inscricoes = Inscricao.objects.filter(usuario=self.aluno)
        self.assertEqual(inscricoes.count(), 2)
        self.assertTrue(inscricoes.filter(curso=self.curso, status="andamento").exists())
        self.assertTrue(inscricoes.filter(curso=self.outro_curso, status="andamento").exists())

    def test_usuario_conclui_curso_depois_de_iniciar(self):
        self.client.force_login(self.aluno)

        self.client.get(reverse("acao_curso", args=[self.curso.id]))
        self.client.get(reverse("acao_curso", args=[self.curso.id]))

        inscricao = Inscricao.objects.get(usuario=self.aluno, curso=self.curso)
        self.assertEqual(inscricao.status, "concluido")

    def test_perfil_conta_cursos_comprados_e_finalizados(self):
        Inscricao.objects.create(usuario=self.aluno, curso=self.curso, status="concluido")
        Inscricao.objects.create(usuario=self.aluno, curso=self.outro_curso, status="andamento")
        curso_reembolsado = Curso.objects.create(nome="Curso Reembolsado")
        Inscricao.objects.create(usuario=self.aluno, curso=curso_reembolsado, status="reembolsado")
        self.client.force_login(self.aluno)

        resposta = self.client.get(reverse("perfil"))

        self.assertEqual(resposta.context["total_comprados"], 2)
        self.assertEqual(resposta.context["total_concluidos"], 1)

    def test_conta_tempo_que_usuario_esta_no_curso(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="andamento",
        )
        Inscricao.objects.filter(id=inscricao.id).update(
            data_inscricao=timezone.now() - timedelta(days=4)
        )

        inscricao.refresh_from_db()

        self.assertEqual(inscricao.dias_em_andamento, 4)

    def test_acesso_diario_incrementa_dias_seguidos(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="andamento",
            ultima_interacao=timezone.now().date() - timedelta(days=1),
            dias_seguidos=2,
        )
        self.client.force_login(self.aluno)

        self.client.get(reverse("detalhe_curso", args=[self.curso.id]))

        inscricao.refresh_from_db()
        self.assertEqual(inscricao.dias_seguidos, 3)
        self.assertEqual(inscricao.ultima_interacao, timezone.now().date())

    def test_acesso_diario_reinicia_se_usuario_pulou_dia(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="andamento",
            ultima_interacao=timezone.now().date() - timedelta(days=3),
            dias_seguidos=5,
        )
        self.client.force_login(self.aluno)

        self.client.get(reverse("detalhe_curso", args=[self.curso.id]))

        inscricao.refresh_from_db()
        self.assertEqual(inscricao.dias_seguidos, 1)

    def test_usuario_so_avalia_curso_concluido(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="andamento",
        )
        self.client.force_login(self.aluno)

        self.client.post(reverse("avaliar_curso", args=[inscricao.id]), {"nota": "10"})

        inscricao.refresh_from_db()
        self.assertIsNone(inscricao.nota)
        self.assertFalse(RelatorioIA.objects.filter(inscricao=inscricao).exists())

    @patch("cursos.views.gerar_relatorio_com_gemini", return_value="Relatorio gerado pela IA")
    def test_espaco_para_pensamento_salva_avaliacao_e_relatorio_ia(self, gerar_relatorio):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="concluido",
        )
        self.client.force_login(self.aluno)

        resposta = self.client.post(
            f"{reverse('avaliar_curso', args=[inscricao.id])}?next=detalhe",
            {
                "nota": "9",
                "categorias": ["Conteudo do curso", "Organizacao do site"],
                "pensamento": "Gostei do conteudo e achei o site organizado.",
            },
        )

        inscricao.refresh_from_db()
        relatorio = RelatorioIA.objects.get(inscricao=inscricao)
        self.assertRedirects(resposta, reverse("detalhe_curso", args=[self.curso.id]))
        self.assertEqual(inscricao.nota, 9)
        self.assertEqual(inscricao.pensamento, "Gostei do conteudo e achei o site organizado.")
        self.assertEqual(relatorio.relatorio_gerado, "Relatorio gerado pela IA")
        self.assertEqual(relatorio.categorias, "Conteudo do curso, Organizacao do site")
        gerar_relatorio.assert_called_once()

    def test_pensamento_do_aluno_aparece_no_detalhe_do_curso(self):
        Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="concluido",
            nota=10,
            pensamento="Curso muito util.",
        )

        resposta = self.client.get(reverse("detalhe_curso", args=[self.curso.id]))

        self.assertContains(resposta, "Curso muito util.")
        self.assertContains(resposta, "10/10")

    def test_reembolso_do_aluno_muda_status_para_reembolsado(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="andamento",
        )
        self.client.force_login(self.aluno)

        resposta = self.client.post(reverse("solicitar_reembolso_aluno", args=[inscricao.id]))

        inscricao.refresh_from_db()
        self.assertRedirects(resposta, reverse("perfil"))
        self.assertEqual(inscricao.status, "reembolsado")

    def test_curso_concluido_nao_pode_ser_reembolsado_pelo_aluno(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="concluido",
        )
        self.client.force_login(self.aluno)

        self.client.post(reverse("solicitar_reembolso_aluno", args=[inscricao.id]))

        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, "concluido")

    def test_dashboard_calcula_retencao_cancelamento_e_abandono(self):
        usuario_recorrente = User.objects.create_user(username="recorrente")
        usuario_unico = User.objects.create_user(username="unico")
        usuario_reembolsado = User.objects.create_user(username="reembolsado")
        curso_extra = Curso.objects.create(nome="Curso Extra")
        curso_cancelado = Curso.objects.create(nome="Curso Cancelado")

        Inscricao.objects.create(usuario=usuario_recorrente, curso=self.curso, status="concluido")
        Inscricao.objects.create(usuario=usuario_recorrente, curso=self.outro_curso, status="andamento")
        inscricao_abandonada = Inscricao.objects.create(
            usuario=usuario_unico,
            curso=curso_extra,
            status="andamento",
            ultima_interacao=timezone.now().date() - timedelta(days=16),
        )
        Inscricao.objects.create(
            usuario=usuario_reembolsado,
            curso=curso_cancelado,
            status="reembolsado",
        )
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse("admin_dashboard_financeiro"))

        inscricao_abandonada.refresh_from_db()
        self.assertEqual(inscricao_abandonada.status, "abandonado")
        self.assertEqual(resposta.context["taxa_retencao"], 50.0)
        self.assertEqual(resposta.context["taxa_abandono"], 33.33)
        self.assertEqual(resposta.context["taxa_cancelamento"], 25.0)

    def test_admin_processa_reembolso_de_inscricao_ativa(self):
        inscricao = Inscricao.objects.create(
            usuario=self.aluno,
            curso=self.curso,
            status="concluido",
        )
        self.client.force_login(self.admin)

        resposta = self.client.post(reverse("admin_processar_reembolso", args=[inscricao.id]))

        inscricao.refresh_from_db()
        self.assertRedirects(resposta, reverse("admin_dashboard_financeiro"))
        self.assertEqual(inscricao.status, "reembolsado")
