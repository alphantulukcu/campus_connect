# Generated by Django 5.0 on 2023-12-16 19:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campus_connect', '0004_entry_likes_number_post_favorites_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_text', models.CharField(max_length=1000)),
                ('entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campus_connect.entry')),
                ('post', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campus_connect.post')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campus_connect.profile')),
            ],
            options={
                'db_table': 'report',
            },
        ),
    ]
