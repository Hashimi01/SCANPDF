#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للتحقق من تقدم كل جلسة screen
يحدد أي جلسات لم تحفظ أي كتاب بعد في MongoDB
"""

import json
import os
from pymongo import MongoClient
from typing import Dict, List, Tuple

# إعدادات
BOOKS_FILE = "books-2025-11-09T23-13-42-652Z.json"
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

# إعدادات (يتم تحديثها تلقائياً من الملف)
START_BOOK = 1  # من الكتاب رقم 1
NUM_SCRIPTS = 50  # عدد السكربتات المتوازية

def calculate_ranges(start: int, end: int, num_scripts: int) -> List[Tuple[int, int, int]]:
    """
    تقسيم النطاق إلى مجموعات متساوية (نفس منطق run_parallel_with_screens.py)
    
    Args:
        start: رقم الكتاب الأول
        end: رقم الكتاب الأخير
        num_scripts: عدد السكربتات
        
    Returns:
        قائمة من tuples (script_num, start, end) لكل سكربت
    """
    total_books = end - start + 1
    books_per_script = total_books // num_scripts
    remainder = total_books % num_scripts
    
    ranges = []
    current_start = start
    
    for i in range(1, num_scripts + 1):
        # توزيع الباقي على السكربتات الأولى
        current_end = current_start + books_per_script - 1
        if i <= remainder:
            current_end += 1
        
        # التأكد من عدم تجاوز النهاية
        if current_end > end:
            current_end = end
        
        if current_start <= end:
            ranges.append((i, current_start, current_end))
            current_start = current_end + 1
    
    return ranges

def load_books():
    """تحميل ملف الكتب"""
    if not os.path.exists(BOOKS_FILE):
        print(f"❌ الملف غير موجود: {BOOKS_FILE}")
        return None
    
    with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("books", [])

def get_saved_book_ids(collection):
    """الحصول على قائمة IDs الكتب المحفوظة في MongoDB"""
    saved_ids = set()
    for book in collection.find({}, {"_id": 1}):
        saved_ids.add(str(book["_id"]))
    return saved_ids

def check_range_progress(books: List[Dict], saved_ids: set, script_num: int, start: int, end: int) -> Dict:
    """
    فحص تقدم نطاق معين
    
    Returns:
        dict مع معلومات التقدم
    """
    # الحصول على الكتب في هذا النطاق (start و end هما أرقام الكتب 1-indexed)
    range_books = books[start-1:end]  # -1 لأن القائمة 0-indexed
    
    expected_count = len(range_books)
    saved_count = 0
    saved_book_ids = []
    missing_book_ids = []
    
    for book in range_books:
        book_id = str(book.get("_id", ""))
        if book_id in saved_ids:
            saved_count += 1
            saved_book_ids.append(book_id)
        else:
            missing_book_ids.append(book_id)
    
    progress_percent = (saved_count / expected_count * 100) if expected_count > 0 else 0
    
    return {
        "script_num": script_num,
        "start": start,
        "end": end,
        "expected": expected_count,
        "saved": saved_count,
        "missing": len(missing_book_ids),
        "progress": progress_percent,
        "status": "✅ يعمل" if saved_count > 0 else "❌ لم يبدأ",
        "missing_ids": missing_book_ids[:5]  # أول 5 فقط للعرض
    }

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔍 فحص تقدم جميع الجلسات")
    print("=" * 70)
    
    # تحميل الكتب
    print(f"\n📚 جاري تحميل ملف الكتب: {BOOKS_FILE}")
    books = load_books()
    if not books:
        print("❌ لم يتم العثور على كتب")
        return
    
    total_books = len(books)
    print(f"✅ تم تحميل {total_books} كتاب")
    
    # حساب النطاقات تلقائياً
    end_book = total_books
    ranges = calculate_ranges(START_BOOK, end_book, NUM_SCRIPTS)
    print(f"\n📊 تم تقسيم {total_books} كتاب على {NUM_SCRIPTS} سكربت")
    
    # الاتصال بـ MongoDB
    print(f"\n📡 جاري الاتصال بـ MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("✅ تم الاتصال بـ MongoDB بنجاح")
    except Exception as e:
        print(f"❌ فشل الاتصال بـ MongoDB: {e}")
        return
    
    # الحصول على الكتب المحفوظة
    print(f"\n🔍 جاري فحص الكتب المحفوظة في MongoDB...")
    saved_ids = get_saved_book_ids(collection)
    total_saved = len(saved_ids)
    print(f"✅ تم العثور على {total_saved} كتاب محفوظ في MongoDB")
    
    # فحص كل نطاق
    print(f"\n{'='*70}")
    print("📊 تقرير تقدم كل جلسة:")
    print(f"{'='*70}\n")
    
    results = []
    not_started = []
    in_progress = []
    completed = []
    
    for script_num, start, end in ranges:
        result = check_range_progress(books, saved_ids, script_num, start, end)
        results.append(result)
        
        if result["saved"] == 0:
            not_started.append(result)
        elif result["saved"] < result["expected"]:
            in_progress.append(result)
        else:
            completed.append(result)
    
    # عرض النتائج
    print(f"{'الجلسة':<8} {'النطاق':<15} {'المتوقع':<10} {'المحفوظ':<10} {'المفقود':<10} {'التقدم':<10} {'الحالة'}")
    print("-" * 70)
    
    for result in results:
        range_str = f"{result['start']}-{result['end']}"
        progress_str = f"{result['progress']:.1f}%"
        print(f"{result['script_num']:<8} {range_str:<15} {result['expected']:<10} {result['saved']:<10} {result['missing']:<10} {progress_str:<10} {result['status']}")
    
    # ملخص
    print(f"\n{'='*70}")
    print("📊 الملخص:")
    print(f"{'='*70}")
    print(f"✅ اكتملت: {len(completed)} جلسة")
    print(f"🔄 قيد العمل: {len(in_progress)} جلسة")
    print(f"❌ لم تبدأ: {len(not_started)} جلسة")
    print(f"📚 إجمالي الكتب المحفوظة: {total_saved}")
    
    # عرض الجلسات التي لم تبدأ
    if not_started:
        print(f"\n{'='*70}")
        print("❌ الجلسات التي لم تحفظ أي كتاب بعد:")
        print(f"{'='*70}")
        for result in not_started:
            print(f"  - الجلسة {result['script_num']}: من {result['start']} إلى {result['end']} ({result['expected']} كتاب)")
            print(f"    اسم الجلسة: book_script_{result['script_num']}")
    
    # عرض الجلسات قيد العمل
    if in_progress:
        print(f"\n{'='*70}")
        print("🔄 الجلسات قيد العمل (لم تكتمل بعد):")
        print(f"{'='*70}")
        for result in in_progress:
            print(f"  - الجلسة {result['script_num']}: {result['saved']}/{result['expected']} ({result['progress']:.1f}%)")
    
    client.close()
    print(f"\n{'='*70}")
    print("✅ اكتمل الفحص!")
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
