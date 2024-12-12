"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
# Config
from .config import GAME_MODES, AUTH_SERVICE_URL

GAME_MODES = GAME_MODES
AUTH_SERVICE_URL = AUTH_SERVICE_URL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-96g9x-miw#=a!lql&#jsh!@umdr(ess*dlt6f1hslksct)ohaj'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
	'gamemanager',
	'*',
]


# Application definition

INSTALLED_APPS = [
	'daphne',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'game_manager',
	'matchmaking',
	'admin_manager',
	'rest_framework',
	'channels',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
	'https://a32d-81-65-161-75.ngrok-free.app',
]


ROOT_URLCONF = 'project.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [os.path.join(BASE_DIR, "templates/")],
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

WSGI_APPLICATION = 'project.wsgi.application'
ASGI_APPLICATION = 'project.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

def read_secret(secret_name):
	file_path = os.environ.get(f'{secret_name}_FILE')
	if file_path and os.path.exists(file_path):
		with open(file_path, 'r') as file:
			return file.read().strip()
	return None

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.environ.get('DB_NAME_2'),
		'USER': read_secret('DB_USER'),
		'PASSWORD': read_secret('DB_PASSWORD'),
		'HOST': os.environ.get('DB_HOST'),
		'PORT': os.environ.get('DB_PORT'),
	}
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Backend cache for channels

CHANNEL_LAYERS = {
	'default': {
		'BACKEND': 'channels_redis.core.RedisChannelLayer',
		'CONFIG': {
			"hosts": [('redis', 6379)],
		},
	},
}


CACHES = {
	"default": 
	{
		"BACKEND": "django_redis.cache.RedisCache",
		"LOCATION": "redis://redis:6379/1",
		"OPTIONS":
		{
			"CLIENT_CLASS": "django_redis.client.DefaultClient",
		}
	}
}

# Log

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'verbose': {
			'format': '{levelname} {module} {message}',
			'style': '{',
		},
		'simple': {
			'format': '{levelname} {message}',
			'style': '{',
		},
	},
	'handlers': {
		'console': {
			'level': 'DEBUG',
			'class': 'logging.StreamHandler',
			'formatter': 'simple',
		},
		'file': {
			'level': 'DEBUG',
			'class': 'logging.FileHandler',
			'filename': os.path.join(BASE_DIR, 'django_debug.log'),
			'formatter': 'verbose',
			'mode': 'w',
		},
	},
	'loggers': {
		'__name__': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
		'game_manager': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
		'matchmaking': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
		'admin_manager': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
		'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
	},
}
