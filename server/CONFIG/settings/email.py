# DEFAULT_FROM_EMAIL = "rojitech9@gmail.com"

ADMINS = [
    ("ROJITECH", "rojitech@gmail.com"),
]


# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# EMAIL_HOST = "localhost"
# EMAIL_HOST_USER = ""
# EMAIL_HOST_PASSWORD = ""
# EMAIL_PORT = 2525



from decouple import config


# EMAIL_BACKEND = 'gmailapi_backend.mail.GmailBackend'
# GMAIL_API_CLIENT_ID = config("MY_EMAIL_BACKEND", default="console")
# GMAIL_API_CLIENT_SECRET = config("MY_EMAIL_BACKEND", default="console")
# GMAIL_API_REFRESH_TOKEN = config("MY_EMAIL_BACKEND", default="console")
ADMINS = []
ALL_ADMINS = {
    "DEVELOPER": config(
        "DEVELOPER_EMAIL", default="EduTechacademy@gmail.com"),
    "ADMIN_1": config("ADMIN_1_EMAIL", default=""),
    "ADMIN_2": config("ADMIN_2_EMAIL", default=""),
    "ADMIN_3": config("ADMIN_3_EMAIL", default=""),
}

for admin in ALL_ADMINS.items():
    if "@" in admin[1]:
        ADMINS.append(admin)


MANAGERS = ADMINS


NO_REPLY_EMAIL = config("NO_REPLY_EMAIL", default="noreply@myworldesim.com")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=True, cast=bool)


MY_EMAIL_BACKEND = config("MY_EMAIL_BACKEND", default="smtp")
EMAIL_BACKEND = F"django.core.mail.backends.{MY_EMAIL_BACKEND}.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="localhost")



EMAIL_HOST = "smtp.gmail.com"
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_PORT = config("EMAIL_PORT", default=2525)


DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
