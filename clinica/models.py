from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from django.db import models
import calendar

# Modelo de usuário personalizado
class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.first_name or self.username

DURACAO_CHOICES = [
    (timedelta(minutes=30), '30 minutos'),
    (timedelta(hours=1), '1 hora'),
    (timedelta(hours=1, minutes=30), '1 hora e 30 minutos'),
    (timedelta(hours=2), '2 horas'),
    (timedelta(hours=2, minutes=30), '2 horas e 30 minutos'),
    (timedelta(hours=3), '3 horas'),
    (timedelta(hours=3, minutes=30), '3 horas e 30 minutos'),
    (timedelta(hours=4), '4 horas'),
    (timedelta(hours=4, minutes=30), '4 horas e 30 minutos'),
    (timedelta(hours=5), '5 horas'),
    (timedelta(hours=5, minutes=30), '5 horas e 30 minutos'),
    (timedelta(hours=6), '6 horas'),
    (timedelta(hours=6, minutes=30), '6 horas e 30 minutos'),
    (timedelta(hours=7), '7 horas'),
    (timedelta(hours=7, minutes=30), '7 horas e 30 minutos'),
    (timedelta(hours=8), '8 horas'),
]

class TiposTratamentos(models.TextChoices):
    FACIAL = 'Facial', 'Facial'
    LABIAL = 'Labial', 'Labial'
    GLUTEOS = 'Glúteos', 'Glúteos'
    CORPORAL = 'Corporal', 'Corporal'

class Tratamento(models.Model):
    nome_tratamento = models.CharField('Tratamento', max_length=100)
    tipo_tratamento = models.CharField('Tipo Tratamento', max_length=100, choices=TiposTratamentos.choices, null=True, blank=True)
    duracao = models.DurationField('Duração', choices=DURACAO_CHOICES, blank=True)
    preco = models.DecimalField('Preço', max_digits=10, decimal_places=2, blank=True)
    descricao = models.CharField('Descrição', max_length=250)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.nome_tratamento

class TipoGenero(models.TextChoices):
    MASCULINO = 'MASCULINO', 'MASCULINO'
    FEMININO = 'FEMININO', 'FEMININO'
    OUTRO = 'OUTRO', 'OUTRO'
    NAO = 'NÃO INFORMAR', 'NÃO INFORMAR'

class Cliente(models.Model):
    nome = models.CharField('Nome', max_length=200)
    dt_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    cpf = models.CharField('CPF', max_length=11, null=True, blank=True)
    telefone = models.CharField('Telefone', max_length=14)
    email = models.EmailField('E-mail', max_length=200)
    sexo = models.CharField('Gênero', max_length=25, choices=TipoGenero.choices, null=True, blank=True)
    observacoes = models.CharField('Observações', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.nome

class TipoAgendamento(models.TextChoices):
    AVALIACAO = 'AVALIAÇÃO', 'AVALIAÇÃO'
    PROCEDIMENTO = 'PROCEDIMENTO', 'PROCEDIMENTO'

class Agendamento(models.Model): 
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name='Cliente')
    tratamento = models.ForeignKey(Tratamento, on_delete=models.CASCADE, verbose_name='Tratamento') 
    data = models.DateField('Data', db_index=True)
    hora = models.TimeField('Horário')
    tipo_agendamento = models.CharField('Tipo de Agendamento', max_length=50, choices=TipoAgendamento.choices)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    def __str__(self):
        return f"{self.cliente.nome} - {self.tratamento.nome_tratamento} - {self.data} - {self.hora}"
    
    class Meta:
        ordering = ['-id']

class CategoriaDespesa(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome

class Despesa(models.Model):
    nome_despesa = models.CharField(max_length=50)
    categoria = models.ForeignKey(CategoriaDespesa, on_delete=models.PROTECT, related_name='despesas')
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    data_vencimento = models.DateField('Data de Vencimento', db_index=True)
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True, db_index=True)
    pago = models.BooleanField('Pago?', default=False, db_index=True)
    fornecedor = models.CharField('Fornecedor', max_length=100, blank=True, null=True)
    observacao = models.TextField('Observação', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.categoria} - R$ {self.valor} - Vencimento: {self.data_vencimento}"

class FormaPagamento(models.TextChoices):
    DINHEIRO = 'DINHEIRO', 'Dinheiro'
    CARTAO_CREDITO = 'CARTAO_CREDITO', 'Cartão de Crédito'
    CARTAO_DEBITO = 'CARTAO_DEBITO', 'Cartão de Débito'
    PIX = 'PIX', 'Pix'
    OUTRO = 'OUTRO', 'Outro'

class Receita(models.Model):
    agendamento = models.ForeignKey(
        'Agendamento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Agendamento relacionado',
        help_text='Selecione um agendamento se a receita estiver ligada a um serviço realizado.'
    )
    descricao = models.CharField('Descrição', max_length=255, blank=True, null=True)
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FormaPagamento.choices)
    recebido = models.BooleanField('Recebido?', default=False, db_index=True)
    data_recebimento = models.DateField('Data de Recebimento', null=True, blank=True, db_index=True)
    observacao = models.TextField('Observações', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        ordering = ['-data_recebimento', '-id']
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'

    def __str__(self):
        if self.agendamento:
            return f"{self.agendamento.cliente.nome} - R$ {self.valor} - {self.data_recebimento or 'A receber'}"
        return f"{self.descricao or 'Receita Avulsa'} - R$ {self.valor}"
    

class Caixa(models.Model):
    ano = models.PositiveIntegerField()
    mes = models.PositiveIntegerField()

    @property
    def data_inicial(self):
        return timezone.datetime(self.ano, self.mes, 1).date()

    @property
    def data_final(self):
        ultimo_dia = calendar.monthrange(self.ano, self.mes)[1]
        return timezone.datetime(self.ano, self.mes, ultimo_dia).date()

    @property
    def total_receitas(self):
        from .models import Receita
        return Receita.objects.filter(
            data__range=(self.data_inicial, self.data_final)
        ).aggregate(total=Sum('valor'))['total'] or 0

    @property
    def total_despesas(self):
        from .models import Despesa
        return Despesa.objects.filter(
            data__range=(self.data_inicial, self.data_final)
        ).aggregate(total=Sum('valor'))['total'] or 0

    @property
    def saldo(self):
        return self.total_receitas - self.total_despesas

    def __str__(self):
        return f"Caixa {self.mes}/{self.ano} - Saldo: R$ {self.saldo:.2f}"

    class Meta:
        verbose_name = "Caixa"
        verbose_name_plural = "Caixas"
        ordering = ['-ano', '-mes']