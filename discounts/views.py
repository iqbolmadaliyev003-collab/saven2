import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.models import Business, Cashier
from discounts.models import DiscountChangeRequest, DiscountUsage
from discounts.serializers import (
    DiscountChangeRequestCreateSerializer,
    DiscountChangeRequestSerializer,
    DiscountChangeReviewSerializer,
    DiscountStatSerializer,
    DiscountUsageCreateSerializer,
    DiscountUsageSerializer,
)
from users.models import User
from users.permissions import IsAdminRole, IsBusinessOwner, IsCashier


# ==================== BIZNES EGASI: Chegirmalar ====================


class MyDiscountInfoView(APIView):
    """Chegirmalar -> Joriy foizlar ro'yxati."""

    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get(self, request):
        business = get_object_or_404(Business, owner=request.user)
        current_percent = business.application.discount_percent if business.application else None
        pending = DiscountChangeRequest.objects.filter(
            business=business, status=DiscountChangeRequest.Status.PENDING
        ).first()
        return Response(
            {
                "current_percent": current_percent,
                "pending_request": DiscountChangeRequestSerializer(pending).data if pending else None,
            }
        )


class DiscountChangeRequestCreateView(APIView):
    """Foiz o'zgartirish -> So'rov -> Admin."""

    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def post(self, request):
        business = get_object_or_404(Business, owner=request.user)
        serializer = DiscountChangeRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_percent = business.application.discount_percent if business.application else 0
        change_request = DiscountChangeRequest.objects.create(
            business=business,
            requested_by=request.user,
            old_percent=old_percent,
            new_percent=serializer.validated_data["new_percent"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(DiscountChangeRequestSerializer(change_request).data, status=status.HTTP_201_CREATED)


class DiscountHistoryView(generics.ListAPIView):
    """Chegirma tarixi: Kim keldi, qachon, qancha."""

    serializer_class = DiscountUsageSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["used_at"]

    def get_queryset(self):
        business = get_object_or_404(Business, owner=self.request.user)
        return DiscountUsage.objects.filter(business=business)


class DiscountHistoryExportView(APIView):
    """Filtr & Export: CSV, sana oralig'i."""

    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get(self, request):
        business = get_object_or_404(Business, owner=request.user)
        qs = DiscountUsage.objects.filter(business=business)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(used_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(used_at__date__lte=date_to)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="chegirma_tarixi_{business.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Mijoz", "Kassir", "Foiz", "Xarid summasi", "Chegirma summasi", "Sana"])
        for usage in qs:
            writer.writerow(
                [
                    usage.customer.email if usage.customer else "-",
                    usage.cashier.full_name if usage.cashier else "-",
                    usage.applied_percent,
                    usage.purchase_amount,
                    usage.discount_amount,
                    usage.used_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )
        return response


class DiscountStatisticsView(APIView):
    """Statistika: Hafta/oy grafigi."""

    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get(self, request):
        business = get_object_or_404(Business, owner=request.user)
        period = request.query_params.get("period", "week")
        now = timezone.now()
        since = now - timezone.timedelta(days=7 if period == "week" else 30)

        qs = DiscountUsage.objects.filter(business=business, used_at__gte=since)
        data = {
            "period": period,
            "total_amount": qs.aggregate(s=Sum("discount_amount"))["s"] or 0,
            "total_transactions": qs.count(),
        }
        return Response(DiscountStatSerializer(data).data)


# ==================== KASSIR: chegirma qo'llash ====================


class CashierApplyDiscountView(APIView):
    """Kassir mijozga chegirma qo'llaydi (yangi tranzaksiya yozadi)."""

    permission_classes = [IsAuthenticated, IsCashier]

    def post(self, request):
        cashier = get_object_or_404(Cashier, user=request.user, is_active=True)
        business = cashier.business
        serializer = DiscountUsageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = None
        customer_email = serializer.validated_data.get("customer_email")
        if customer_email:
            customer, _ = User.objects.get_or_create(
                email=customer_email, defaults={"username": customer_email, "role": User.Role.CUSTOMER}
            )

        percent = business.application.discount_percent if business.application else 0
        purchase_amount = serializer.validated_data["purchase_amount"]
        discount_amount = purchase_amount * percent / 100

        usage = DiscountUsage.objects.create(
            business=business,
            customer=customer,
            cashier=cashier,
            applied_percent=percent,
            purchase_amount=purchase_amount,
            discount_amount=discount_amount,
        )
        return Response(DiscountUsageSerializer(usage).data, status=status.HTTP_201_CREATED)


# ==================== ADMIN: Foiz o'zgartirish so'rovlarini boshqarish ====================


class AdminDiscountChangeRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiscountChangeRequest.objects.select_related("business", "requested_by").all()
    serializer_class = DiscountChangeRequestSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]


class AdminDiscountChangeReviewView(APIView):
    """Chegirma foizini o'zgartirish (Admin tomonidan)."""

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        change_request = get_object_or_404(DiscountChangeRequest, pk=pk)
        serializer = DiscountChangeReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_request.reviewed_by = request.user
        change_request.reviewed_at = timezone.now()

        if serializer.validated_data["action"] == "approve":
            change_request.status = DiscountChangeRequest.Status.APPROVED
            business = change_request.business
            if business.application:
                business.application.discount_percent = change_request.new_percent
                business.application.save(update_fields=["discount_percent"])
        else:
            change_request.status = DiscountChangeRequest.Status.REJECTED

        change_request.save()
        return Response(DiscountChangeRequestSerializer(change_request).data)
