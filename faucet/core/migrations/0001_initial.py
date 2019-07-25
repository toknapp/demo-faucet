# Generated by Django 2.2.3 on 2019-07-25 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DonationRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=42)),
                ('ip', models.GenericIPAddressField()),
                ('requested', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
