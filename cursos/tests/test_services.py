from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from cursos.models import Curso
from cursos.services.gemini_service import GeminiService


def criar_usuario(username='usuario_teste'):
    return User.objects.create_user(username=username, password='senha123')


def criar_curso(nome='Curso Teste'):
    return Curso.objects.create(
        nome=nome,
        imagem='cursos_imagens/test.jpg',
        resumo='Resumo',
        descricao='Descrição',
        preco=99.99,
    )


class GeminiServiceTest(TestCase):
    @override_settings(GEMINI_API_KEY='')
    def test_init_levanta_erro_sem_api_key(self):
        with self.assertRaises(ValueError) as ctx:
            GeminiService()
        self.assertIn('GEMINI_API_KEY', str(ctx.exception))

    @override_settings(GEMINI_API_KEY='chave-falsa', GEMINI_MODEL='gemini-test')
    @patch('cursos.services.gemini_service.genai')
    def test_gerar_relatorio_retorna_texto_do_gemini(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value.__enter__.return_value = mock_client
        mock_client.models.generate_content.return_value.text = 'Relatório completo gerado'

        servico = GeminiService()
        resultado = servico.gerar_relatorio(
            usuario=criar_usuario(),
            curso=criar_curso(),
            categorias=['conteudo', 'didatica'],
            comentario='Curso muito bom!',
            nota=9,
        )

        self.assertEqual(resultado, 'Relatório completo gerado')

    @override_settings(GEMINI_API_KEY='chave-falsa', GEMINI_MODEL='gemini-test')
    @patch('cursos.services.gemini_service.genai')
    def test_gerar_relatorio_levanta_erro_quando_gemini_retorna_vazio(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value.__enter__.return_value = mock_client
        mock_client.models.generate_content.return_value.text = ''

        servico = GeminiService()
        with self.assertRaises(ValueError) as ctx:
            servico.gerar_relatorio(
                usuario=criar_usuario(),
                curso=criar_curso(),
                categorias=['conteudo'],
                comentario='Comentário qualquer',
            )
        self.assertIn('Gemini', str(ctx.exception))

    @override_settings(GEMINI_API_KEY='chave-falsa', GEMINI_MODEL='gemini-test')
    @patch('cursos.services.gemini_service.genai')
    def test_gerar_relatorio_sem_nota_usa_nao_informada(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value.__enter__.return_value = mock_client
        mock_client.models.generate_content.return_value.text = 'Relatório sem nota'

        servico = GeminiService()
        resultado = servico.gerar_relatorio(
            usuario=criar_usuario(),
            curso=criar_curso(),
            categorias=['conteudo'],
            comentario='Comentário sem nota',
            nota=None,
        )

        prompt_usado = mock_client.models.generate_content.call_args[1]['contents']
        self.assertIn('Não informada', prompt_usado)
        self.assertEqual(resultado, 'Relatório sem nota')
