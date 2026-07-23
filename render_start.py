"""
نقطه ورود مخصوص Render.

Render (در پلن رایگان) فقط اجازه‌ی اجرای Web Service می‌ده، یعنی برنامه باید
روی یه پورت HTTP گوش بده. ربات ما با Polling کار می‌کنه و پورتی باز نمی‌کنه.
این فایل یه وب‌سرور خیلی کوچیک (Flask) رو در یه ترد جدا اجرا می‌کنه تا Render
سرویس رو "زنده" تشخیص بده، و ربات اصلی (bot.py) رو با همون Polling همیشگی در
ترد اصلی اجرا می‌کنه.
"""

import os
import threading

from flask import Flask

import bot  # همون bot.py خودتون

app = Flask(__name__)


@app.route("/")
def health_check():
    return "Bot is running.", 200


def run_web_server() -> None:
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # وب‌سرور رو در پس‌زمینه بالا می‌آریم تا Render سرویس رو healthy ببینه
    threading.Thread(target=run_web_server, daemon=True).start()
    # و ربات رو با همون Polling معمولی اجرا می‌کنیم (این خط بلاک‌کننده است)
    bot.main()
