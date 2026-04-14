from django.urls import include, path
from . import views
from rest_framework.routers import DefaultRouter
# shop/urls.py


router = DefaultRouter()
router.register(r'plans', views.SavingPlanApiset, basename='saving')
router.register(r'user-plans', views.UserSavingApiset, basename='user-saving')
router.register(r'transactions', views.TransactionApiset, basename='transactions')
router.register(r'admin/users', views.UsersApiset, basename='users')
urlpatterns = [
    path('', include(router.urls)),
    path('admin/stats/', views.AdminStatsView.as_view(), name='admin-stats'),
]
