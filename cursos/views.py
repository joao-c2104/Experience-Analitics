from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Curso, Inscricao
from django.utils import timezone
from datetime import timedelta

@login_required
def lista_cursos(request):
    cursos = Curso.objects.all()
    return render(request, 'cursos/lista_cursos.html', {'cursos': cursos})

def fazer_logout(request):
    logout(request)
    return redirect('lista_cursos')

def detalhe_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscricao = None
    
    if request.user.is_authenticated:
        inscricao = Inscricao.objects.filter(usuario=request.user, curso=curso).first()
        if inscricao and inscricao.status == 'andamento':
            hoje = timezone.now().date()
            
            if inscricao.ultima_interacao != hoje:
                if inscricao.ultima_interacao == hoje - timedelta(days=1):
                    inscricao.dias_seguidos += 1
                else:
                    inscricao.dias_seguidos = 1
                inscricao.ultima_interacao = hoje
                inscricao.save()
    
    # BUSCA OS PENSAMENTOS PÚBLICOS: Apenas de inscrições concluídas e que não estejam vazias
    pensamentos_publicos = Inscricao.objects.filter(
        curso=curso, 
        status='concluido'
    ).exclude(pensamento__isnull=True).exclude(pensamento='')
            
    return render(request, 'cursos/detalhe_curso.html', {
        'curso': curso,
        'inscricao': inscricao,
        'pensamentos_publicos': pensamentos_publicos
    })

@login_required
def acao_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscricao = Inscricao.objects.filter(usuario=request.user, curso=curso).first()
    
    if not inscricao:
        Inscricao.objects.create(usuario=request.user, curso=curso, status='andamento', ultima_interacao=timezone.now().date(), dias_seguidos=1)
    elif inscricao.status == 'andamento':
        inscricao.status = 'concluido'
        inscricao.save()
        
    return redirect('detalhe_curso', curso_id=curso.id)

@login_required
def perfil(request):
    # Juntamos as duas funções perfil que estavam duplicadas
    minhas_inscricoes = Inscricao.objects.filter(usuario=request.user)
    
    cursos_andamento = minhas_inscricoes.filter(status='andamento')
    cursos_concluidos = minhas_inscricoes.filter(status='concluido')
    
    total_comprados = minhas_inscricoes.count()
    total_concluidos = cursos_concluidos.count()
    
    return render(request, 'cursos/perfil.html', {
        'cursos_andamento': cursos_andamento,
        'cursos_concluidos': cursos_concluidos,
        'total_comprados': total_comprados,
        'total_concluidos': total_concluidos
    })

@login_required
def avaliar_curso(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)
        
    if request.method == "POST":
        if inscricao.status == 'concluido':
            nota_enviada = request.POST.get('nota')
            pensamento_enviado = request.POST.get('pensamento') # Captura o pensamento
            
            if nota_enviada and 0 <= int(nota_enviada) <= 10:
                inscricao.nota = int(nota_enviada)
                
            if pensamento_enviado:
                inscricao.pensamento = pensamento_enviado.strip()
                
            inscricao.save()
                
    elif request.method == "GET" and request.GET.get('alterar') == 'true':
        inscricao.nota = None
        inscricao.save()

    origem = request.GET.get('next', 'perfil')
    if origem == 'detalhe':
        return redirect('detalhe_curso', curso_id=inscricao.curso.id)
    return redirect('perfil')