from rest_framework import serializers

from businesses.models import Application, Business, Cashier, Category
from users.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "is_active"]


# ---------------- ARIZA (Wizard 4 qadam) ----------------


class ApplicationStep1Serializer(serializers.ModelSerializer):
    """Step 1 — Biznes."""

    class Meta:
        model = Application
        fields = [
            "id", "business_name", "category", "business_type",
            "responsible_full_name", "short_description",
        ]

    def create(self, validated_data):
        validated_data["applicant"] = self.context["request"].user
        validated_data["current_step"] = 2
        return super().create(validated_data)


class ApplicationStep2Serializer(serializers.ModelSerializer):
    """Step 2 — Kontakt."""

    class Meta:
        model = Application
        fields = ["phone_number", "email", "instagram", "telegram", "website"]

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.current_step = max(instance.current_step, 3)
        instance.save(update_fields=["current_step"])
        return instance


class ApplicationStep3Serializer(serializers.ModelSerializer):
    """Step 3 — Joylashuv."""

    class Meta:
        model = Application
        fields = [
            "region", "city_district", "full_address",
            "work_days", "work_hours_from", "work_hours_to",
            "latitude", "longitude",
        ]

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.current_step = max(instance.current_step, 4)
        instance.save(update_fields=["current_step"])
        return instance


class ApplicationStep4Serializer(serializers.ModelSerializer):
    """Step 4 — Chegirma. Yakuniy qadam -> status PENDING ga o'tadi (Ariza yuborish)."""

    class Meta:
        model = Application
        fields = ["discount_percent", "min_purchase_amount", "discount_type"]

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.status = Application.Status.PENDING
        instance.save(update_fields=["status"])
        return instance


class ApplicationSerializer(serializers.ModelSerializer):
    """To'liq ariza ma'lumoti (o'qish uchun)."""

    category = CategorySerializer(read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = [
            "id", "applicant", "status", "reviewed_by", "reviewed_at",
            "created_at", "updated_at", "current_step",
        ]


class ApplicationReviewSerializer(serializers.Serializer):
    """Admin: Tasdiqlash (listing faollashadi) / Rad etish (sabab yoziladi)."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


# ---------------- BIZNES (faol listing) ----------------


class CashierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cashier
        fields = ["id", "business", "user", "full_name", "is_active", "added_at"]
        read_only_fields = ["id", "added_at", "business"]


class CashierCreateSerializer(serializers.Serializer):
    """Kassir qo'shish: Email, parol berish."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value


class BusinessSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True, required=False
    )
    cashiers_count = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id", "owner", "application", "name", "category", "category_id",
            "business_type", "description", "logo",
            "phone_number", "email", "instagram", "telegram", "website",
            "region", "city_district", "full_address", "latitude", "longitude",
            "partnership_status", "contract_signed", "qr_code",
            "is_active", "cashiers_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "application", "created_at", "updated_at"]

    def get_cashiers_count(self, obj):
        return obj.cashiers.filter(is_active=True).count()


class BusinessDashboardSerializer(serializers.Serializer):
    """Dashboard (Bosh sahifa): Bugungi stat, daromad, mijozlar."""

    today_customers = serializers.IntegerField()
    today_discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_customers = serializers.IntegerField()
    active_discount_percent = serializers.IntegerField()


class PartnershipStatusUpdateSerializer(serializers.Serializer):
    """Hamkorlikni to'xtatish."""

    partnership_status = serializers.ChoiceField(choices=Business.PartnershipStatus.choices)
