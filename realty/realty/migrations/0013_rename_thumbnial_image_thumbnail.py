# Generated by Django 4.2.1 on 2023-05-10 06:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('realty', '0012_image_source_image_thumbnial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='image',
            old_name='thumbnial',
            new_name='thumbnail',
        ),
    ]
