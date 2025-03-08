# Save this as a script and run it to check available URLs in your project
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruiter_platform.settings')
django.setup()

# Import Django's URL resolver
from django.urls import get_resolver

# Get all URL patterns
resolver = get_resolver()
url_patterns = sorted(resolver.reverse_dict.keys())

# Print all URL pattern names
print("Available URL names:")
for pattern in url_patterns:
    if isinstance(pattern, str):
        print(f"- {pattern}")