from django.db import models

class Curso(models.Model):
    nome = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to='cursos_imagens/')
    
    def __str__(self):
        return self.nome