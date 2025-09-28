import os
import time
import tarfile
import boto3
from botocore.client import Config
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

s3_url = os.environ['S3_URL']
s3_port = os.environ.get('S3_PORT', '9000')
access_key = os.environ['S3_USERNAME']
secret_key = os.environ['S3_PASSWORD']
bucket_name = os.environ['BUCKET_NAME']
interval = int(os.environ.get('BACKUP_INTERVAL', '3600'))
max_total_size_gb = float(os.environ.get('MAX_TOTAL_SIZE_GB', '20'))  # Максимальный размер всех бэкапов
max_backups = int(os.environ.get('MAX_BACKUPS', '20'))  # Максимальное количество бэкапов
world_name = os.environ['WORLD_NAME']

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=f"{s3_url}:{s3_port}",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def ensure_bucket():
    try:
        s3.head_bucket(Bucket=bucket_name)
    except:
        s3.create_bucket(Bucket=bucket_name)

def list_backups():
    # Получить список всех бэкапов в бакете
    resp = s3.list_objects_v2(Bucket=bucket_name, Prefix="world_")
    if 'Contents' not in resp:
        return []
    backups = []
    for obj in resp['Contents']:
        backups.append({
            'Key': obj['Key'],
            'Size': obj['Size'],
            'LastModified': obj['LastModified']
        })
    # Сортируем по времени создания (свежее -- в начале)
    backups.sort(key=lambda x: x['LastModified'], reverse=True)
    return backups

def remove_old_backups():
    backups = list_backups()
    total_size = sum(b['Size'] for b in backups)
    total_size_gb = total_size / (1024 ** 3)

    # Если превышен лимит по количеству или размеру -- удаляем старые
    while len(backups) > max_backups or total_size_gb > max_total_size_gb:
        oldest = backups[-1]
        print(f"Removing old backup: {oldest['Key']}")
        s3.delete_object(Bucket=bucket_name, Key=oldest['Key'])
        backups.pop()
        total_size = sum(b['Size'] for b in backups)
        total_size_gb = total_size / (1024 ** 3)

def do_backup():
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = f"/tmp/minecraft_world_{ts}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(f"/minecraft/{world_name}", arcname="world")
    s3.upload_file(archive_path, bucket_name, f"world_{ts}.tar.gz")
    os.remove(archive_path)

def print_backup_stats():
    backups = list_backups()
    total_size = sum(b['Size'] for b in backups)
    print(f"Backups count: {len(backups)}")
    print(f"Total backup size: {total_size / (1024 ** 3):.2f} GB")

if __name__ == "__main__":
    print("Backup script started")
    ensure_bucket()
    while True:
        print("Starting backup...")
        do_backup()
        print("Backup uploaded.")
        remove_old_backups()
        print_backup_stats()
        print("Done. Sleeping.")
        time.sleep(interval)
