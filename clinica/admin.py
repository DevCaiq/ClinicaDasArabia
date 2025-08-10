from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, Tratamento, Agendamento, Receita, Despesa, Caixa, CustomUser


# Registro do modelo CustomUser com UserAdmin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Mostra miniatura da imagem
    def profile_picture_tag(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;" />', obj.profile_picture.url)
        return "-"
    profile_picture_tag.short_description = 'Foto'

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_picture_tag')

    fieldsets = UserAdmin.fieldsets + (
        ('Informações adicionais', {'fields': ('profile_picture',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações adicionais', {'fields': ('profile_picture',)}),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email')
    search_fields = ('nome', 'telefone', 'email')

@admin.register(Tratamento)
class TratamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_tratamento', 'preco')
    search_fields = ('nome_tratamento',)

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tratamento', 'data', 'hora', 'tipo_agendamento')
    list_filter = ('data', 'tipo_agendamento')
    search_fields = ('cliente__nome', 'tratamento__nome_tratamento')

@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data_recebimento', 'forma_pagamento')
    list_filter = ('forma_pagamento', 'data_recebimento')
    search_fields = ('descricao',)

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('nome_despesa', 'valor', 'data_vencimento', 'categoria')
    list_filter = ('categoria', 'data_vencimento')
    search_fields = ('nome_despesa',)

@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    list_display = ('ano', 'mes', 'total_receitas', 'total_despesas', 'saldo')
