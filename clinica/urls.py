from django.urls import path
from clinica.views import *

urlpatterns = [
    path('', index, name='index'),  # Alteração aqui
    path('tratamento/', tratamento, name='tratamentos'),
    path('agendamento/', agendamento, name='agendamento'),
]
