import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webclinica.settings")
django.setup()

from clinica.models import Cliente, Agendamento
from django.db import transaction
from collections import Counter, defaultdict

# ========================
# 1. Limpeza de CPFs duplicados
# ========================
def clean_cpfs():
    print("Verificando CPFs duplicados...")
    cpfs = Cliente.objects.exclude(cpf__isnull=True).exclude(cpf__exact='').values_list('cpf', flat=True)
    duplicates = [cpf for cpf, count in Counter(cpfs).items() if count > 1]

    if duplicates:
        print(f"CPFs duplicados encontrados: {duplicates}")
        with transaction.atomic():
            for cpf in duplicates:
                clientes = Cliente.objects.filter(cpf=cpf).order_by('id')
                # mantém o primeiro
                for c in clientes[1:]:
                    print(f"Removendo CPF do cliente {c.nome} (id: {c.id})")
                    c.cpf = None
                    c.save()
    else:
        print("Nenhum CPF duplicado encontrado.")

# ========================
# 2. Limpeza de Agendamentos duplicados
# ========================
def clean_agendamentos():
    print("Verificando agendamentos duplicados...")
    agendamentos = Agendamento.objects.all().order_by('id')
    seen = defaultdict(list)

    for a in agendamentos:
        key = (a.cliente_id, a.data, a.hora)
        seen[key].append(a)

    with transaction.atomic():
        for key, duplicates in seen.items():
            if len(duplicates) > 1:
                print(f"Duplicados encontrados para cliente {key[0]} na data {key[1]} horário {key[2]}")
                # mantém o primeiro, remove os outros
                for a in duplicates[1:]:
                    print(f"Removendo agendamento duplicado id: {a.id}")
                    a.delete()

# ========================
# Executa
# ========================
if __name__ == "__main__":
    clean_cpfs()
    clean_agendamentos()
    print("Limpeza concluída!")
