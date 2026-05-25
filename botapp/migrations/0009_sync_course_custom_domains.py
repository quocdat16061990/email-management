import os
import requests
from django.db import migrations
from concurrent.futures import ThreadPoolExecutor, as_completed

def sync_custom_domains(apps, schema_editor):
    Course = apps.get_model('botapp', 'Course')
    CourseLink = apps.get_model('botapp', 'CourseLink')
    
    # 1. Xóa các khóa học tự tạo (không có spotlight_id)
    Course.objects.filter(spotlight_id__isnull=True).delete()
    Course.objects.filter(spotlight_id="").delete()
    
    # 2. Clear all web_link values and CourseLink records
    Course.objects.all().update(web_link="")
    CourseLink.objects.all().delete()
    
    # 2. Get the Voomly bearer token from settings
    from django.conf import settings
    token = settings.VOOMLY_BEARER_TOKEN
    
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "cache-control": "no-cache",
        "funnel-version": "2",
        "origin": "https://app.voomly.com",
        "player-version": "2",
        "pragma": "no-cache",
    }
    
    # 3. Get all courses with a spotlight_id
    courses_with_id = list(Course.objects.exclude(spotlight_id__isnull=True).exclude(spotlight_id=""))
    
    def fetch_domain(c_id, spotlight_id, c_name):
        detail_url = f"https://api.voomly.com/spotlights/{spotlight_id}"
        try:
            res = requests.get(detail_url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                cd = data.get("customDomain")
                if cd:
                    cd = cd.strip()
                    if not (cd.startswith("http://") or cd.startswith("https://")):
                        return c_id, f"https://{cd}"
                    return c_id, cd
        except Exception as err:
            print(f"Error fetching customDomain for course {c_name} ({spotlight_id}): {err}")
        return c_id, ""

    course_domains = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {
            executor.submit(fetch_domain, c.id, c.spotlight_id, c.name): c 
            for c in courses_with_id
        }
        for future in as_completed(futures):
            c_id, web_link = future.result()
            if web_link:
                course_domains[c_id] = web_link
                
    # 4. Update the web_link in the database
    for c in courses_with_id:
        new_link = course_domains.get(c.id, "")
        if new_link:
            c.web_link = new_link
            c.save(update_fields=["web_link"])

def reverse_sync(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('botapp', '0008_customer_is_verified_telegram_customer_telegram_otp_and_more'),
    ]

    operations = [
        migrations.RunPython(sync_custom_domains, reverse_code=reverse_sync),
    ]
