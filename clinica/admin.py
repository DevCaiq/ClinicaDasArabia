from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum
from .models import (
    CustomUser,
    Cliente,
    Tratamento,
    Agendamento,
    Receita,
    Despesa,
    Caixa,
    Produto,
    MovimentacaoEstoque,
    ConsumoProduto,
    CategoriaDespesa,
)


# ===========================
# Custom AdminSite
# ===========================
# ===========================
# Custom AdminSite
# ===========================
class CustomAdminSite(AdminSite):
    site_header = "Painel Administrativo"
    site_title = "Admin"
    index_title = "Home"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.custom_index), name='index'),
        ]
        return custom_urls + urls

    def custom_index(self, request):
        despesas_em_aberto = Despesa.objects.filter(pago=False).aggregate(total=Sum('valor'))['total'] or 0
        receitas_recebidas = Receita.objects.filter(recebido=True).aggregate(total=Sum('valor'))['total'] or 0
        caixa_atual = receitas_recebidas - despesas_em_aberto

        context = dict(
            self.each_context(request),
            despesas_em_aberto=despesas_em_aberto,
            receitas=receitas_recebidas,
            caixa=caixa_atual
        )
        return render(request, 'admin/index.html', context)


# ===========================
# Instância da AdminSite customizada
# ===========================
custom_admin_site = CustomAdminSite(name='custom_admin')


# ===========================
# Admins dos Models
# ===========================
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    def profile_picture_tag(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;" />', obj.profile_picture.url)
        return "-"
    profile_picture_tag.short_description = 'Foto'

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_picture_tag')
    fieldsets = UserAdmin.fieldsets + (('Informações adicionais', {'fields': ('profile_picture',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Informações adicionais', {'fields': ('profile_picture',)}),)


class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email')
    search_fields = ('nome', 'telefone', 'email')


class TratamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_tratamento', 'tipo_tratamento', 'duracao', 'preco')
    search_fields = ('nome_tratamento',)
    list_filter = ('tipo_tratamento',)


# Inline para registrar consumos diretamente no Agendamento
class ConsumoProdutoInline(admin.TabularInline):
    model = ConsumoProduto
    extra = 1
    autocomplete_fields = ['produto']  # opcional: facilita seleção do produto no admin


class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tratamento', 'data', 'hora', 'tipo_agendamento', 'status')
    list_filter = ('data', 'tipo_agendamento', 'status')
    search_fields = ('cliente__nome', 'tratamento__nome_tratamento')
    inlines = [ConsumoProdutoInline]  # agora é possível cadastrar consumos diretamente


class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data_recebimento', 'forma_pagamento')
    list_filter = ('forma_pagamento', 'data_recebimento')
    search_fields = ('descricao',)


class DespesaAdmin(admin.ModelAdmin):
    list_display = ('nome_despesa', 'valor', 'data_vencimento', 'categoria')
    list_filter = ('categoria', 'data_vencimento')
    search_fields = ('nome_despesa',)

class CategoriaDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

class CaixaAdmin(admin.ModelAdmin):
    list_display = ('ano', 'mes', 'total_receitas', 'total_despesas', 'saldo')


class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'marca', 'preco_venda', 'data_validade', 'quantidade_estoque')
    list_filter = ('marca',)
    search_fields = ('nome', 'marca')


class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'motivo', 'data')
    list_filter = ('tipo', 'data')
    search_fields = ('produto__nome', 'motivo')


# ===========================
# Registrar models na AdminSite customizada
# ===========================
custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Cliente, ClienteAdmin)
custom_admin_site.register(Tratamento, TratamentoAdmin)
custom_admin_site.register(Agendamento, AgendamentoAdmin)
custom_admin_site.register(Receita, ReceitaAdmin)
custom_admin_site.register(Despesa, DespesaAdmin)
custom_admin_site.register(CategoriaDespesa, CategoriaDespesaAdmin)
custom_admin_site.register(Caixa, CaixaAdmin)
custom_admin_site.register(Produto, ProdutoAdmin)
custom_admin_site.register(MovimentacaoEstoque, MovimentacaoEstoqueAdmin)
