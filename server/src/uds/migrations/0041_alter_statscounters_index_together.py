# Generated by Django 3.2 on 2021-05-12 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0040_auto_20210422_1340'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='statscounters',
            index_together={('owner_type', 'counter_type', 'stamp'), ('owner_type', 'stamp')},
        ),
    ]