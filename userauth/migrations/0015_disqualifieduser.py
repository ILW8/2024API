# Generated by Django 4.2.6 on 2024-01-28 04:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0014_tournamentplayerbadge_userauth_to_user_id_e2d512_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisqualifiedUser',
            fields=[
                ('osu_user_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
            ],
        ),
    ]
