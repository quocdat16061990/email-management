from django.urls import path

from .views import (
    api_chatgpt_accounts_create,
    api_chatgpt_accounts_delete,
    api_chatgpt_accounts_list,
    api_chatgpt_accounts_update,
    api_dashboard_create,
    api_dashboard_delete,
    api_dashboard_list,
    api_dashboard_stats,
    api_dashboard_update,
    api_customer_chatgpt_access_update,
    api_login,
    api_logout,
    chatgpt_accounts_view,
    dashboard_view,
    login_view,
    logout_view,
)


urlpatterns = [
    path("", login_view, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("chatgpt-accounts/", chatgpt_accounts_view, name="chatgpt_accounts"),
    path("logout/", logout_view, name="logout"),
    path("api/login/", api_login, name="api_login"),
    path("api/logout/", api_logout, name="api_logout"),
    path("api/dashboard/", api_dashboard_list, name="api_dashboard_list"),
    path("api/dashboard/create/", api_dashboard_create, name="api_dashboard_create"),
    path("api/dashboard/<int:id>/", api_dashboard_update, name="api_dashboard_update"),
    path("api/dashboard/<int:id>/delete/", api_dashboard_delete, name="api_dashboard_delete"),
    path("api/customers/<int:id>/chatgpt-access/", api_customer_chatgpt_access_update, name="api_customer_chatgpt_access_update"),
    path("api/dashboard/stats/", api_dashboard_stats, name="api_dashboard_stats"),
    path("api/chatgpt-accounts/", api_chatgpt_accounts_list, name="api_chatgpt_accounts_list"),
    path("api/chatgpt-accounts/create/", api_chatgpt_accounts_create, name="api_chatgpt_accounts_create"),
    path("api/chatgpt-accounts/<int:id>/update/", api_chatgpt_accounts_update, name="api_chatgpt_accounts_update"),
    path("api/chatgpt-accounts/<int:id>/delete/", api_chatgpt_accounts_delete, name="api_chatgpt_accounts_delete"),
]
