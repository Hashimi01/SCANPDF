#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتشغيل عدة نسخ متوازية من inspect_books_mongodb.py
يقسم الكتب إلى مجموعات ويشغل كل مجموعة في عملية منفصلة
"""

import subprocess
import sys
import time
import os
import json
from typing import List, Tuple
from multiprocessing import Process
import signal

# إعدادات
BOOKS_FILE = "books-2025-11-09T23-13-42-652Z.json"
SCRIPT_NAME = "inspect_books_mongodb.py"
START_BOOK = 100  # من الكتاب رقم 100
END_BOOK = 2116   # إلى الكتاب رقم 2116
NUM_SCRIPTS = 50  # عدد السكربتات المتوازية (يمكن تعديله)

def calculate_ranges(start: int, end: int, num_scripts: int) -> List[Tuple[int, int]]:
    """
    تقسيم النطاق إلى مجموعات متساوية
    
    Args:
        start: رقم الكتاب الأول
        end: رقم الكتاب الأخير
        num_scripts: عدد السكربتات
        
    Returns:
        قائمة من tuples (start, end) لكل سكربت
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


def run_single_script(start: int, end: int, script_num: int, total: int):
    """
    تشغيل سكربت واحد مع نطاق محدد
    
    Args:
        start: رقم الكتاب الأول
        end: رقم الكتاب الأخير
        script_num: رقم السكربت
        total: العدد الإجمالي للسكربتات
    """
    try:
        print(f"🚀 [السكربت {script_num}/{total}] بدء: من الكتاب {start} إلى {end}")
        
        # إنشاء input للنطاق (start, end, y للتأكيد)
        input_data = f"{start}\n{end}\ny\n"
        
        # تشغيل السكربت
        process = subprocess.Popen(
            [sys.executable, SCRIPT_NAME],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # إرسال input
        stdout, stderr = process.communicate(input=input_data, timeout=None)
        
        if process.returncode == 0:
            print(f"✅ [السكربت {script_num}/{total}] اكتمل: من {start} إلى {end}")
        else:
            error_msg = stderr[:300] if stderr else "Unknown error"
            print(f"❌ [السكربت {script_num}/{total}] فشل: من {start} إلى {end}")
            print(f"   الخطأ: {error_msg}")
            
    except Exception as e:
        print(f"❌ [السكربت {script_num}/{total}] خطأ: {e}")


def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🚀 سكريبت تشغيل متوازي لفحص الكتب")
    print("=" * 70)
    
    # التحقق من وجود الملفات
    if not os.path.exists(SCRIPT_NAME):
        print(f"❌ السكربت غير موجود: {SCRIPT_NAME}")
        sys.exit(1)
    
    if not os.path.exists(BOOKS_FILE):
        print(f"❌ ملف الكتب غير موجود: {BOOKS_FILE}")
        sys.exit(1)
    
    # قراءة عدد الكتب الفعلي
    try:
        with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        total_books_in_file = len(data.get("books", []))
        print(f"📚 عدد الكتب في الملف: {total_books_in_file}")
    except:
        total_books_in_file = END_BOOK
    
    # التحقق من النطاق
    if START_BOOK < 1 or START_BOOK > total_books_in_file:
        print(f"❌ رقم البداية غير صحيح (يجب أن يكون بين 1 و {total_books_in_file})")
        sys.exit(1)
    if END_BOOK < START_BOOK or END_BOOK > total_books_in_file:
        print(f"❌ رقم النهاية غير صحيح (يجب أن يكون بين {START_BOOK} و {total_books_in_file})")
        sys.exit(1)
    
    # حساب النطاقات
    total_books_to_process = END_BOOK - START_BOOK + 1
    print(f"\n📊 تقسيم {total_books_to_process} كتاب (من {START_BOOK} إلى {END_BOOK}) على {NUM_SCRIPTS} سكربت...")
    ranges = calculate_ranges(START_BOOK, END_BOOK, NUM_SCRIPTS)
    
    print(f"\n📋 النطاقات:")
    for i, (start, end) in enumerate(ranges, 1):
        count = end - start + 1
        print(f"   السكربت {i:2d}: من {start:4d} إلى {end:4d} ({count:3d} كتاب)")
    
    # تأكيد البدء
    print(f"\n{'='*70}")
    confirm = input(f"هل تريد البدء بتشغيل {NUM_SCRIPTS} سكربت متوازي؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        sys.exit(0)
    
    # تشغيل جميع السكربتات باستخدام multiprocessing
    print(f"\n🚀 بدء تشغيل {NUM_SCRIPTS} سكربت متوازي...\n")
    processes = []
    
    for i, (start, end) in enumerate(ranges, 1):
        p = Process(target=run_single_script, args=(start, end, i, NUM_SCRIPTS))
        p.start()
        processes.append(p)
        time.sleep(0.2)  # تأخير قصير بين كل سكربت
    
    print(f"\n✅ تم بدء تشغيل جميع السكربتات ({NUM_SCRIPTS} سكربت)")
    print(f"⏳ جاري الانتظار حتى اكتمال جميع السكربتات...\n")
    
    # انتظار اكتمال جميع العمليات
    completed = 0
    for i, p in enumerate(processes, 1):
        p.join()
        completed += 1
        print(f"📊 التقدم: {completed}/{NUM_SCRIPTS} سكربت اكتمل")
    
    print(f"\n{'='*70}")
    print(f"✅ اكتملت جميع السكربتات ({completed}/{NUM_SCRIPTS})")
    print(f"{'='*70}")
    print("\n🎉 اكتملت العملية بنجاح!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
        # إنهاء جميع العمليات
        import os
        os._exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
