from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Curso, Inscricao

@login_required
def lista_cursos(request):
    cursos = Curso.objects.all()
    return render(request, 'cursos/lista_cursos.html', {'cursos': cursos})

@login_required
def perfil(request):
    minhas_inscricoes = Inscricao.objects.filter(usuario=request.user)
    
    cursos_andamento = minhas_inscricoes.filter(status='andamento')
    cursos_concluidos = minhas_inscricoes.filter(status='concluido')
    
    return render(request, 'cursos/perfil.html', {
        'cursos_andamento': cursos_andamento,
        'cursos_concluidos': cursos_concluidos
    })

def fazer_logout(request):
    logout(request)
    return redirect('lista_cursos')