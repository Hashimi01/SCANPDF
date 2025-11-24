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

# النطاقات (من run_parallel_with_screens.py)
RANGES = [
    (1, 110, 150),   # script_1: من 110 إلى 150
    (2, 151, 191),   # script_2: من 151 إلى 191
    (3, 192, 232),   # script_3: من 192 إلى 232
    (4, 233, 273),   # script_4: من 233 إلى 273
    (5, 274, 314),   # script_5: من 274 إلى 314
    (6, 315, 355),   # script_6: من 315 إلى 355
    (7, 356, 396),   # script_7: من 356 إلى 396
    (8, 397, 436),   # script_8: من 397 إلى 436
    (9, 437, 476),   # script_9: من 437 إلى 476
    (10, 477, 516),  # script_10: من 477 إلى 516
    (11, 517, 556),  # script_11: من 517 إلى 556
    (12, 557, 596),  # script_12: من 557 إلى 596
    (13, 597, 636),  # script_13: من 597 إلى 636
    (14, 637, 676),  # script_14: من 637 إلى 676
    (15, 677, 716),  # script_15: من 677 إلى 716
    (16, 717, 756),  # script_16: من 717 إلى 756
    (17, 757, 796),  # script_17: من 757 إلى 796
    (18, 797, 836),  # script_18: من 797 إلى 836
    (19, 837, 876),  # script_19: من 837 إلى 876
    (20, 877, 916),  # script_20: من 877 إلى 916
    (21, 917, 956),  # script_21: من 917 إلى 956
    (22, 957, 996),  # script_22: من 957 إلى 996
    (23, 997, 1036), # script_23: من 997 إلى 1036
    (24, 1037, 1076), # script_24: من 1037 إلى 1076
    (25, 1077, 1116), # script_25: من 1077 إلى 1116
    (26, 1117, 1156), # script_26: من 1117 إلى 1156
    (27, 1157, 1196), # script_27: من 1157 إلى 1196
    (28, 1197, 1236), # script_28: من 1197 إلى 1236
    (29, 1237, 1276), # script_29: من 1237 إلى 1276
    (30, 1277, 1316), # script_30: من 1277 إلى 1316
    (31, 1317, 1356), # script_31: من 1317 إلى 1356
    (32, 1357, 1396), # script_32: من 1357 إلى 1396
    (33, 1397, 1436), # script_33: من 1397 إلى 1436
    (34, 1437, 1476), # script_34: من 1437 إلى 1476
    (35, 1477, 1516), # script_35: من 1477 إلى 1516
    (36, 1517, 1556), # script_36: من 1517 إلى 1556
    (37, 1557, 1596), # script_37: من 1557 إلى 1596
    (38, 1597, 1636), # script_38: من 1597 إلى 1636
    (39, 1637, 1676), # script_39: من 1637 إلى 1676
    (40, 1677, 1716), # script_40: من 1677 إلى 1716
    (41, 1717, 1756), # script_41: من 1717 إلى 1756
    (42, 1757, 1796), # script_42: من 1757 إلى 1796
    (43, 1797, 1836), # script_43: من 1797 إلى 1836
    (44, 1837, 1876), # script_44: من 1837 إلى 1876
    (45, 1877, 1916), # script_45: من 1877 إلى 1916
    (46, 1917, 1956), # script_46: من 1917 إلى 1956
    (47, 1957, 1996), # script_47: من 1957 إلى 1996
    (48, 1997, 2036), # script_48: من 1997 إلى 2036
    (49, 2037, 2076), # script_49: من 2037 إلى 2076
    (50, 2077, 2116), # script_50: من 2077 إلى 2116
]

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
    
    for script_num, start, end in RANGES:
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
