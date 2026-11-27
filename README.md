# ربات مسابقه hesam

## نصب روی Termux (اندروید)
1. فایل ZIP را استخراج کنید.
2. وارد پوشه پروژه شوید.
3. `pip install -r requirements.txt`
4. `cp .env.example .env`
5. `nano .env` و توکن BotFather را جایگزین متن نمونه کنید.
6. `python bot.py`

## دستورات
- `/start` ثبت نام
- `/quiz` دریافت سؤال
- `/score` امتیاز
- `/top` ده نفر برتر
- `/winners` فهرست برندگان
- `/reset` شروع دوباره با تأیید

برای ساخت توکن، در تلگرام به BotFather پیام دهید و دستور `/newbot` را اجرا کنید.
