from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0019_refactor_screenpagebinding_global"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="screenpagebinding",
            name="device_ids",
        ),
    ]
