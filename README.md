# 🤖 MyTranslator — Telegram Translator Bot

ربات تلگرام دستیار مترجم با هوش مصنوعی رایگان **Google Gemini**.
هر متنی بفرستید، ترجمه‌اش را تحویل می‌گیرید.

- فارسی ← انگلیسی
- هر زبان دیگر ← فارسی
- `/to French` برای ترجمه همیشگی به یک زبان دلخواه، `/auto` برای برگشت به حالت خودکار

## راه‌اندازی

### ۱. ساخت ربات در تلگرام
1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام بدهید و `/newbot` را بفرستید.
2. یک اسم و یک username (که به `bot` ختم شود) انتخاب کنید.
3. **توکن** را کپی کنید.

### ۲. گرفتن کلید رایگان Gemini
1. به [Google AI Studio](https://aistudio.google.com/apikey) بروید و با اکانت گوگل وارد شوید.
2. روی **Create API key** بزنید و کلید را کپی کنید.

> اگر از ایران استفاده می‌کنید، Gemini ممکن است بدون VPN یا سرور خارج کار نکند.

### ۳. نصب و اجرا
```bash
git clone https://github.com/amiralialamdari/MyTranslator.git
cd MyTranslator
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # Linux/Mac: cp .env.example .env
```
فایل `.env` را باز کنید و توکن تلگرام و کلید Gemini را بگذارید. بعد:
```bash
python bot.py
```

### ۴. (اختیاری) شخصی‌کردن ربات
به ربات `/myid` بفرستید، عدد را در `ALLOWED_USER_ID` داخل `.env` بگذارید و ربات را دوباره اجرا کنید. حالا فقط شما می‌توانید از آن استفاده کنید.

## ⚠️ امنیت
فایل `.env` هرگز نباید در گیت‌هاب آپلود شود (در `.gitignore` قرار دارد).
