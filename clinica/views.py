from .models import Agendamento, Cliente, Tratamento, TipoAgendamento
from django.views.decorators.http import require_POST
from .forms import AgendamentoForm, ClienteForm
from django.shortcuts import render, redirect
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
import urllib.parse
import datetime
import json


def index(request):
    return render(request, 'index.html')

def tratamento(request):
    return render(request, 'tratamentos.html')

def agendamento(request):
    if request.method == 'POST':
        # Se a requisição é AJAX, processamos como uma API
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # O JavaScript envia formData, então processamos com os forms
                cliente_form = ClienteForm(request.POST)
                agendamento_form = AgendamentoForm(request.POST)

                if cliente_form.is_valid() and agendamento_form.is_valid():
                    cliente = cliente_form.save()

                    data_hora = agendamento_form.cleaned_data['data_hora']
                    tratamento = agendamento_form.cleaned_data['tratamento']
                    tipo_agendamento = agendamento_form.cleaned_data['tipo_agendamento']

                    agendamento_obj = Agendamento.objects.create(
                        cliente=cliente,
                        tratamento=tratamento,
                        data=data_hora.date(),
                        hora=data_hora.time(),
                        tipo_agendamento=tipo_agendamento,
                    )

                    nome_tratamento = agendamento_obj.tratamento.nome_tratamento
                    mensagem = (
                        f"Agendamento:\n"
                        f"Nome: {cliente.nome}\n"
                        f"Telefone: {cliente.telefone}\n"
                        f"Tratamento: {nome_tratamento}\n"
                        f"Data: {agendamento_obj.data.strftime('%d/%m/%Y')}\n"
                        f"Hora: {agendamento_obj.hora.strftime('%H:%M')}\n"
                        f"Tipo: {agendamento_obj.tipo_agendamento}"
                    )
                    mensagem_codificada = urllib.parse.quote(mensagem)
                    link_whatsapp = f"https://wa.me/5511940709836?text={mensagem_codificada}"
                    
                    return JsonResponse({'status': 'success', 'whatsapp_url': link_whatsapp})

                else:
                    # Se houver erros, retorna um JSON com os erros
                    errors = {}
                    if cliente_form.errors:
                        errors.update(cliente_form.errors)
                    if agendamento_form.errors:
                        errors.update(agendamento_form.errors)

                    return JsonResponse({'status': 'error', 'errors': errors}, status=400)

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': 'Ocorreu um erro inesperado.'}, status=500)

        # Para requisições POST normais (não-AJAX)
        else:
            cliente_form = ClienteForm(request.POST)
            agendamento_form = AgendamentoForm(request.POST)

            if cliente_form.is_valid() and agendamento_form.is_valid():
                try:
                    cliente = cliente_form.save()
                    data_hora = agendamento_form.cleaned_data['data_hora']
                    tratamento = agendamento_form.cleaned_data['tratamento']
                    tipo_agendamento = agendamento_form.cleaned_data['tipo_agendamento']
                    
                    agendamento_obj = Agendamento.objects.create(
                        cliente=cliente,
                        tratamento=tratamento,
                        data=data_hora.date(),
                        hora=data_hora.time(),
                        tipo_agendamento=tipo_agendamento,
                    )
                    
                    nome_tratamento = agendamento_obj.tratamento.nome_tratamento
                    mensagem = (
                        f"Agendamento:\n"
                        f"Nome: {cliente.nome}\n"
                        f"Telefone: {cliente.telefone}\n"
                        f"Tratamento: {nome_tratamento}\n"
                        f"Data: {agendamento_obj.data.strftime('%d/%m/%Y')}\n"
                        f"Hora: {agendamento_obj.hora.strftime('%H:%M')}\n"
                        f"Tipo: {agendamento_obj.tipo_agendamento}"
                    )
                    mensagem_codificada = urllib.parse.quote(mensagem)
                    link_whatsapp = f"https://wa.me/5511940709836?text={mensagem_codificada}"
                    
                    return redirect(link_whatsapp)
                except Exception as e:
                    messages.error(request, f"Erro ao salvar o agendamento: {e}")
            else:
                for form in [cliente_form, agendamento_form]:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"Erro no campo '{field}': {error}")
                messages.error(request, "Por favor, corrija os erros no formulário.")
    
    else:
        cliente_form = ClienteForm()
        agendamento_form = AgendamentoForm()

    context = {'cliente_form': cliente_form, 'agendamento_form': agendamento_form}
    return render(request, 'agendamento.html', context)