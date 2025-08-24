from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from django.db import models
import calendar

# =============================
# Usuário
# =============================
class CustomUser(AbstractUser):
    profile_picture = models.ImageField(
        "Foto de Perfil",
        upload_to='profile_pics/',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.first_name or self.username


# =============================
# Tratamentos
# =============================
DURACAO_CHOICES = [
    (30, '30 minutos'),
    (60, '1 hora'),
    (90, '1 hora e 30 minutos'),
    (120, '2 horas'),
    (150, '2 horas e 30 minutos'),
    (180, '3 horas'),
    (210, '3 horas e 30 minutos'),
    (240, '4 horas'),
    (270, '4 horas e 30 minutos'),
    (300, '5 horas'),
    (330, '5 horas e 30 minutos'),
    (360, '6 horas'),
    (390, '6 horas e 30 minutos'),
    (420, '7 horas'),
    (450, '7 horas e 30 minutos'),
    (480, '8 horas'),
]


class TiposTratamentos(models.TextChoices):
    FACIAL = 'Facial', 'Facial'
    LABIAL = 'Labial', 'Labial'
    GLUTEOS = 'Glúteos', 'Glúteos'
    CORPORAL = 'Corporal', 'Corporal'


class Tratamento(models.Model):
    nome_tratamento = models.CharField('Tratamento', max_length=100)
    tipo_tratamento = models.CharField(
        'Tipo Tratamento',
        max_length=20,
        choices=TiposTratamentos.choices,
        null=True,
        blank=True
    )
    duracao = models.PositiveIntegerField(
        "Duração (minutos)", choices=DURACAO_CHOICES, blank=True, null=True
    )
    preco = models.DecimalField('Preço', max_digits=10, decimal_places=2, blank=True, null=True)
    descricao = models.CharField('Descrição', max_length=250)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.nome_tratamento

    @property
    def duracao_timedelta(self):
        return timedelta(minutes=self.duracao or 0)


# =============================
# Clientes
# =============================
class TipoGenero(models.TextChoices):
    MASCULINO = 'MASCULINO', 'Masculino'
    FEMININO = 'FEMININO', 'Feminino'
    OUTRO = 'OUTRO', 'Outro'
    NAO = 'NAO_INFORMAR', 'Não Informar'


class Cliente(models.Model):
    nome = models.CharField('Nome', max_length=200)
    dt_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, null=True, blank=True)
    telefone = models.CharField('Telefone', max_length=14)
    email = models.EmailField('E-mail', max_length=200)
    sexo = models.CharField('Gênero', max_length=25, choices=TipoGenero.choices, null=True, blank=True)
    observacoes = models.CharField('Observações', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    def __str__(self):
        return self.nome


# =============================
# Agendamentos
# =============================
class TipoAgendamento(models.TextChoices):
    AVALIACAO = 'AVALIACAO', 'Avaliação'
    PROCEDIMENTO = 'PROCEDIMENTO', 'Procedimento'


class Agendamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name='Cliente')
    tratamento = models.ForeignKey(Tratamento, on_delete=models.CASCADE, verbose_name='Tratamento')
    data = models.DateField('Data', db_index=True)
    hora = models.TimeField('Horário')
    tipo_agendamento = models.CharField('Tipo de Agendamento', max_length=20, choices=TipoAgendamento.choices)

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
        ('CONCLUIDO', 'Concluído'),
    ]
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    # Campo auxiliar para rastrear se estoque já foi descontado
    _estoque_descontado = False

    def __str__(self):
        return f"{self.cliente.nome} - {self.tratamento.nome_tratamento} - {self.data} - {self.hora}"

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(fields=['cliente', 'data', 'hora'], name='unique_cliente_horario')
        ]

    def save(self, *args, **kwargs):
        """Desconta produtos do estoque quando agendamento é concluído"""
        try:
            original = Agendamento.objects.get(pk=self.pk)
            status_anterior = original.status
        except Agendamento.DoesNotExist:
            status_anterior = None

        super().save(*args, **kwargs)  # Salva primeiro para garantir ID

        # Se mudou para concluído e ainda não descontou estoque
        if self.status == 'CONCLUIDO' and status_anterior != 'CONCLUIDO' and not self._estoque_descontado:
            for consumo in self.consumos.all():  # usa os produtos ligados ao agendamento
                produto = consumo.produto
                if produto.quantidade_estoque >= consumo.quantidade:
                    produto.quantidade_estoque -= consumo.quantidade
                    produto.save()
                    # Cria movimentação de estoque
                    from .models import MovimentacaoEstoque
                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        tipo='SAIDA',
                        quantidade=consumo.quantidade,
                        motivo=f'Uso no agendamento {self.id} - {self.cliente.nome}'
                    )
            self._estoque_descontado = True



