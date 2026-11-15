from django.db import migrations


def add_categories(apps, schema_editor):
    Category = apps.get_model("posts", "Category")
    for section in ("market", "lostfound"):
        for name in ("Electronics", "Books & study", "Clothing", "Accessories", "Home & dorm", "Other"):
            Category.objects.get_or_create(section=section, name=name)


class Migration(migrations.Migration):
    dependencies = [("posts", "0004_marketitem_image_marketitem_location_and_more")]
    operations = [migrations.RunPython(add_categories, migrations.RunPython.noop)]
