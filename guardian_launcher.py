#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لانچر ابری و ۱۰۰٪ امن نگهبان پرتفوی برای ریپازیتوری پابلیک GitHub Actions (guardian_launcher.py)
"""

import json
import os
import sys
import urllib.parse
import urllib.request

TARGET_SCRIPT_NAME = "portfolio_shield1_sim.py"


def get_gdrive_access_token():
    client_id = os.environ.get("GDRIVE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN", "").strip()
    folder_id = os.environ.get("GDRIVE_FOLDER_ID", "").strip()

    if not (client_id and client_secret and refresh_token and folder_id):
        print(
            "[!] خطا: متغیرهای محیطی گوگل درایو (GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID) "
            "در GitHub Secrets یا محیط اجرا تنظیم نشده‌اند!"
        )
        return None, folder_id

    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("access_token"), folder_id
    except Exception as e:
        print(f"[!] خطا در دریافت Access Token از گوگل درایو: {e}")
    return None, folder_id


def gdrive_find_latest_file_id(access_token, folder_id, filename):
    q = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    params = urllib.parse.urlencode(
        {
            "q": q,
            "fields": "files(id, name, modifiedTime, size)",
            "orderBy": "modifiedTime desc",
            "pageSize": 5,
        }
    )
    url = f"https://www.googleapis.com/drive/v3/files?{params}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {access_token}"}, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            if resp.status == 200:
                files = json.loads(resp.read().decode("utf-8")).get("files") or []
                if files:
                    return files[0].get("id"), files[0].get("modifiedTime", "")
    except Exception as e:
        print(f"[!] خطا در جستجوی فایل {filename} در گوگل درایو: {e}")
    return None, ""


def gdrive_download_file(access_token, file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {access_token}"}, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            if resp.status == 200:
                return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[!] خطا در دانلود فایل از گوگل درایو: {e}")
    return None


def main():
    print("=" * 80)
    print("  لانچر ابری نگهبان پرتفوی مفید (بارگذاری مستقیم از Google Drive در RAM)")
    print("=" * 80)

    access_token, folder_id = get_gdrive_access_token()
    if not access_token:
        sys.exit(1)

    fid, mod_time = gdrive_find_latest_file_id(
        access_token, folder_id, TARGET_SCRIPT_NAME
    )
    if not fid:
        print(
            f"[!] خطا: فایل «{TARGET_SCRIPT_NAME}» در پوشه گوگل درایو ({folder_id}) یافت نشد!"
        )
        sys.exit(1)

    print(
        f"[+] آخرین نسخه «{TARGET_SCRIPT_NAME}» در گوگل درایو یافت شد (آخرین ویرایش: {mod_time}). در حال بارگذاری در حافظه رم..."
    )
    remote_code = gdrive_download_file(access_token, fid)
    if not remote_code or len(remote_code) < 1000:
        print(f"[!] خطا: محتوای دانلودشده «{TARGET_SCRIPT_NAME}» ناقص یا خالی است!")
        sys.exit(1)

    print(
        f"[+] کد نگهبان پرتفوی ({len(remote_code):,} بایت) با موفقیت در RAM بارگذاری شد. شروع اجرا...\n"
        + "=" * 80
    )
    exec_globals = {
        "__name__": "__main__",
        "__file__": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), TARGET_SCRIPT_NAME
        ),
        "__builtins__": __builtins__,
    }
    exec(
        compile(remote_code, f"<gdrive_cloud:{TARGET_SCRIPT_NAME}>", "exec"),
        exec_globals,
    )


if __name__ == "__main__":
    main()
