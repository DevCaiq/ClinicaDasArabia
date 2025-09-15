from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractYear
from datetime import datetime as dt, timedelta, date
from django.db.models import Sum, Count, F
from django.http import JsonResponse
from django.contrib import messages
from dateutil.relativedelta import relativedelta
import datetime
from .models import *


import urllib.parse

from .models import (
    Agendamento, Cliente, Tratamento,
    Receita, Despesa, Caixa, Produto, ConsumoProduto
)
from .forms import AgendamentoForm, ClienteForm


def index(request):
    nomes_tratamentos_destaque = [
        'Harmonização Facial',
        'Botox',
        'Rinomodelação',
        'Peeling',
        'Microagulhamento',
        'Fios de PDO',
        'Bioestimulador de Colágeno'
    ]

    tratamentos_destaque = list(Tratamento.objects.filter(nome_tratamento__in=nomes_tratamentos_destaque))

    meio = len(tratamentos_destaque) // 2
    col1 = tratamentos_destaque[:meio]
    col2 = tratamentos_destaque[meio:]

    return render(request, 'index.html', {
        'coluna1': col1,
        'coluna2': col2,
    })


def tratamento(request):
    tratamentos = Tratamento.objects.all()  # Busca todos os tratamentos
    return render(request, 'tratamentos.html', {'tratamentos': tratamentos})


def criar_agendamento(cliente_form, agendamento_form):
    """Cria agendamento, valida estoque e gera link WhatsApp"""
    cliente = cliente_form.save()
    data_hora = agendamento_form.cleaned_data['data_hora']
    tratamento = agendamento_form.cleaned_data['tratamento']
    tipo_agendamento = agendamento_form.cleaned_data['tipo_agendamento']

    # Criar agendamento (sem ainda mexer no estoque)
    agendamento_obj = Agendamento.objects.create(
        cliente=cliente,
        tratamento=tratamento,
        data=data_hora.date(),
        hora=data_hora.time(),
        tipo_agendamento=tipo_agendamento,
        status='PENDENTE'
    )

    # Mensagem automática do WhatsApp
    nome_tratamento = agendamento_obj.tratamento.nome_tratamento
    mensagem = (
        f"Prezado(a) {cliente.nome},\n"
        f"Agradecemos pelo seu contato. Seguem os detalhes do seu agendamento:\n"
        f"Nome: {cliente.nome}\n"
        f"Telefone: {cliente.telefone}\n"
        f"Tratamento: {nome_tratamento}\n"
        f"Data: {agendamento_obj.data.strftime('%d/%m/%Y')}\n"
        f"Hora: {agendamento_obj.hora.strftime('%H:%M')}\n"
        f"Tipo: {agendamento_obj.tipo_agendamento}\n\n"
        f"Por favor, aguardar o retorno da confirmação do agendamento\n"
        f"Atenciosamente,\n"
        f"Dra. Naime Farhat - Clínica das Árabia"
    )
    mensagem_codificada = urllib.parse.quote(mensagem)
    link_whatsapp = f"https://wa.me/5511988910049?text={mensagem_codificada}"
    return agendamento_obj, link_whatsapp


def agendamento(request):
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST)
        agendamento_form = AgendamentoForm(request.POST)

        if cliente_form.is_valid() and agendamento_form.is_valid():
            try:
                agendamento_obj, link_whatsapp = criar_agendamento(cliente_form, agendamento_form)
                messages.success(request, "Agendamento criado com sucesso!")

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'whatsapp_url': link_whatsapp})
                else:
                    return redirect(link_whatsapp)

            except Exception as e:
                messages.error(request, f"Erro ao salvar o agendamento: {e}")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            errors = {}
            for form in [cliente_form, agendamento_form]:
                if form.errors:
                    errors.update(form.errors)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': errors}, status=400)
            else:
                for field, error_list in errors.items():
                    for error in error_list:
                        messages.error(request, f"Erro no campo '{field}': {error}")
    else:
        cliente_form = ClienteForm()
        agendamento_form = AgendamentoForm()

    context = {'cliente_form': cliente_form, 'agendamento_form': agendamento_form}
    return render(request, 'agendamento.html', context)


def concluir_agendamento(request, agendamento_id):
    """Quando um agendamento é concluído, desconta os produtos do estoque (usando método do modelo)."""
    try:
        agendamento = Agendamento.objects.get(id=agendamento_id)
        try:
            agendamento.descontar_estoque_e_concluir()
            messages.success(request, "Agendamento concluído e estoque atualizado!")
        except ValidationError as e:
            messages.error(request, str(e))
    except Agendamento.DoesNotExist:
        messages.error(request, "Agendamento não encontrado.")
    return redirect("admin:clinica_agendamento_changelist")


