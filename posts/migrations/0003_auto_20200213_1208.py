# Generated by Django 2.2 on 2020-02-13 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20200120_2045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(),
        ),
    ]
