from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"{self.usuario.username} - {self.curso.nome}"