# Chegirma Platformasi — Backend (Django + DRF)

Ushbu loyiha 3 ta flow uchun to'liq backend API taqdim etadi:
1. **Admin panel** (super admin/admin uchun boshqaruv)
2. **Biznes egasi web** (dashboard, kassirlar, chegirmalar)
3. **Ariza qoldirish** (4 qadamli wizard: Biznes → Kontakt → Joylashuv → Chegirma)

## Texnologiyalar
- Python 3.11+, Django 6, Django REST Framework
- JWT autentifikatsiya (SimpleJWT)
- SQLite (standart, production uchun PostgreSQL'ga o'tkazish tavsiya etiladi)

## O'rnatish

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Django admin: `http://127.0.0.1:8000/django-admin/`
API bazaviy manzil: `http://127.0.0.1:8000/api/v1/`

Kunlik statistikani hisoblash (cron orqali har kuni ishga tushiring):
```bash
python manage.py calculate_daily_stats
```

## Apps tuzilmasi

| App | Vazifasi |
|---|---|
| `users` | Custom User (rollar: superadmin, admin, business_owner, cashier, customer), login/register, 2FA maydoni, bloklash, membership, admin foydalanuvchi boshqaruvi |
| `businesses` | Category, Application (4 qadamli ariza wizard), Business (faol listing), Cashier |
| `discounts` | Chegirma foizini o'zgartirish so'rovi, chegirma qo'llash (kassir), chegirma tarixi, statistikalar, CSV export |
| `payments` | To'lovlar, muvaffaqiyatsiz to'lovlar/qayta urinish, refund so'rovlari, oylik daromad, CSV export |
| `notifications` | Foydalanuvchi bildirishnomalari (yangi mijoz/chegirma/eslatma), Admin push (alohida/kategoriya/hammaga, UZ/RU/EN, rejalashtirish) |
| `analytics` | DAU/MAU, konversiya, chegirma hajmi, churn rate, kategoriya bo'yicha faollik (`calculate_daily_stats` command orqali to'ldiriladi) |

## Rollar (User.role) — 4+1 rolli tizim
| Rol | Tavsif | Huquqlari |
|---|---|---|
| `superadmin` | Adminlarni boshqaruvchi/ko'rib turuvchi | Admin akkauntlarini yaratish/ro'yxat/bloklash (`/superadmin/admins/`) + barcha admin huquqlari |
| `admin` | Admin panel operatori | Oddiy foydalanuvchilar, ariza/biznes, to'lov, push, analitika bilan ishlaydi. Boshqa admin/superadminni ko'ra/bloklay olmaydi |
| `business_owner` | Biznesmen | Biznes-web: dashboard, kassirlar, chegirmalar, o'z biznes profili |
| `cashier` | Kassir | Biznes egasi qo'shadigan xodim — chegirma qo'llash |
| `customer` | Oddiy user | Ariza beruvchi, mijoz — ro'yxatdan o'tish, ariza wizard, bildirishnoma, to'lov |

**Muhim:** `admin/users/` endpointi faqat oddiy foydalanuvchilarni (mijoz/biznes egasi/kassir) ko'rsatadi — admin/superadmin akkauntlari u yerda ko'rinmaydi, ular alohida `superadmin/admins/` orqali (faqat superadmin ruxsati bilan) boshqariladi.

---

## API Endpointlar

### Auth / Users (`users` app)
| Method | URL | Tavsif |
|---|---|---|
| POST | `/api/v1/auth/register/` | Ro'yxatdan o'tish |
| POST | `/api/v1/auth/login/` | Kirish (Email+Parol, ixtiyoriy `otp_code`) |
| POST | `/api/v1/auth/token/refresh/` | JWT token yangilash |
| POST | `/api/v1/auth/change-password/` | Parol almashtirish |
| GET/PATCH | `/api/v1/me/` | O'z profili (Profil / Sozlama) |
| GET | `/api/v1/admin/users/` | Oddiy foydalanuvchilar ro'yxati — mijoz/biznes egasi/kassir (admin/superadmin bu yerda ko'rinmaydi) |
| GET | `/api/v1/admin/users/{id}/` | Profilni ko'rish (membership, tarix) |
| POST | `/api/v1/admin/users/{id}/block/` | Bloklash / Blokni ochish (admin/superadmin nishonini faqat superadmin bloklay oladi) |
| POST | `/api/v1/admin/users/{id}/membership/` | Membership uzaytirish/bekor qilish |
| GET/POST | `/api/v1/superadmin/admins/` | **[Faqat SUPERADMIN]** Admin akkauntlari ro'yxati / yangi admin yaratish |
| GET/PATCH/DELETE | `/api/v1/superadmin/admins/{id}/` | **[Faqat SUPERADMIN]** Admin akkaunt tafsiloti/tahrirlash/deaktivatsiya |

