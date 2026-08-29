# VEXORA 1.0.0 Commercial Build

این نسخه باید به‌عنوان یک پایه‌ی تجاری واقعی در نظر گرفته شود، نه یک
نمونه‌ی صرفاً نمایشی. ساختار نصب، اجرای سرویس، دیتابیس، احراز هویت،
فروشگاه، مدیریت پلن، سفارش، کاربر، سرور، پشتیبانی، گزارش، تنظیمات و
Audit در معماری پروژه جدا شده‌اند.

## مسیرهای اصلی

`/` → `/shop/`

`/shop/` → صفحه عمومی فروشگاه

`/shop/plans/` → لیست پلن‌ها

`/shop/support/` → ثبت درخواست پشتیبانی

`/admin/login` → تنها ورودی بخش مدیریت

`/admin/` → داشبورد

`/admin/orders/` → سفارش‌ها

`/admin/users/` → کاربران

`/admin/plans/` → پلن‌ها

`/admin/servers/` → سرورها

`/admin/support/` → تیکت‌ها

`/admin/reports/` → گزارش‌ها

`/admin/settings/` → تنظیمات

`/admin/admins/` → مدیران

`/admin/audit/` → Audit Log

## اصول نصب

Installer به فایل `.env.example` وابسته نیست. فایل `/etc/vexora/.env` را
خودش می‌سازد، Secret و Password را تولید می‌کند و دسترسی فایل را محدود
می‌کند.

Backend با Uvicorn روی `0.0.0.0:6000` اجرا می‌شود. این انتخاب عمداً با
الگوی سرویس‌هایی که کاربر خواسته هماهنگ است.

Nginx لایه‌ی عمومی TLS است. پورت 443 ثابت است و Installer یک پورت HTTPS
آزاد دوم را از مجموعه‌ی مشخص انتخاب می‌کند. پورت 8080 متعلق به VEXORA
نیست.

Certificate شرط موفقیت نصب است. اگر Certbot نتواند گواهی واقعی بگیرد،
Installer نباید پیام Installation completed successfully بدهد.

## Certificate modes

### Domain

برای دامنه، Certbot با standalone HTTP-01 اجرا می‌شود. در این مرحله Nginx
موقتاً متوقف می‌شود تا پورت 80 برای ACME آزاد باشد.

### Public IP

برای IP عمومی، Installer ابتدا نسخه‌ی Certbot را بررسی می‌کند. اگر نسخه‌ی
نصب‌شده قابلیت IP certificate را نداشته باشد، نصب متوقف می‌شود و Certificate
جعلی ساخته نمی‌شود.

## Database

SQLite با WAL برای نصب اولیه انتخاب شده تا سرویس به PostgreSQL خارجی وابسته
نباشد. جدول‌ها شامل admin، user، plan، order، server، ticket، ticket
message، settings، audit و session هستند.

ساختار database عمداً از UI جدا است تا در آینده بتوان backend دیتابیس را
بدون بازنویسی ظاهر تغییر داد.

## Recovery

`/opt/vexora/scripts/backup.sh` تنظیمات و داده‌های سرویس را archive می‌کند و
SHA-256 کنار archive قرار می‌دهد.

`restore.sh` قبل از استخراج، checksum را بررسی می‌کند و بعد سرویس را restart
می‌کند.

`update.sh` سورس جدید را با virtualenv فعلی جایگزین می‌کند و سرویس را پس از
بررسی دوباره بالا می‌آورد.

`uninstall.sh` برای حذف کامل confirmation متنی می‌خواهد.

## UI reference

پوشه‌ی `docs/preview/` تصاویر مرجع طراحی مورد استفاده برای جهت بصری نسخه‌ی
تجاری را نگه می‌دارد. این فایل‌ها بخشی از runtime نیستند.
