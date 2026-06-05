from django.contrib import admin
from .models import Curso, Inscricao, RelatorioIA
from django.db import models
from django.shortcuts import redirect

admin.site.register(Curso)
admin.site.register(Inscricao)
admin.site.register(RelatorioIA)

class DashboardFinanceiro(models.Model):
    class Meta:
        verbose_name = "Dashboard Financeiro"
        verbose_name_plural = "Dashboards Financeiros"
        managed = False

@admin.register(DashboardFinanceiro)
class DashboardFinanceiroAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    def changelist_view(self, request, extra_context=None):
        return redirect('admin_dashboard_financeiro')
