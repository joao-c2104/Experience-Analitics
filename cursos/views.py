from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Curso, Inscricao, RelatorioIA
from .services.gemini_service import gerar_relatorio_com_gemini
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
            categorias = request.POST.getlist('categorias')
            pensamento_enviado = request.POST.get('pensamento', '').strip()

            try:
                nota = int(nota_enviada)
            except (TypeError, ValueError):
                nota = None

            if nota is not None and 0 <= nota <= 10:
                inscricao.nota = nota

            # O perfil continua aceitando somente a nota; o relatório nasce no detalhe.
            if not categorias and not pensamento_enviado and request.GET.get('next') != 'detalhe':
                inscricao.save()
                return redirect('perfil')

            if not categorias:
                messages.error(request, "Escolha pelo menos uma categoria para o feedback.")
                return redirect('detalhe_curso', curso_id=inscricao.curso.id)

            if not pensamento_enviado:
                messages.error(request, "Escreva seu feedback antes de enviar.")
                return redirect('detalhe_curso', curso_id=inscricao.curso.id)

            try:
                relatorio = gerar_relatorio_com_gemini(
                    usuario=request.user,
                    curso=inscricao.curso,
                    categorias=categorias,
                    comentario=pensamento_enviado,
                    nota=inscricao.nota
                )
            except Exception as erro:
                messages.error(request, f"Não foi possível gerar o relatório com IA: {erro}")
                return redirect('detalhe_curso', curso_id=inscricao.curso.id)

            inscricao.pensamento = pensamento_enviado
            inscricao.save()

            RelatorioIA.objects.create(
                usuario=request.user,
                curso=inscricao.curso,
                inscricao=inscricao,
                categorias=", ".join(categorias),
                comentario_original=pensamento_enviado,
                relatorio_gerado=relatorio
            )

            messages.success(request, "Avaliação enviada e relatório com IA gerado com sucesso.")

    elif request.method == "GET" and request.GET.get('alterar') == 'true':
        inscricao.nota = None
        inscricao.save()

    origem = request.GET.get('next', 'perfil')
    if origem == 'detalhe':
        return redirect('detalhe_curso', curso_id=inscricao.curso.id)
    return redirect('perfil')


@staff_member_required
def relatorios(request):
    relatorios_ia = RelatorioIA.objects.all().order_by('-data_criacao')
    return render(request, 'cursos/relatorios.html', {
        'relatorios': relatorios_ia
    })


@staff_member_required
def detalhe_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioIA, id=relatorio_id)
    return render(request, 'cursos/detalhe_relatorio.html', {
        'relatorio': relatorio
    })