# =============================
# Despesas
# =============================
class CategoriaDespesa(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Despesa(models.Model):
    nome_despesa = models.CharField('Despesa', max_length=50)
    categoria = models.ForeignKey(CategoriaDespesa, on_delete=models.PROTECT, related_name='despesas')
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    data_vencimento = models.DateField('Data de Vencimento', db_index=True)
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True, db_index=True)
    pago = models.BooleanField('Pago?', default=False, db_index=True)
    fornecedor = models.CharField('Fornecedor', max_length=100, blank=True, null=True)
    observacao = models.TextField('Observação', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def esta_atrasada(self):
        return not self.pago and self.data_vencimento < timezone.now().date()

    def __str__(self):
        return f"{self.categoria} - R$ {self.valor} - Vencimento: {self.data_vencimento}"


# =============================
# Receitas
# =============================
class FormaPagamento(models.TextChoices):
    DINHEIRO = 'DINHEIRO', 'Dinheiro'
    CARTAO_CREDITO = 'CARTAO_CREDITO', 'Cartão de Crédito'
    CARTAO_DEBITO = 'CARTAO_DEBITO', 'Cartão de Débito'
    PIX = 'PIX', 'Pix'
    OUTRO = 'OUTRO', 'Outro'


class Receita(models.Model):
    agendamento = models.ForeignKey(
        Agendamento,
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


# =============================
# Caixa
# =============================
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
        return Receita.objects.filter(
            data_recebimento__range=(self.data_inicial, self.data_final),
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

    @property
    def total_despesas(self):
        return Despesa.objects.filter(
            data_pagamento__range=(self.data_inicial, self.data_final),
            pago=True
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


# =============================
# Produtos e Estoque
# =============================
class Produto(models.Model):
    nome = models.CharField('Nome do Produto', max_length=200)
    descricao = models.TextField('Descrição', blank=True, null=True)
    marca = models.CharField('Marca', max_length=100, blank=True, null=True)
    data_validade = models.DateField('Data de Validade', blank=True, null=True)
    preco_custo = models.DecimalField('Preço de Custo', max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField('Preço de Venda', max_digits=10, decimal_places=2)
    quantidade_estoque = models.PositiveIntegerField('Quantidade em Estoque', default=0)
    estoque_minimo = models.PositiveIntegerField('Estoque Mínimo', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def atualizar_estoque(self, tipo, quantidade):
        """Atualiza estoque com validação de entrada/saída"""
        if tipo == 'ENTRADA':
            self.quantidade_estoque += quantidade
        elif tipo == 'SAIDA':
            if quantidade > self.quantidade_estoque:
                raise ValueError(f"Estoque insuficiente: {self.quantidade_estoque} disponível")
            self.quantidade_estoque -= quantidade
        else:
            raise ValueError("Tipo de movimentação inválido")
        self.save()

    def __str__(self):
        return self.nome


class MovimentacaoEstoque(models.Model):
    TIPO_MOVIMENTACAO = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_MOVIMENTACAO)
    quantidade = models.PositiveIntegerField('Quantidade')
    motivo = models.CharField('Motivo', max_length=255, blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Atualiza estoque automaticamente ao salvar movimentação"""
        if not self.pk:  # só na criação
            self.produto.atualizar_estoque(self.tipo, self.quantidade)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} - {self.quantidade}"


class ConsumoProduto(models.Model):
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name="consumos",
        verbose_name="Agendamento"
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        verbose_name="Produto"
    )
    quantidade = models.PositiveIntegerField("Quantidade utilizada")

    def __str__(self):
        return f"{self.agendamento} - {self.produto.nome} ({self.quantidade})"
