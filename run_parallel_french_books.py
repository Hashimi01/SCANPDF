#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتشغيل عدة نسخ متوازية من reprocess_french_books.py
يستخدم screen للحفاظ على العملية حتى لو انقطع الاتصال
يقسم الكتب الفرنسية على عدة سكربتات متوازية
"""

import subprocess
import sys
import time
import os
import json
from typing import List, Tuple

# إعدادات
INPUT_FILE = "french_books_incorrectly_processed.json"
SCRIPT_NAME = "reprocess_french_books.py"
NUM_SCRIPTS = 10  # عدد السكربتات المتوازية (يمكن تعديله)

def check_screen_installed() -> bool:
    """التحقق من تثبيت screen"""
    try:
        subprocess.run(['which', 'screen'], check=True, capture_output=True)
        return True
    except:
        return False

def install_screen():
    """تثبيت screen"""
    print("📦 جاري تثبيت screen...")
    try:
        subprocess.run(['apt', 'update'], check=True, capture_output=True)
        subprocess.run(['apt', 'install', '-y', 'screen'], check=True, capture_output=True)
        print("✅ تم تثبيت screen بنجاح")
        return True
    except Exception as e:
        print(f"❌ فشل تثبيت screen: {e}")
        return False

def get_books_count(books_file: str) -> int:
    """قراءة عدد الكتب من الملف JSON"""
    try:
        with open(books_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        books = data.get("books", [])
        return len(books)
    except Exception as e:
        print(f"⚠️  خطأ في قراءة الملف: {e}")
        return 0

def calculate_ranges(start: int, end: int, num_scripts: int) -> List[Tuple[int, int]]:
    """
    تقسيم النطاق إلى مجموعات متساوية
    
    Args:
        start: رقم الكتاب الأول (1-indexed)
        end: رقم الكتاب الأخير (1-indexed)
        num_scripts: عدد السكربتات
        
    Returns:
        قائمة من tuples (start, end) لكل سكربت (1-indexed)
    """
    total_books = end - start + 1
    books_per_script = total_books // num_scripts
    remainder = total_books % num_scripts
    
    ranges = []
    current_start = start
    
    for i in range(num_scripts):
        # توزيع الباقي على السكربتات الأولى
        current_end = current_start + books_per_script - 1
        if i < remainder:
            current_end += 1
        
        # التأكد من عدم تجاوز النهاية
        if current_end > end:
            current_end = end
        
        if current_start <= end:
            ranges.append((current_start, current_end))
            current_start = current_end + 1
    
    return ranges

def create_screen_session(session_name: str, start: int, end: int, script_num: int, total: int):
    """
    إنشاء جلسة screen جديدة وتشغيل السكربت فيها
    
    Args:
        session_name: اسم الجلسة
        start: رقم الكتاب الأول (1-indexed)
        end: رقم الكتاب الأخير (1-indexed)
        script_num: رقم السكربت
        total: العدد الإجمالي للسكربتات
    """
    # إنشاء script مؤقت لتشغيل السكربت
    script_content = f"""#!/bin/bash
