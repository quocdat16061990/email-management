import logging
from django.core.management.base import BaseCommand
from botapp.services import sync_courses_from_voomly, sync_all_students_from_voomly

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Synchronize courses and students from Voomly"

    def handle(self, *args, **options):
        self.stdout.write("Starting Voomly synchronization...")
        try:
            self.stdout.write("Step 1: Synchronizing courses...")
            course_result = sync_courses_from_voomly()
            self.stdout.write(self.style.SUCCESS(f"Courses sync completed: {course_result}"))

            self.stdout.write("Step 2: Synchronizing all students...")
            student_result = sync_all_students_from_voomly()
            self.stdout.write(self.style.SUCCESS(f"Students sync completed: {student_result}"))
            
            self.stdout.write(self.style.SUCCESS("Voomly synchronization finished successfully!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during Voomly sync: {e}"))
            logger.error("Voomly sync command error", exc_info=True)
