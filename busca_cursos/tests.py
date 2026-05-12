from django.test import TestCase
from django.urls import reverse
from cursos.models import Curso


class BuscaCursosViewTest(TestCase):

    def setUp(self):
        Curso.objects.create(nome="Excel para Iniciantes")
        Curso.objects.create(nome="Marketing Digital")
        Curso.objects.create(nome="Gestão Financeira")

    def test_busca_sem_termo_retorna_pagina(self):
        """Acessar /buscar/ sem termo exibe o estado inicial."""
        response = self.client.get(reverse('buscar_cursos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buscar por palavra-chave')

    def test_busca_com_termo_encontra_curso(self):
        """Buscar 'Excel' deve retornar o curso correspondente."""
        response = self.client.get(reverse('buscar_cursos'), {'q': 'Excel'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Excel para Iniciantes')
        self.assertNotContains(response, 'Marketing Digital')

    def test_busca_case_insensitive(self):
        """A busca deve ignorar maiúsculas/minúsculas."""
        response = self.client.get(reverse('buscar_cursos'), {'q': 'marketing'})
        self.assertContains(response, 'Marketing Digital')

    def test_busca_sem_resultados(self):
        """Busca por termo inexistente deve exibir mensagem de vazio."""
        response = self.client.get(reverse('buscar_cursos'), {'q': 'Python'})
        self.assertContains(response, 'Nenhum curso encontrado')

    def test_busca_parcial(self):
        """Busca parcial deve encontrar cursos que contenham o trecho."""
        response = self.client.get(reverse('buscar_cursos'), {'q': 'financeira'})
        self.assertContains(response, 'Gestão Financeira')

    def test_contexto_retorna_query_e_total(self):
        """O contexto deve conter o termo buscado e o total de resultados."""
        response = self.client.get(reverse('buscar_cursos'), {'q': 'Digital'})
        self.assertEqual(response.context['query'], 'Digital')
        self.assertEqual(response.context['total_resultados'], 1)
