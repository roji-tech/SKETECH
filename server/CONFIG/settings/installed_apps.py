# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',


    # installed apps
    'django_extensions',
    'django_seed',
    'django_filters',
    'storages',
    "corsheaders",
    "rest_framework",
    "djoser",
    "rest_framework_simplejwt.token_blacklist",

    'main',
    'main.tenancy',
    'api',
    'library',
    'myquiz',
    # 'attendance',
    'report',
    'notification',
    'event',
]
