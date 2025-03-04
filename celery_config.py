import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruiter_platform_sonnet.settings')

# Create the celery app
app = Celery('recruiter_platform_sonnet')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    result_expires=3600,  # Results expire after 1 hour
    worker_max_tasks_per_child=500,  # Restart worker after 500 tasks
    task_time_limit=600,  # 10 minute timeout
    task_soft_time_limit=300,  # 5 minute soft timeout
    worker_concurrency=4,  # Number of worker processes
    task_default_queue='default',
    task_queues={
        'default': {},
        'evaluations': {
            'exchange': 'evaluations',
            'routing_key': 'evaluations',
        },
    },
    task_routes={
        'core.tasks.evaluate_assessment': {'queue': 'evaluations'},
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')