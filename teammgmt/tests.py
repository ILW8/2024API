import datetime
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from teammgmt.models import TournamentTeam
from teammgmt.views import TournamentTeamViewSet
from userauth.authentication import IsSuperUser
from userauth.models import TournamentPlayer
from rest_framework.test import APIRequestFactory


class TestRegistrationCutoffTestCase(TestCase):
    def setUp(self):
        # create our users
        self.tourney_team = TournamentTeam.objects.create(osu_flag="SH")
        self.tourney_users = []
        for i in range(11):
            user = User.objects.create(pk=i, username=f"user_{i}")
            self.tourney_users.append(
                TournamentPlayer.objects.create(user=user,
                                                team=self.tourney_team,
                                                osu_user_id=i,
                                                discord_user_id=i,
                                                osu_stats_updated=datetime.datetime.now(tz=datetime.timezone.utc))
            )

    def test_roster_change_too_early(self):
        factory = APIRequestFactory()
        request = factory.patch(f'/registrants/update_users')
        members_view = TournamentTeamViewSet.as_view({'patch': 'members'}, permission_classes=[])
        settings.TEAM_ROSTER_REGISTRATION_START = (datetime.datetime.now(tz=datetime.timezone.utc) +
                                                   datetime.timedelta(days=5))

        res = members_view(request, pk=self.tourney_team.pk)

        self.assertContains(res, "Registration opens in", status_code=403)

    def test_roster_change_ok(self):
        factory = APIRequestFactory()
        request = factory.patch(f'/registrants/update_users')
        members_view = TournamentTeamViewSet.as_view({'patch': 'members'}, permission_classes=[])
        settings.TEAM_ROSTER_REGISTRATION_START = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
        settings.TEAM_ROSTER_REGISTRATION_END = datetime.datetime.now(tz=datetime.timezone.utc) + timedelta(days=1)

        res = members_view(request, pk=self.tourney_team.pk)

        self.assertContains(res, "required field", status_code=400)
        self.assertContains(res, "missing", status_code=400)

    def test_roster_change_too_late(self):
        factory = APIRequestFactory()
        request = factory.patch(f'/registrants/update_users')
        members_view = TournamentTeamViewSet.as_view({'patch': 'members'}, permission_classes=[])
        settings.TEAM_ROSTER_REGISTRATION_START = (datetime.datetime.now(tz=datetime.timezone.utc) -
                                                   datetime.timedelta(days=10))
        settings.USER_REGISTRATION_END = (datetime.datetime.now(tz=datetime.timezone.utc) -
                                          datetime.timedelta(days=5))
        settings.TEAM_ROSTER_SELECTION_END = (datetime.datetime.now(tz=datetime.timezone.utc) -
                                              datetime.timedelta(days=2))

        res = members_view(request, pk=self.tourney_team.pk)
        self.assertContains(res, "Roster selection ", status_code=403)

    def test_roster_after_regs_end(self):
        factory = APIRequestFactory()
        request = factory.patch(f'/registrants/update_users')
        members_view = TournamentTeamViewSet.as_view({'patch': 'members'}, permission_classes=[])
        settings.TEAM_ROSTER_REGISTRATION_START = (datetime.datetime.now(tz=datetime.timezone.utc) -
                                                   datetime.timedelta(days=10))
        settings.USER_REGISTRATION_END = (datetime.datetime.now(tz=datetime.timezone.utc) -
                                          datetime.timedelta(days=1))
        settings.TEAM_ROSTER_SELECTION_END = (datetime.datetime.now(tz=datetime.timezone.utc) +
                                              datetime.timedelta(days=2))

        res = members_view(request, pk=self.tourney_team.pk)
        self.assertContains(res, "required field", status_code=400)
        self.assertContains(res, "missing", status_code=400)

    # def test_roster_after_regs_end(self):
    def test_staff_cannot_manage_tournament_teams(self):
        request = APIRequestFactory().get(f'/teams/{self.tourney_team.osu_flag}/members')
        request.user = User.objects.create(is_staff=True)
        members_view = TournamentTeamViewSet.as_view({'get': 'members'}, permission_classes=[])
        has_permission = IsSuperUser().has_permission(request, members_view)

        self.assertFalse(has_permission)

    def test_superuser_can_manage_tournament_teams(self):
        request = APIRequestFactory().get(f'/teams/{self.tourney_team.osu_flag}/members')
        request.user = User.objects.create(is_superuser=True)
        members_view = TournamentTeamViewSet.as_view({'get': 'members'}, permission_classes=[])
        has_permission = IsSuperUser().has_permission(request, members_view)

        self.assertTrue(has_permission)


class TestTournamentUserConstraints(TestCase):
    def test_must_be_in_roster_for_captain(self):
        with self.assertRaises(IntegrityError) as expect:
            user = User.objects.create()
            tourney_player = TournamentPlayer.objects.create(
                user=user,
                osu_user_id=1,
                discord_user_id=1,
                osu_stats_updated=datetime.datetime.now(tz=datetime.timezone.utc),
                is_captain=True,
                in_roster=False
            )
            tourney_player.save()
        self.assertTrue("captain_only_if_also_in_roster" in str(expect.exception))
