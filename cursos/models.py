from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    
    def __str__(self):
        return f"{self.usuario.username} - {self.curso.nome}"