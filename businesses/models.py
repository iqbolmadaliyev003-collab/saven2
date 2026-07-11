import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    """Biznes turi/kategoriyasi (Tanlang / YaTT / MCHJ kabi biznes turi ham shu yerda bo'lishi mumkin)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BusinessType(models.TextChoices):
    YATT = "yatt", "YaTT"
    MCHJ = "mchj", "MCHJ"


class WorkDay(models.TextChoices):
    MON_FRI = "mon_fri", "Dushanba - Juma"
    MON_SAT = "mon_sat", "Dushanba - Shanba"
    EVERYDAY = "everyday", "Har kuni"


class Application(models.Model):
    """
    Ariza qoldirish - 4 qadamli wizard:
    1) Biznes  2) Kontakt  3) Joylashuv  4) Chegirma
    Admin panel: Arizalar ro'yxati -> Yangi ariza ko'rish -> Tasdiqlash / Rad etish
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        PENDING = "pending", "Ko'rib chiqilmoqda"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    class DiscountType(models.TextChoices):
        FIXED = "fixed", "Barcha mahsulotlar"
        MIN_PURCHASE = "min_purchase", "Minimal xarid summasi"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )

    # --- Step 1: Biznes ---
    business_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="applications")
    business_type = models.CharField(max_length=10, choices=BusinessType.choices)
    responsible_full_name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)

    # --- Step 2: Kontakt ---
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    instagram = models.CharField(max_length=150, blank=True)
    telegram = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)

    # --- Step 3: Joylashuv ---
    region = models.CharField(max_length=120)
    city_district = models.CharField(max_length=120)
    full_address = models.CharField(max_length=500)
    work_days = models.CharField(max_length=20, choices=WorkDay.choices, default=WorkDay.EVERYDAY)
    work_hours_from = models.TimeField(blank=True, null=True)
    work_hours_to = models.TimeField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    # --- Step 4: Chegirma ---
    discount_percent = models.PositiveSmallIntegerField(default=10)
    min_purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.FIXED)

    # --- Wizard progress / status ---
    current_step = models.PositiveSmallIntegerField(default=1)  # 1..4
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_applications",
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business_name} - {self.status}"


class Business(models.Model):
    """Tasdiqlangan arizadan yaratiladigan faol biznes (listing)."""

    class PartnershipStatus(models.TextChoices):
        ACTIVE = "active", "Faol hamkorlik"
        PAUSED = "paused", "To'xtatilgan"
        STOPPED = "stopped", "Bekor qilingan"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_businesses"
    )
    application = models.OneToOneField(
        Application, on_delete=models.SET_NULL, blank=True, null=True, related_name="business"
    )

    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="businesses")
    business_type = models.CharField(max_length=10, choices=BusinessType.choices)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)

    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    instagram = models.CharField(max_length=150, blank=True)
    telegram = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)

    region = models.CharField(max_length=120)
    city_district = models.CharField(max_length=120)
    full_address = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    partnership_status = models.CharField(
        max_length=20, choices=PartnershipStatus.choices, default=PartnershipStatus.ACTIVE
    )
    contract_signed = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Cashier(models.Model):
    """Biznes egasi qo'shgan kassirlar ro'yxati."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="cashiers")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cashier_profile"
    )
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} @ {self.business.name}"
