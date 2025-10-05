MIDDLEWARE = [
    'main.tenancy.middlewares.AppendSlashMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise here

    'django.contrib.sessions.middleware.SessionMiddleware',
    'main.tenancy.middlewares.RequestThreadLocalMiddleware',
    'main.tenancy.middlewares.UnifiedTenantMiddleware',

    "corsheaders.middleware.CorsMiddleware",

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

