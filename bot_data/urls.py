from django.urls import path
from . import views

urlpatterns = [
    path('api/bot-data/', views.BotDataView.as_view(), name='bot_data_api'),
    path('api/bot-data/check/<int:user_id>/', views.CheckUserView.as_view(), name='check_user_api'),
    path('api/teams/', views.TeamsListView.as_view(), name='teams_api'),
    path('api/solo-players/', views.SoloPlayersListView.as_view(), name='solo_players_api'),
    path('api/my-team/<int:user_id>/', views.MyTeamView.as_view(), name='my_team_api'),
    path('api/join-team/', views.JoinTeamView.as_view(), name='join_team_api'),
    path('api/remove-member/', views.RemoveMemberView.as_view(), name='remove_member_api'),
    path('api/channels/', views.SubscriptionChannelsView.as_view(), name='channels_api'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
