from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("botapp", "0011_remove_course_spotlight_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customer",
            name="courses",
        ),
        migrations.AddField(
            model_name="chatgptaccount",
            name="is_visible_to_customers",
            field=models.BooleanField(default=False, verbose_name="Cho phép khách hàng nhìn thấy"),
        ),
        migrations.DeleteModel(
            name="CourseLink",
        ),
        migrations.DeleteModel(
            name="Enrollment",
        ),
        migrations.DeleteModel(
            name="Course",
        ),
    ]
