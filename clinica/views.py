from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime as dt, timedelta
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
    """Quando um agendamento é concluído, desconta os produtos do estoque"""
    try:
        agendamento = Agendamento.objects.get(id=agendamento_id)

        # Verifica todos os consumos vinculados a este agendamento
        for consumo in agendamento.consumos.all():
            if consumo.produto.quantidade_estoque < consumo.quantidade:
                messages.error(
                    request,
                    f"Estoque insuficiente para o produto {consumo.produto.nome}"
                )
                return redirect("admin:clinica_agendamento_changelist")

        # Desconta do estoque
        for consumo in agendamento.consumos.all():
            produto = consumo.produto
            produto.quantidade_estoque -= consumo.quantidade
            produto.save()

        agendamento.status = "CONCLUIDO"
        agendamento.save()

        messages.success(request, "Agendamento concluído e estoque atualizado!")
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
