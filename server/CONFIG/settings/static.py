from .base import BASE_DIR
import os
from decouple import config

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Directories for local static files (optional)
STATICFILES_DIRS = [
    BASE_DIR / "static",  # assuming BASE_DIR is the root directory of your project
    # Other directories can be added here
]

# Not needed for local development, but typically used in production
# STATIC_ROOT = BASE_DIR / 'staticfiles'
# This is for serving static files in production
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Enable WhiteNoise to compress files and serve efficiently
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

IDRIVE_ENDPOINT = config("IDRIVE_ENDPOINT")
IDRIVE_ACCESS_KEY_ID = config("IDRIVE_ACCESS_KEY_ID")
IDRIVE_SECRET_ACCESS_KEY = config("IDRIVE_SECRET_ACCESS_KEY")
IDRIVE_BUCKET_NAME = config("IDRIVE_BUCKET_NAME")

# AWS_ACCESS_KEY_ID = IDRIVE_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY = IDRIVE_SECRET_ACCESS_KEY
# AWS_S3_ENDPOINT_URL = IDRIVE_ENDPOINT
# AWS_STORAGE_BUCKET_NAME = IDRIVE_BUCKET_NAME
# AWS_S3_REGION_NAME = None  # iDrive E2 typically doesn't use regions
# AWS_S3_CUSTOM_DOMAIN = f'{IDRIVE_BUCKET_NAME}.{IDRIVE_ENDPOINT}'


AWS_S3_ENDPOINT_URL = f'https://{IDRIVE_ENDPOINT}'
AWS_ACCESS_KEY_ID = IDRIVE_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = IDRIVE_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = IDRIVE_BUCKET_NAME
AWS_S3_SIGNATURE_VERSION = 's3v4'

# import boto3
# s3 = boto3.client('s3',
#                   endpoint_url=f'https://{IDRIVE_ENDPOINT}',
#                   aws_access_key_id=IDRIVE_ACCESS_KEY_ID,
#                   aws_secret_access_key=IDRIVE_SECRET_ACCESS_KEY
#                   )

# # Try uploading a test file
# s3.upload_file('/home/roji/UBUNTU/RTG_CODE/DJANGO/SKE_TECH_WORLD/CONFIG/settings/media.py',
#                IDRIVE_BUCKET_NAME, 'uploaded_file.py')
