from rest_framework import serializers

from discounts.models import DiscountChangeRequest, DiscountUsage


class DiscountChangeRequestCreateSerializer(serializers.Serializer):
    """Foiz o'zgartirish so'rovi (Biznes egasi -> Admin)."""

    new_percent = serializers.IntegerField(min_value=1, max_value=100)
    reason = serializers.CharField(required=False, allow_blank=True)


class DiscountChangeRequestSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = DiscountChangeRequest
        fields = [
            "id", "business", "business_name", "requested_by", "old_percent", "new_percent",
            "reason", "status", "reviewed_by", "reviewed_at", "created_at",
        ]
        read_only_fields = fields


class DiscountChangeReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])


class DiscountUsageSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    cashier_name = serializers.CharField(source="cashier.full_name", read_only=True)

    class Meta:
        model = DiscountUsage
        fields = [
            "id", "business", "customer", "customer_email", "cashier", "cashier_name",
            "applied_percent", "purchase_amount", "discount_amount", "used_at",
        ]
        read_only_fields = ["id", "used_at"]


class DiscountUsageCreateSerializer(serializers.Serializer):
    """Kassir tomonidan chegirma qo'llash (mijoz keldi -> chegirma berildi)."""

    customer_email = serializers.EmailField(required=False, allow_blank=True)
    purchase_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class DiscountStatSerializer(serializers.Serializer):
    """Statistika: Hafta/oy grafigi."""

    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_transactions = serializers.IntegerField()
