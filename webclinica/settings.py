# settings.py
from pathlib import Path
import os
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ----- SECRET & DEBUG -----
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = os.environ.get('DJANGO_DEBUG', '1').lower() in ('1', 'true', 'yes')

# Em produção: exigir a SECRET_KEY
if not DEBUG and not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in production environment")

# ----- Hosts -----
# Use variável de ambiente DJANGO_ALLOWED_HOSTS como 'dominio.com,www.dominio.com,127.0.0.1'
ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'clinicadasarabia.com.br,www.clinicadasarabia.com.br,localhost,127.0.0.1,72.60.8.166'
).split(',')

# ----- Installed apps -----
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'clinica',
]

# ----- Middleware (WhiteNoise logo após SecurityMiddleware) -----
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <<-- importante: após SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webclinica.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Recomendo usar BASE_DIR / 'templates' para caminhos absolutos
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webclinica.wsgi.application'

# -----------------------------------------------------------
# Configurações específicas para produção (quando DEBUG == False)
# -----------------------------------------------------------
if not DEBUG:
    # Segurança HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Quando estiver atrás do Nginx (proxy) para que Django saiba do HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Origem confiáveis para CSRF — especifique com esquema (https://...)
    CSRF_TRUSTED_ORIGINS = os.environ.get(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'https://clinicadasarabia.com.br,https://www.clinicadasarabia.com.br'
    ).split(',')

    # Banco de dados de produção (Postgres) — valores via env
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    # Desenvolvimento - SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation (mantive como você tinha)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ----- Static & Media -----
STATIC_URL = '/static/'
# pasta onde collectstatic colocará todos os arquivos para o Nginx servir
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# WhiteNoise storage (atenção: CompressedManifest pode quebrar se faltar arquivos referenciados)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Mensagens
MESSAGE_TAGS = {
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

AUTH_USER_MODEL = 'clinica.CustomUser'

# Jazzmin (mantive seu bloco)
JAZZMIN_SETTINGS = {
    'site_title': 'Clínica Das Árabia',
    'site_header': 'Clínica Das Árabia',
    'site_brand': 'Clínica Das Árabia',
    'site_logo': "images/CDA.png",
    "user_avatar": "profile_picture",
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'clinica.Agendamento': 'fa-solid fa-calendar-days',
        'clinica.Cliente': 'fa-solid fa-people-roof',
        'clinica.Tratamento': 'fa-solid fa-syringe',
        'clinica.Caixa': 'fa-solid fa-money-bill-transfer',
        'clinica.Despesa': 'fa-solid fa-file-invoice-dollar',
        'clinica.Receita': 'fa-solid fa-money-bill-trend-up',
        'clinica.CustomUser': 'fa-solid fa-user-plus',
        'clinica.Produto': 'fa-solid fa-flask-vial',
        'clinica.MovimentacaoEstoque': 'fa-regular fa-share-from-square',
        'clinica.CategoriaDespesa': 'fa-regular fa-pen-to-square',
    },
    'welcome_sign': 'Bem-vindo(a) a Clínica das Árabia',
    'copyright': 'Clínica das Árabia',
    'search_model': ['tratamento.Tratamento'],
    "custom_css": "css/custom-jazzmin.css",
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
