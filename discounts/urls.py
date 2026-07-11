from django.urls import path
from rest_framework.routers import DefaultRouter

from discounts.views import (
    AdminDiscountChangeRequestViewSet,
    AdminDiscountChangeReviewView,
    CashierApplyDiscountView,
    DiscountChangeRequestCreateView,
    DiscountHistoryExportView,
    DiscountHistoryView,
    DiscountStatisticsView,
    MyDiscountInfoView,
)

router = DefaultRouter()
router.register("admin/discount-requests", AdminDiscountChangeRequestViewSet, basename="admin-discount-requests")

urlpatterns = [
    path("my-business/discount/", MyDiscountInfoView.as_view(), name="my-discount-info"),
    path("my-business/discount/change-request/", DiscountChangeRequestCreateView.as_view(), name="discount-change-request"),
    path("my-business/discount/history/", DiscountHistoryView.as_view(), name="discount-history"),
    path("my-business/discount/history/export/", DiscountHistoryExportView.as_view(), name="discount-history-export"),
    path("my-business/discount/statistics/", DiscountStatisticsView.as_view(), name="discount-statistics"),

    path("cashier/apply-discount/", CashierApplyDiscountView.as_view(), name="cashier-apply-discount"),

    path("admin/discount-requests/<uuid:pk>/review/", AdminDiscountChangeReviewView.as_view(), name="admin-discount-review"),
] + router.urls