cd /root/i2pdf
source venv/bin/activate
echo "🇫🇷 السكربت {script_num}/{total}: إعادة فحص الكتب الفرنسية من {start} إلى {end}"
echo "📅 بدء العملية: $(date)"
python {SCRIPT_NAME} {start} {end}
echo "✅ اكتمل السكربت {script_num}/{total}"
echo "📅 انتهاء العملية: $(date)"
"""
    
    # حفظ السكربت المؤقت
    temp_script = f"/tmp/run_french_script_{script_num}.sh"
    with open(temp_script, 'w') as f:
        f.write(script_content)
    
    # جعل السكربت قابل للتنفيذ
    os.chmod(temp_script, 0o755)
    
    # إنشاء جلسة screen جديدة وتشغيل السكربت
    screen_cmd = [
        'screen',
        '-dmS', session_name,  # -d: detached, -m: create new, -S: session name
        'bash', temp_script
    ]
    
    try:
        subprocess.run(screen_cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"❌ فشل إنشاء جلسة screen {session_name}: {e}")
        return False

def list_screen_sessions():
    """عرض قائمة جلسات screen النشطة"""
    try:
        result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
        return result.stdout
    except:
        return ""

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🇫🇷 سكريبت تشغيل متوازي لإعادة فحص الكتب الفرنسية")
    print("=" * 70)
    
    # التحقق من تثبيت screen
    if not check_screen_installed():
        print("⚠️  screen غير مثبت")
        if not install_screen():
            print("❌ لا يمكن المتابعة بدون screen")
            sys.exit(1)
    
    # التحقق من وجود الملفات
    if not os.path.exists(SCRIPT_NAME):
        print(f"❌ السكربت غير موجود: {SCRIPT_NAME}")
        sys.exit(1)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ملف الكتب الفرنسية غير موجود: {INPUT_FILE}")
        print(f"💡 قم بتشغيل check_french_books_status.py أولاً")
        sys.exit(1)
    
    # قراءة عدد الكتب الفعلي
    total_books = get_books_count(INPUT_FILE)
    if total_books == 0:
        print(f"❌ لم يتم العثور على كتب في الملف")
        sys.exit(1)
    
    print(f"📚 عدد الكتب الفرنسية في الملف: {total_books}")
    
    # حساب النطاقات
    START_BOOK = 1
    END_BOOK = total_books
    print(f"\n📊 تقسيم {total_books} كتاب (من {START_BOOK} إلى {END_BOOK}) على {NUM_SCRIPTS} سكربت...")
    ranges = calculate_ranges(START_BOOK, END_BOOK, NUM_SCRIPTS)
    
    print(f"\n📋 النطاقات:")
    for i, (start, end) in enumerate(ranges, 1):
        count = end - start + 1
        print(f"   السكربت {i:2d}: من {start:4d} إلى {end:4d} ({count:3d} كتاب) - جلسة: french_script_{i}")
    
    # تأكيد البدء
    print(f"\n{'='*70}")
    print(f"ℹ️  سيتم إنشاء {NUM_SCRIPTS} جلسة screen منفصلة")
    print(f"ℹ️  سيتم إعادة فحص الكتب الفرنسية باللغة الفرنسية")
    print(f"ℹ️  يمكنك فحص التقدم باستخدام: screen -ls")
    print(f"ℹ️  للدخول إلى جلسة: screen -r french_script_X")
    print(f"ℹ️  للخروج من جلسة: Ctrl+A ثم D")
    print(f"{'='*70}")
    confirm = input(f"\nهل تريد البدء بتشغيل {NUM_SCRIPTS} سكربت متوازي؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        sys.exit(0)
    
    # إنشاء جميع جلسات screen
    print(f"\n🚀 بدء إنشاء {NUM_SCRIPTS} جلسة screen...\n")
    created_sessions = []
    
    for i, (start, end) in enumerate(ranges, 1):
        session_name = f"french_script_{i}"
        print(f"📺 إنشاء جلسة {i}/{NUM_SCRIPTS}: {session_name} (الكتب {start}-{end})")
        
        if create_screen_session(session_name, start, end, i, NUM_SCRIPTS):
            created_sessions.append(session_name)
            time.sleep(0.3)  # تأخير قصير بين كل جلسة
        else:
            print(f"⚠️  فشل إنشاء جلسة {session_name}")
    
    print(f"\n{'='*70}")
    print(f"✅ تم إنشاء {len(created_sessions)}/{NUM_SCRIPTS} جلسة screen")
    print(f"{'='*70}")
    
    # عرض الجلسات النشطة
    print("\n📺 الجلسات النشطة:")
    sessions_list = list_screen_sessions()
    print(sessions_list)
    
    print(f"\n{'='*70}")
    print("📝 أوامر مفيدة:")
    print(f"{'='*70}")
    print("  عرض جميع الجلسات:     screen -ls")
    print("  الدخول إلى جلسة:       screen -r french_script_X")
    print("  الخروج من جلسة:        Ctrl+A ثم D")
    print("  إنهاء جلسة:             screen -X -S french_script_X quit")
    print("  إنهاء جميع الجلسات:     for s in $(screen -ls | grep -o '[0-9]*\\.french_script_[^[:space:]]*' | grep -v '^[0-9]*\\.$'); do screen -S \"$s\" -X quit; done")
    print(f"\n{'='*70}")
    print("✅ تم بدء جميع السكربتات في جلسات screen منفصلة!")
    print("💡 يمكنك إغلاق Terminal - السكربتات ستستمر في العمل")
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
        print("💡 الجلسات النشطة ستستمر في العمل")
        print("💡 لإنهاء جميع الجلسات: screen -X quit")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

