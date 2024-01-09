from django.conf import settings
from django.db import models

import teammgmt.models


# Create your models here.
class TournamentPlayer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)

    discord_user_id = models.CharField(max_length=20)
    discord_username = models.CharField(max_length=64, blank=True)
    discord_global_name = models.CharField(max_length=64, blank=True)
    discord_avatar = models.CharField(max_length=64, blank=True)

    osu_user_id = models.BigIntegerField()
    osu_username = models.CharField(max_length=64)
    osu_flag = models.CharField(max_length=4)

    is_organizer = models.BooleanField(default=False)
    team = models.ForeignKey(teammgmt.models.TournamentTeam,
                             related_name='players',
                             on_delete=models.PROTECT,
                             default=teammgmt.models.TournamentTeam.get_default_pk)
    in_roster = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.osu_username} ({self.osu_flag}|{self.discord_global_name})"

    class Meta:
        indexes = [
            models.Index(fields=['discord_user_id', 'osu_user_id']),
            models.Index(fields=['osu_user_id']),
            models.Index(fields=['team'])
        ]
