from django.urls import path
from rest_framework.routers import DefaultRouter

from businesses.views import (
    AdminApplicationReviewView,
    AdminApplicationViewSet,
    AdminBusinessStatsView,
    AdminBusinessStopPartnershipView,
    AdminBusinessViewSet,
    ApplicationDetailView,
    ApplicationWizardStep1View,
    ApplicationWizardStepUpdateView,
    CategoryViewSet,
    MyApplicationsView,
    MyBusinessDashboardView,
    MyBusinessView,
    MyCashierDetailView,
    MyCashierListCreateView,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("admin/applications", AdminApplicationViewSet, basename="admin-applications")
router.register("admin/businesses", AdminBusinessViewSet, basename="admin-businesses")

urlpatterns = [
    # ---- Ariza qoldirish (wizard) ----
    path("applications/", MyApplicationsView.as_view(), name="my-applications"),
    path("applications/step1/", ApplicationWizardStep1View.as_view(), name="application-step1"),
    path("applications/<uuid:pk>/step/<int:step>/", ApplicationWizardStepUpdateView.as_view(), name="application-step"),
    path("applications/<uuid:pk>/", ApplicationDetailView.as_view(), name="application-detail"),

    # ---- Admin: ariza va biznes boshqaruvi ----
    path("admin/applications/<uuid:pk>/review/", AdminApplicationReviewView.as_view(), name="admin-application-review"),
    path("admin/businesses/<uuid:pk>/stop-partnership/", AdminBusinessStopPartnershipView.as_view(), name="admin-business-stop"),
    path("admin/businesses/<uuid:pk>/stats/", AdminBusinessStatsView.as_view(), name="admin-business-stats"),

    # ---- Biznes egasi ----
    path("my-business/", MyBusinessView.as_view(), name="my-business"),
    path("my-business/dashboard/", MyBusinessDashboardView.as_view(), name="my-business-dashboard"),
    path("my-business/cashiers/", MyCashierListCreateView.as_view(), name="my-cashiers"),
    path("my-business/cashiers/<uuid:pk>/", MyCashierDetailView.as_view(), name="my-cashier-detail"),
] + router.urls
