from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import logout
from .models import Curso, Inscricao
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

# --- FUNÇÃO AUXILIAR (STRIKE DIÁRIA) ---
def verificar_e_aplicar_strikes():
    """
    Varre o banco de dados em busca de inscrições 'Em Andamento' que 
    não registram interação há 15 dias ou mais e altera o status para 'Abandonado'.
    """
    # Como ultima_interacao é um DateField, pegamos a data de hoje (sem horas)
    hoje = timezone.now().date()
    limite_inatividade = hoje - timedelta(days=15)
    
    # Filtra quem está em andamento E (passou de 15 dias sem interagir OU nunca interagiu e a inscrição é antiga)
    inscricoes_com_strike = Inscricao.objects.filter(
        status='andamento'
    ).filter(
        models.Q(ultima_interacao__lte=limite_inatividade) | 
        models.Q(ultima_interacao__isnull=True, data_inscricao__date__lte=limite_inatividade)
    )
    
    # Executa o update em massa no banco de dados
    if inscricoes_com_strike.exists():
        inscricoes_com_strike.update(status='abandonado')


# --- VIEWS EXISTENTES ---

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
        Inscricao.objects.create(
            usuario=request.user, 
            curso=curso, 
            status='andamento', 
            ultima_interacao=timezone.now().date(), 
            dias_seguidos=1
        )
    elif inscricao.status == 'andamento':
        inscricao.status = 'concluido'
        inscricao.save()
        
    return redirect('detalhe_curso', curso_id=curso.id)

@login_required
def perfil(request):
    minhas_inscricoes = Inscricao.objects.filter(usuario=request.user)
    
    cursos_andamento = minhas_inscricoes.filter(status='andamento')
    cursos_concluidos = minhas_inscricoes.filter(status='concluido')
    
    total_comprados = minhas_inscricoes.exclude(status='reembolsado').count()
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
            pensamento_enviado = request.POST.get('pensamento')
            
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

@login_required
def solicitar_reembolso_aluno(request, inscricao_id):
    inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)
    
    # REGRA NOVA: Só permite reembolso se o status for exatamente 'andamento'
    if inscricao.status != 'andamento':
        messages.error(request, "O reembolso só pode ser solicitado enquanto o curso estiver em andamento. Cursos já concluídos não são elegíveis.")
        return redirect('perfil')

    if request.method == 'POST':
        inscricao.status = 'reembolsado'
        inscricao.save()
        messages.success(request, f"O reembolso do curso '{inscricao.curso.nome}' foi processado. O acesso foi revogado.")
        return redirect('perfil')
        
    return render(request, 'cursos/confirmar_reembolso_aluno.html', {'inscricao': inscricao})


# --- VIEWS DE ADMINISTRADOR ATUALIZADAS ---

@staff_member_required
def dashboard_financeiro(request):
    # 1. Executa a checagem automática da Strike de 15 dias antes de computar os dados
    verificar_e_aplicar_strikes()

    # 2. Processa as métricas normalmente com os dados atualizados
    total_validas = Inscricao.objects.exclude(status='reembolsado').count()
    abandonados = Inscricao.objects.filter(status='abandonado').count()
    taxa_abandono = (abandonados / total_validas * 100) if total_validas > 0 else 0
    
    total_usuarios = Inscricao.objects.exclude(status='reembolsado').values('usuario').distinct().count()
    usuarios_recorrentes = Inscricao.objects.exclude(status='reembolsado').values('usuario').annotate(total_cursos=Count('id')).filter(total_cursos__gt=1).count()
    taxa_retencao = (usuarios_recorrentes / total_usuarios * 100) if total_usuarios > 0 else 0
    
    total_historico_absoluto = Inscricao.objects.count()
    reembolsados = Inscricao.objects.filter(status='reembolsado').count()
    taxa_cancelamento = (reembolsados / total_historico_absoluto * 100) if total_historico_absoluto > 0 else 0
    
    # Lista apenas inscrições ativas elegíveis para reembolso
    inscricoes_ativas = Inscricao.objects.filter(status__in=['andamento', 'concluido']).order_by('-data_inscricao')

    context = {
        'taxa_abandono': round(taxa_abandono, 2),
        'taxa_retencao': round(taxa_retencao, 2),
        'taxa_cancelamento': round(taxa_cancelamento, 2),
        'inscricoes_reembolso': inscricoes_ativas,
    }
    return render(request, 'admin/cursos/dashboard.html', context)

@staff_member_required
def processar_reembolso(request, order_id):
    # Recupera a inscrição se ela estiver ativa (andamento ou concluído)
    inscricao = get_object_or_404(Inscricao, id=order_id, status__in=['andamento', 'concluido'])
    
    if request.method == 'POST':
        inscricao.status = 'reembolsado'
        inscricao.save()
        # Envia feedback visual para o dashboard
        messages.success(request, f"O curso '{inscricao.curso.nome}' do usuário {inscricao.usuario.username} foi reembolsado com sucesso!")
        return redirect('admin_dashboard_financeiro')
        
    return render(request, 'admin/cursos/confirmar_reembolso.html', {'inscricao': inscricao})