from django import forms
from .models import Agendamento, Cliente, Tratamento
from django.utils import timezone
import datetime

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control firstname', 'placeholder': 'Nome Completo*', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control email', 'placeholder': 'Email*', 'required': True}),
            'telefone': forms.TextInput(attrs={'class': 'form-control phone', 'placeholder': 'Telefone*', 'required': True}),
        }


class AgendamentoForm(forms.ModelForm):
    data_hora = forms.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.TextInput(attrs={
            'class': 'form-control datetimepicker', 
            'placeholder': 'Selecione data e hora*',
            'autocomplete': 'off',
            'required': True,
            'id': 'id_data_hora',
        }),
        label='Data e Hora'
    )

    class Meta:
        model = Agendamento
        fields = ['tratamento', 'tipo_agendamento', 'data_hora']
        widgets = {
            'tratamento': forms.Select(attrs={'class': 'form-select'}),
            'tipo_agendamento': forms.Select(attrs={'class': 'form-select staff'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tratamento'].empty_label = "Selecione um tratamento*"
        if hasattr(self.fields['tipo_agendamento'], 'choices'):
            choices = list(self.fields['tipo_agendamento'].choices)
            if choices and choices[0][0] != '':
                self.fields['tipo_agendamento'].choices = [('', 'Tipo de Agendamento*')] + choices

    def clean_data_hora(self):
        data_hora = self.cleaned_data.get('data_hora')
        if not data_hora:
            raise forms.ValidationError("Este campo é obrigatório.")

        if not timezone.is_aware(data_hora):
            data_hora = timezone.make_aware(data_hora)

        agora = timezone.now()
        if data_hora < agora:
            raise forms.ValidationError("Não é possível agendar em datas passadas.")

        dia_semana = data_hora.weekday()
        hora = data_hora.time()

        if dia_semana >= 0 and dia_semana <= 4:  # Segunda a Sexta
            if not (hora >= datetime.time(10, 0) and hora <= datetime.time(18, 0)):
                raise forms.ValidationError("Horário fora do expediente (10:00 às 18:00, segunda a sexta).")
        elif dia_semana == 5:  # Sábado
            if not (hora >= datetime.time(12, 0) and hora <= datetime.time(16, 0)):
                raise forms.ValidationError("Horário fora do expediente (12:00 às 16:00, sábado).")
        else:
            raise forms.ValidationError("Agendamento não permitido neste dia.")

        return data_hora

    def clean(self):
        cleaned_data = super().clean()
        tratamento = cleaned_data.get('tratamento')
        data_hora = cleaned_data.get('data_hora')
        if tratamento and data_hora:
            conflito = Agendamento.objects.filter(
                tratamento=tratamento,
                data=data_hora.date(),
                hora=data_hora.time()
            ).exists()
            if conflito:
                raise forms.ValidationError("Já existe um agendamento neste horário para este tratamento.")
        return cleaned_data
