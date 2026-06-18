from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from datetime import timedelta
from django.db.models import Count

from .models import Curso, Inscricao, RelatorioIA
from .services.gemini_service import GeminiService


class LoginRedirectView(View):
    def get(self, request):
        if request.user.is_staff:
            return redirect('admin_dashboard_financeiro')
        return redirect('lista_cursos')


class FazerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('lista_cursos')


class ListaCursosView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff:
            return redirect('admin_dashboard_financeiro')
        cursos = Curso.objects.all()
        return render(request, 'cursos/lista_cursos.html', {'cursos': cursos})


class ListaCursosAdminView(LoginRequiredMixin, View):
    def get(self, request):
        cursos = Curso.objects.all()
        return render(request, 'cursos/lista_cursos.html', {'cursos': cursos})


class DetalheCursoView(View):
    def get(self, request, curso_id):
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


class AcaoCursoView(LoginRequiredMixin, View):
    def _processar(self, request, curso_id):
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

    def get(self, request, curso_id):
        return self._processar(request, curso_id)

    def post(self, request, curso_id):
        return self._processar(request, curso_id)


class PerfilView(LoginRequiredMixin, View):
    def get(self, request):
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


class AvaliarCursoView(LoginRequiredMixin, View):
    def post(self, request, inscricao_id):
        inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)

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
                servico = GeminiService()
                relatorio = servico.gerar_relatorio(
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

        origem = request.GET.get('next', 'perfil')
        if origem == 'detalhe':
            return redirect('detalhe_curso', curso_id=inscricao.curso.id)
        return redirect('perfil')

    def get(self, request, inscricao_id):
        inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)

        if request.GET.get('alterar') == 'true':
            inscricao.nota = None
            inscricao.save()

        origem = request.GET.get('next', 'perfil')
        if origem == 'detalhe':
            return redirect('detalhe_curso', curso_id=inscricao.curso.id)
        return redirect('perfil')


@method_decorator(staff_member_required, name='dispatch')
class RelatoriosView(View):
    def get(self, request):
        relatorios_ia = RelatorioIA.objects.all().order_by('-data_criacao')
        return render(request, 'cursos/relatorios.html', {
            'relatorios': relatorios_ia
        })


@method_decorator(staff_member_required, name='dispatch')
class DetalheRelatorioView(View):
    def get(self, request, relatorio_id):
        relatorio = get_object_or_404(RelatorioIA, id=relatorio_id)
        return render(request, 'cursos/detalhe_relatorio.html', {
            'relatorio': relatorio
        })


class SolicitarReembolsoAlunoView(LoginRequiredMixin, View):
    def get(self, request, inscricao_id):
        inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)

        if inscricao.status != 'andamento':
            messages.error(request, "O reembolso só pode ser solicitado enquanto o curso estiver em andamento. Cursos já concluídos não são elegíveis.")
            return redirect('perfil')

        return render(request, 'cursos/confirmar_reembolso_aluno.html', {'inscricao': inscricao})

    def post(self, request, inscricao_id):
        inscricao = get_object_or_404(Inscricao, id=inscricao_id, usuario=request.user)

        if inscricao.status != 'andamento':
            messages.error(request, "O reembolso só pode ser solicitado enquanto o curso estiver em andamento. Cursos já concluídos não são elegíveis.")
            return redirect('perfil')

        inscricao.status = 'reembolsado'
        inscricao.save()
        messages.success(request, f"O reembolso do curso '{inscricao.curso.nome}' foi processado. O acesso foi revogado.")
        return redirect('perfil')


@method_decorator(staff_member_required, name='dispatch')
class DashboardFinanceiroView(View):
    def get(self, request):
        Inscricao.aplicar_strikes()

        total_validas = Inscricao.objects.exclude(status='reembolsado').count()
        abandonados = Inscricao.objects.filter(status='abandonado').count()
        taxa_abandono = (abandonados / total_validas * 100) if total_validas > 0 else 0

        total_usuarios = Inscricao.objects.exclude(status='reembolsado').values('usuario').distinct().count()
        usuarios_recorrentes = Inscricao.objects.exclude(status='reembolsado').values('usuario').annotate(total_cursos=Count('id')).filter(total_cursos__gt=1).count()
        taxa_retencao = (usuarios_recorrentes / total_usuarios * 100) if total_usuarios > 0 else 0

        total_historico_absoluto = Inscricao.objects.count()
        reembolsados = Inscricao.objects.filter(status='reembolsado').count()
        taxa_cancelamento = (reembolsados / total_historico_absoluto * 100) if total_historico_absoluto > 0 else 0

        inscricoes_ativas = Inscricao.objects.filter(status__in=['andamento', 'concluido']).order_by('-data_inscricao')

        context = {
            'taxa_abandono': round(taxa_abandono, 2),
            'taxa_retencao': round(taxa_retencao, 2),
            'taxa_cancelamento': round(taxa_cancelamento, 2),
            'inscricoes_reembolso': inscricoes_ativas,
        }
        return render(request, 'admin/cursos/dashboard.html', context)


@method_decorator(staff_member_required, name='dispatch')
class ProcessarReembolsoView(View):
    def get(self, request, order_id):
        inscricao = get_object_or_404(Inscricao, id=order_id, status__in=['andamento', 'concluido'])
        return render(request, 'admin/cursos/confirmar_reembolso.html', {'inscricao': inscricao})

    def post(self, request, order_id):
        inscricao = get_object_or_404(Inscricao, id=order_id, status__in=['andamento', 'concluido'])
        inscricao.status = 'reembolsado'
        inscricao.save()
        messages.success(request, f"O curso '{inscricao.curso.nome}' do usuário {inscricao.usuario.username} foi reembolsado com sucesso!")
        return redirect('admin_dashboard_financeiro')
