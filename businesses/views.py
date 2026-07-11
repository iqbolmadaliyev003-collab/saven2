from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from businesses.models import Application, Business, Cashier, Category
from businesses.serializers import (
    ApplicationReviewSerializer,
    ApplicationSerializer,
    ApplicationStep1Serializer,
    ApplicationStep2Serializer,
    ApplicationStep3Serializer,
    ApplicationStep4Serializer,
    BusinessDashboardSerializer,
    BusinessSerializer,
    CashierCreateSerializer,
    CashierSerializer,
    CategorySerializer,
    PartnershipStatusUpdateSerializer,
)
from discounts.models import DiscountUsage
from users.models import User
from users.permissions import IsAdminRole, IsBusinessOwner


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


# ==================== ARIZA QOLDIRISH (Wizard) ====================


class MyApplicationsView(generics.ListAPIView):
    """Foydalanuvchining o'z arizalari ro'yxati."""

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)


class ApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Application.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.Role.ADMIN, User.Role.SUPERADMIN):
            return Application.objects.all()
        return Application.objects.filter(applicant=user)


class ApplicationWizardStep1View(generics.CreateAPIView):
    """1/4 qadam — Biznes. Yangi ariza yaratadi (draft)."""

    serializer_class = ApplicationStep1Serializer
    permission_classes = [IsAuthenticated]


class ApplicationWizardStepUpdateView(APIView):
    """2/4, 3/4, 4/4 qadamlarni to'ldirish uchun umumiy view."""

    permission_classes = [IsAuthenticated]

    step_serializers = {
        2: ApplicationStep2Serializer,
        3: ApplicationStep3Serializer,
        4: ApplicationStep4Serializer,
    }

    def patch(self, request, pk, step):
        step = int(step)
        serializer_class = self.step_serializers.get(step)
        if not serializer_class:
            return Response({"detail": "Noto'g'ri qadam."}, status=400)

        application = get_object_or_404(Application, pk=pk, applicant=request.user)
        serializer = serializer_class(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ApplicationSerializer(application).data)


# ==================== ADMIN PANEL: Biznes boshqaruvi ====================


class AdminApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """Arizalar ro'yxati -> Yangi ariza ko'rish."""

    queryset = Application.objects.select_related("category", "applicant").all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category", "business_type"]
    search_fields = ["business_name", "applicant__email", "phone_number"]
    ordering_fields = ["created_at"]


class AdminApplicationReviewView(APIView):
    """
    Tasdiqlash (listing faollashadi) / Rad etish (sabab yoziladi)
    """

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        serializer = ApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()

        if action == "approve":
            application.status = Application.Status.APPROVED
            application.save()

            business, created = Business.objects.get_or_create(
                application=application,
                defaults=dict(
                    owner=application.applicant,
                    name=application.business_name,
                    category=application.category,
                    business_type=application.business_type,
                    description=application.short_description,
                    phone_number=application.phone_number,
                    email=application.email,
                    instagram=application.instagram,
                    telegram=application.telegram,
                    website=application.website,
                    region=application.region,
                    city_district=application.city_district,
                    full_address=application.full_address,
                    latitude=application.latitude,
                    longitude=application.longitude,
                    is_active=True,
                ),
            )
            owner = application.applicant
            if owner.role != User.Role.BUSINESS_OWNER:
                owner.role = User.Role.BUSINESS_OWNER
                owner.save(update_fields=["role"])

            return Response(BusinessSerializer(business).data)

        else:
            application.status = Application.Status.REJECTED
            application.rejection_reason = serializer.validated_data.get("rejection_reason", "")
            application.save()
            return Response(ApplicationSerializer(application).data)


class AdminBusinessViewSet(viewsets.ReadOnlyModelViewSet):
    """Faol Bizneslar ro'yxati -> Biznes profili ko'rish."""

    queryset = Business.objects.select_related("category", "owner").all()
    serializer_class = BusinessSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["partnership_status", "category", "is_active"]
    search_fields = ["name", "owner__email", "phone_number"]


class AdminBusinessStopPartnershipView(APIView):
    """Hamkorlikni to'xtatish."""

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        serializer = PartnershipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business.partnership_status = serializer.validated_data["partnership_status"]
        if business.partnership_status == Business.PartnershipStatus.STOPPED:
            business.is_active = False
        business.save()
        return Response(BusinessSerializer(business).data)


class AdminBusinessStatsView(APIView):
    """Statistikasini ko'rish (Admin tomonidan)."""

    permission_classes = [IsAdminRole]

    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        usages = DiscountUsage.objects.filter(business=business)
        data = {
            "total_customers": usages.values("customer").distinct().count(),
            "total_discount_amount": usages.aggregate(s=Sum("discount_amount"))["s"] or 0,
            "total_transactions": usages.count(),
        }
        return Response(data)


# ==================== BIZNES EGASI: Dashboard, Profil, Kassirlar ====================


class MyBusinessView(generics.RetrieveUpdateAPIView):
    """Biznes egasi o'z biznes profilini ko'rish/tahrirlash (Profil / Sozlama)."""

    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get_object(self):
        return get_object_or_404(Business, owner=self.request.user)


class MyBusinessDashboardView(APIView):
    """Dashboard (Bosh sahifa): Bugungi stat, daromad, mijozlar."""

    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get(self, request):
        business = get_object_or_404(Business, owner=request.user)
        today = timezone.localdate()
        today_usages = DiscountUsage.objects.filter(business=business, used_at__date=today)

        data = {
            "today_customers": today_usages.values("customer").distinct().count(),
            "today_discount_amount": today_usages.aggregate(s=Sum("discount_amount"))["s"] or 0,
            "today_revenue": today_usages.aggregate(s=Sum("purchase_amount"))["s"] or 0,
            "total_customers": DiscountUsage.objects.filter(business=business).values("customer").distinct().count(),
            "active_discount_percent": business.application.discount_percent if business.application else 0,
        }
        serializer = BusinessDashboardSerializer(data)
        return Response(serializer.data)


class MyCashierListCreateView(generics.ListCreateAPIView):
    """Kassirlar: Ro'yxat ko'rish / Kassir qo'shish (Email, parol berish)."""

    serializer_class = CashierSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get_queryset(self):
        business = get_object_or_404(Business, owner=self.request.user)
        return Cashier.objects.filter(business=business)

    def create(self, request, *args, **kwargs):
        business = get_object_or_404(Business, owner=request.user)
        serializer = CashierCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cashier_user = User.objects.create_user(
            username=serializer.validated_data["email"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            role=User.Role.CASHIER,
        )
        cashier = Cashier.objects.create(
            business=business,
            user=cashier_user,
            full_name=serializer.validated_data["full_name"],
        )
        return Response(CashierSerializer(cashier).data, status=status.HTTP_201_CREATED)


class MyCashierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CashierSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get_queryset(self):
        business = get_object_or_404(Business, owner=self.request.user)
        return Cashier.objects.filter(business=business)
