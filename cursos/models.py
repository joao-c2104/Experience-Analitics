from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Curso(models.Model):
    nome = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to='cursos_imagens/')
    resumo = models.CharField(max_length=250, default="Resumo do curso...")
    descricao = models.TextField(default="Descrição detalhada do curso...")
    preco = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    def __str__(self):
        return self.nome
    
class Inscricao(models.Model):
    STATUS_CHOICES = (
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('abandonado', 'Abandonado'),
        ('reembolsado', 'Reembolsado'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='andamento')
    data_inscricao = models.DateTimeField(auto_now_add=True)
    nota = models.IntegerField(null=True, blank=True)
    ultima_interacao = models.DateField(null=True, blank=True)
    dias_seguidos = models.IntegerField(default=0)
    pensamento = models.TextField(null=True, blank=True)

    @property
    def dias_em_andamento(self):
        agora = timezone.now()
        diferenca = agora - self.data_inscricao
        return max(1, diferenca.days)

    @property
    def acessado_hoje(self):
        if self.ultima_interacao:
            return self.ultima_interacao == timezone.now().date()
        return False

    @classmethod
    def aplicar_strikes(cls):
        hoje = timezone.now().date()
        limite_inatividade = hoje - timedelta(days=15)
        cls.objects.filter(
            status='andamento'
        ).filter(
            Q(ultima_interacao__lte=limite_inatividade) |
            Q(ultima_interacao__isnull=True, data_inscricao__date__lte=limite_inatividade)
        ).update(status='abandonado')

    def __str__(self):
        return f"{self.usuario.username} - {self.curso.nome}"


class RelatorioIA(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name="relatorios_ia")
    categorias = models.CharField(max_length=255)
    comentario_original = models.TextField()
    relatorio_gerado = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Relatório de {self.usuario.username} - {self.curso.nome}"