def admin_agendamentos_json(request):
    """Endpoint JSON para calendário do admin"""
    agendamentos = Agendamento.objects.all()
    eventos = []

    for ag in agendamentos:
        start = dt.combine(ag.data, ag.hora)
        end = start + (ag.tratamento.duracao_timedelta if ag.tratamento else timedelta(hours=1))
        eventos.append({
            'title': f'{ag.cliente.nome} - {ag.tratamento.nome_tratamento}',
            'start': start.isoformat(),
            'end': end.isoformat(),
            'extendedProps': {'tipo': ag.tipo_agendamento.upper()},
            'color': '#f39c12' if ag.tipo_agendamento.upper() == 'AVALIACAO' else '#27ae60'
        })

    return JsonResponse(eventos, safe=False)


def admin_index(request):
    """Dashboard financeiro simples"""
    despesas_em_aberto = Despesa.objects.filter(pago=False).aggregate(total=Sum('valor'))['total'] or 0
    receitas = Receita.objects.filter(recebido=True).aggregate(total=Sum('valor'))['total'] or 0
    caixa = receitas - despesas_em_aberto

    context = {
        'despesas_em_aberto': despesas_em_aberto,
        'receitas': receitas,
        'caixa': caixa,
    }
    return render(request, 'admin/index.html', context)



# ============================= #
# GRAFICOS
# ============================= #

# AGENDAMENTOS
def agendamentos_por_tratamento(request):
    data = Agendamento.objects.values('tratamento__nome_tratamento') \
        .annotate(count=Count('id')) \
        .order_by('-count')
    labels = [item['tratamento__nome_tratamento'] for item in data]
    counts = [item['count'] for item in data]
    return JsonResponse({'labels': labels, 'counts': counts})

def agendamentos_por_periodo(request, periodo='dia'):
    if periodo == 'dia':
        trunc = TruncDay('data')
    elif periodo == 'semana':
        trunc = TruncWeek('data')
    else:
        trunc = TruncMonth('data')

    data = Agendamento.objects.annotate(period=trunc) \
        .values('period') \
        .annotate(count=Count('id')) \
        .order_by('period')
    labels = [item['period'].strftime('%d/%m/%Y') for item in data]
    counts = [item['count'] for item in data]
    return JsonResponse({'labels': labels, 'counts': counts})

def clientes_com_mais_agendamentos(request):
    data = Agendamento.objects.values('cliente__nome') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:10]
    labels = [item['cliente__nome'] for item in data]
    counts = [item['count'] for item in data]
    return JsonResponse({'labels': labels, 'counts': counts})

