from django.shortcuts import render, redirect, get_object_or_404
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

def detalhe_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscricao = None
    
    if request.user.is_authenticated:
        inscricao = Inscricao.objects.filter(usuario=request.user, curso=curso).first()
        
    return render(request, 'cursos/detalhe_curso.html', {
        'curso': curso,
        'inscricao': inscricao
    })

@login_required
def acao_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscricao = Inscricao.objects.filter(usuario=request.user, curso=curso).first()
    
    if not inscricao:
        Inscricao.objects.create(usuario=request.user, curso=curso, status='andamento')
    elif inscricao.status == 'andamento':
        inscricao.status = 'concluido'
        inscricao.save()
        
    return redirect('detalhe_curso', curso_id=curso.id)