### Bizneslar / Ariza (`businesses` app)
| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/v1/categories/` | Kategoriyalar ro'yxati |
| GET | `/api/v1/applications/` | O'z arizalarim |
| POST | `/api/v1/applications/step1/` | **Wizard 1/4** — Biznes ma'lumotlari |
| PATCH | `/api/v1/applications/{id}/step/2/` | **Wizard 2/4** — Kontakt |
| PATCH | `/api/v1/applications/{id}/step/3/` | **Wizard 3/4** — Joylashuv |
| PATCH | `/api/v1/applications/{id}/step/4/` | **Wizard 4/4** — Chegirma (yuborish, status→pending) |
| GET | `/api/v1/applications/{id}/` | Ariza tafsilotlari |
| GET | `/api/v1/admin/applications/` | Arizalar ro'yxati (filter: `status`,`category`) |
| POST | `/api/v1/admin/applications/{id}/review/` | Tasdiqlash/Rad etish (`action: approve|reject`) |
| GET | `/api/v1/admin/businesses/` | Faol bizneslar ro'yxati |
| POST | `/api/v1/admin/businesses/{id}/stop-partnership/` | Hamkorlikni to'xtatish |
| GET | `/api/v1/admin/businesses/{id}/stats/` | Biznes statistikasi |
| GET/PATCH | `/api/v1/my-business/` | Biznes egasi profili |
| GET | `/api/v1/my-business/dashboard/` | Dashboard (bugungi stat, daromad, mijozlar) |
| GET/POST | `/api/v1/my-business/cashiers/` | Kassirlar ro'yxati / qo'shish |
| GET/PATCH/DELETE | `/api/v1/my-business/cashiers/{id}/` | Kassir tafsiloti |

### Chegirmalar (`discounts` app)
| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/v1/my-business/discount/` | Joriy foiz + kutilayotgan so'rov |
| POST | `/api/v1/my-business/discount/change-request/` | Foiz o'zgartirish so'rovi |
| GET | `/api/v1/my-business/discount/history/` | Chegirma tarixi |
| GET | `/api/v1/my-business/discount/history/export/` | CSV export (`date_from`,`date_to`) |
| GET | `/api/v1/my-business/discount/statistics/` | Hafta/oy grafigi (`period=week|month`) |
| POST | `/api/v1/cashier/apply-discount/` | Kassir: chegirma qo'llash |
| GET | `/api/v1/admin/discount-requests/` | So'rovlar ro'yxati |
| POST | `/api/v1/admin/discount-requests/{id}/review/` | Tasdiqlash/Rad etish |

### To'lovlar (`payments` app)
| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/v1/payments/` | O'z to'lovlarim |
| POST | `/api/v1/payments/{id}/retry/` | Qayta urinish |
| POST | `/api/v1/payments/{id}/refund/` | Refund so'rash |
| GET | `/api/v1/admin/payments/` | To'lov tarixi (filter: `status`,`provider`) |
| GET | `/api/v1/admin/payments/failed/` | Muvaffaqiyatsiz to'lovlar |
| GET | `/api/v1/admin/payments/monthly-revenue/` | Oylik daromad |
| GET | `/api/v1/admin/payments/export/` | CSV export |
| GET | `/api/v1/admin/refunds/` | Refund so'rovlari |
| POST | `/api/v1/admin/refunds/{id}/review/` | Refund tasdiqlash |

### Bildirishnomalar (`notifications` app)
| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/v1/notifications/` | Mening bildirishnomalarim |
| POST | `/api/v1/notifications/{id}/read/` | O'qilgan deb belgilash |
| POST | `/api/v1/notifications/read-all/` | Barchasini o'qilgan qilish |
| GET/POST | `/api/v1/admin/push-notifications/` | Push xabar ro'yxati / yaratish |
| POST | `/api/v1/admin/push-notifications/{id}/send/` | Darhol yuborish |

### Analitika (`analytics` app)
| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/v1/admin/dashboard/` | Admin Dashboard (DAU/MAU, konversiya, bizneslar, foydalanuvchilar) |
| GET | `/api/v1/admin/analytics/daily-stats/` | Kunlik statistikalar tarixi |
| GET | `/api/v1/admin/analytics/category-activity/` | Kategoriya bo'yicha faollik |
| GET | `/api/v1/admin/analytics/churn-rate/` | Churn rate |
| GET | `/api/v1/admin/analytics/conversion/` | Konversiya (yuklab oldi→to'ladi) |
| GET | `/api/v1/admin/analytics/discount-volume/` | Chegirma hajmi |

---

## Muhim eslatmalar
- **2FA**: `User.is_2fa_enabled` va `two_fa_secret` maydonlari tayyor; haqiqiy OTP generatsiya/tekshirish uchun `pyotp` yoki SMS-provayder integratsiyasi qo'shilishi kerak (`users/serializers.py::LoginSerializer`).
- **To'lov provayderlari** (Click/Payme/Uzum): `Payment` modelida provider maydoni bor, lekin haqiqiy tashqi API chaqiruvi ulanmagan — `payments/views.py::PaymentRetryView` ichida qo'shiladigan joy ko'rsatilgan (`NOTE` izohi).
- Barcha ro'yxat (list) endpointlarida DRF pagination, filter va search ishlaydi (`?search=`, `?ordering=`, va model-ga xos filterlar).
- Media fayllar (logo, avatar, QR kod) `MEDIA_URL=/media/` orqali xizmat qiladi (faqat DEBUG rejimida).
- Loyiha to'liq test qilindi: ro'yxatdan o'tish → login → 4 qadamli ariza → admin tasdiqlash → biznes yaratilishi → kassir qo'shish → chegirma qo'llash → tarix → push bildirishnoma yetkazish.