# FINANCEIRO
def receitas_despesas_por_mes(request):
    hoje = datetime.date.today()
    meses = [hoje - datetime.timedelta(days=30*i) for i in range(5,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]

    receitas_data = [Receita.objects.filter(data_recebimento__month=m.month, data_recebimento__year=m.year)
                     .aggregate(total=Sum('valor'))['total'] or 0 for m in meses]
    despesas_data = [Despesa.objects.filter(data_vencimento__month=m.month, data_vencimento__year=m.year)
                     .aggregate(total=Sum('valor'))['total'] or 0 for m in meses]

    return JsonResponse({'labels': labels, 'receitas': receitas_data, 'despesas': despesas_data})

def receita_acumulada_vs_despesa(request):
    hoje = datetime.date.today()
    meses = [hoje - datetime.timedelta(days=30*i) for i in range(5,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]
    receitas_acum = []
    despesas_acum = []
    r_total = 0
    d_total = 0
    for m in meses:
        r = Receita.objects.filter(data_recebimento__month=m.month, data_recebimento__year=m.year)\
            .aggregate(total=Sum('valor'))['total'] or 0
        d = Despesa.objects.filter(data_vencimento__month=m.month, data_vencimento__year=m.year)\
            .aggregate(total=Sum('valor'))['total'] or 0
        r_total += r
        d_total += d
        receitas_acum.append(r_total)
        despesas_acum.append(d_total)

    return JsonResponse({'labels': labels, 'receitas': receitas_acum, 'despesas': despesas_acum})

def despesas_por_categoria(request):
    data = Despesa.objects.values('categoria__nome').annotate(total=Sum('valor'))
    labels = [item['categoria__nome'] for item in data]
    totals = [item['total'] for item in data]
    return JsonResponse({'labels': labels, 'totals': totals})

def receitas_por_tipo_pagamento(request):
    data = Receita.objects.values('forma_pagamento').annotate(total=Sum('valor'))
    labels = [item['forma_pagamento'] for item in data]
    totals = [item['total'] for item in data]
    return JsonResponse({'labels': labels, 'totals': totals})

#ESTOQUE & PRODUTOS
def movimentacao_estoque(request):
    hoje = datetime.date.today()
    meses = [hoje - datetime.timedelta(days=30*i) for i in range(5,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]
    entradas = []
    saidas = []
    for m in meses:
        ent = MovimentacaoEstoque.objects.filter(tipo='entrada', data__month=m.month, data__year=m.year)\
            .aggregate(total=Sum('quantidade'))['total'] or 0
        sai = MovimentacaoEstoque.objects.filter(tipo='saida', data__month=m.month, data__year=m.year)\
            .aggregate(total=Sum('quantidade'))['total'] or 0
        entradas.append(ent)
        saidas.append(sai)
    return JsonResponse({'labels': labels, 'entradas': entradas, 'saidas': saidas})

def produtos_estoque_baixo_json(request):
    produtos = Produto.objects.filter(quantidade_estoque__lte=F('estoque_minimo')).values('nome','quantidade_estoque')
    data = {
        'labels':[p['nome'] for p in produtos],
        'quantidades':[p['quantidade_estoque'] for p in produtos]
    }
    return JsonResponse(data)

# ---------- Clientes ----------
def clientes_por_idade_json(request):
    hoje = date.today()
    clientes = Cliente.objects.annotate(
        idade=hoje.year - ExtractYear('dt_nascimento')  # corrigido para dt_nascimento
    ).values('idade').annotate(count=Count('id')).order_by('idade')
    
    data = {
        'labels': [c['idade'] for c in clientes],
        'counts': [c['count'] for c in clientes]
    }
    return JsonResponse(data)

def novos_clientes_mes_json(request):
    hoje = date.today()
    meses = [hoje - relativedelta(months=i) for i in range(11, -1, -1)]
    labels = [m.strftime("%b/%Y") for m in meses]

    counts = [
        Cliente.objects.filter(created_at__year=m.year, created_at__month=m.month).count()
        for m in meses
    ]

    return JsonResponse({'labels': labels, 'counts': counts})

def top_tratamentos_por_cliente_json(request):
    agendamentos = Agendamento.objects.values('tratamento__nome_tratamento') \
                                      .annotate(count=Count('id')) \
                                      .order_by('-count')[:10]
    data = {
        'labels': [a['tratamento__nome_tratamento'] for a in agendamentos],
        'counts': [a['count'] for a in agendamentos]
    }
    return JsonResponse(data)

# ---------- Indicadores combinados ----------
def agendamentos_trend_json(request):
    hoje = date.today()
    meses = [hoje - timedelta(days=30*i) for i in range(11,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]
    counts = [Agendamento.objects.filter(data__year=m.year, data__month=m.month).count() for m in meses]
    return JsonResponse({'labels': labels, 'counts': counts})

def receitas_vs_a_receber_json(request):
    hoje = date.today()
    meses = [hoje - timedelta(days=30*i) for i in range(11,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]
    receitas = [Receita.objects.filter(data_recebimento__year=m.year, data_recebimento__month=m.month, recebido=True).aggregate(total=Sum('valor'))['total'] or 0 for m in meses]
    a_receber = [Receita.objects.filter(data_recebimento__year=m.year, data_recebimento__month=m.month, recebido=False).aggregate(total=Sum('valor'))['total'] or 0 for m in meses]
    return JsonResponse({'labels': labels, 'recebidas': receitas, 'a_receber': a_receber})

def saldo_caixa_json(request):
    hoje = date.today()
    meses = [hoje - timedelta(days=30*i) for i in range(11,-1,-1)]
    labels = [m.strftime("%b/%Y") for m in meses]
    saldos = []
    for m in meses:
        receitas = Receita.objects.filter(data_recebimento__year=m.year, data_recebimento__month=m.month, recebido=True).aggregate(total=Sum('valor'))['total'] or 0
        despesas = Despesa.objects.filter(data_vencimento__year=m.year, data_vencimento__month=m.month, pago=True).aggregate(total=Sum('valor'))['total'] or 0
        saldos.append(receitas - despesas)
    return JsonResponse({'labels': labels, 'saldos': saldos})

def produtos_criticos_json(request):
    produtos = Produto.objects.filter(
        quantidade_estoque__lte=F('estoque_minimo')
    ).values('nome', 'quantidade_estoque')[:10]  # top 10
    data = {
        'labels':[p['nome'] for p in produtos],
        'counts':[p['quantidade_estoque'] for p in produtos]
    }
    return JsonResponse(data)

def taxa_cancelamento_json(request):
    total = Agendamento.objects.count()
    cancelados = Agendamento.objects.filter(status='cancelado').count()
    data = {
        'labels':['Cancelados','Ativos'],
        'percentuais':[cancelados, total-cancelados]
    }
    return JsonResponse(data)