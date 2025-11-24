#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت سريع لفحص تقدم جلسات إعادة فحص الكتب الفرنسية
"""

import json
import os
from pymongo import MongoClient
from typing import List, Tuple

# إعدادات
INPUT_FILE = "french_books_incorrectly_processed.json"
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"
NUM_SCRIPTS = 20

def calculate_ranges(start: int, end: int, num_scripts: int) -> List[Tuple[int, int]]:
    """تقسيم النطاق"""
    total = end - start + 1
    per_script = total // num_scripts
    remainder = total % num_scripts
    
    ranges = []
    current = start
    for i in range(num_scripts):
        end_range = current + per_script - 1
        if i < remainder:
            end_range += 1
        if end_range > end:
            end_range = end
        if current <= end:
            ranges.append((current, end_range))
            current = end_range + 1
    return ranges

def main():
    print("=" * 70)
    print("🇫🇷 فحص تقدم إعادة فحص الكتب الفرنسية")
    print("=" * 70)
    
    # تحميل الكتب
    if not os.path.exists(INPUT_FILE):
        print(f"❌ الملف غير موجود: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    books = data.get("books", [])
    total = len(books)
    print(f"\n📚 إجمالي الكتب: {total}")
    
    # حساب النطاقات
    ranges = calculate_ranges(1, total, NUM_SCRIPTS)
    
    # الاتصال بـ MongoDB
    print(f"\n📡 جاري الاتصال بـ MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        collection = client[DB_NAME][COLLECTION_NAME]
        print("✅ تم الاتصال")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        return
    
    # فحص الكتب المحفوظة باللغة الفرنسية
    saved_french = {}
    for book in collection.find({"language": "fra"}, {"_id": 1, "pdfName": 1}):
        book_id = str(book.get("_id", ""))
        saved_french[book_id] = True
    
    print(f"✅ تم العثور على {len(saved_french)} كتاب فرنسي محفوظ بشكل صحيح\n")
    
    # فحص كل نطاق
    print(f"{'الجلسة':<10} {'النطاق':<15} {'المتوقع':<10} {'المحفوظ':<10} {'المتبقي':<10} {'التقدم':<10} {'الحالة'}")
    print("-" * 70)
    
    total_saved = 0
    total_expected = 0
    
    for i, (start, end) in enumerate(ranges, 1):
        range_books = books[start-1:end]
        expected = len(range_books)
        saved = sum(1 for b in range_books if str(b.get("_id", "")) in saved_french)
        remaining = expected - saved
        progress = (saved / expected * 100) if expected > 0 else 0
        
        total_expected += expected
        total_saved += saved
        
        status = "✅ اكتمل" if saved == expected else ("🔄 يعمل" if saved > 0 else "❌ لم يبدأ")
        range_str = f"{start}-{end}"
        print(f"{i:<10} {range_str:<15} {expected:<10} {saved:<10} {remaining:<10} {progress:.1f}%{'':<5} {status}")
    
    # الملخص
    total_progress = (total_saved / total_expected * 100) if total_expected > 0 else 0
    print(f"\n{'='*70}")
    print(f"📊 الملخص:")
    print(f"   ✅ محفوظ: {total_saved}/{total_expected} ({total_progress:.1f}%)")
    print(f"   ❌ متبقي: {total_expected - total_saved}")
    print(f"{'='*70}")
    
    client.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف")
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

