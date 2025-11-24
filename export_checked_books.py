#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لجلب أسماء وروابط الكتب المفحوصة من MongoDB
وتخزينها في ملف JSON
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

# اسم ملف الإخراج (سيحفظ في المجلد الحالي حيث يتم تشغيل السكربت)
OUTPUT_FILE = "checked_books.json"

def get_checked_books(collection) -> List[Dict]:
    """
    جلب جميع الكتب المفحوصة من MongoDB
    
    Returns:
        قائمة بالكتب مع معلوماتها
    """
    books = []
    
    # جلب جميع الكتب
    for book in collection.find({}):
        book_data = {
            "_id": str(book.get("_id", "")),
            "title": book.get("title", ""),
            "pdfName": book.get("pdfName", ""),
            "pdfLink": book.get("pdfLink", ""),
            "url": book.get("url", book.get("pdfLink", "")),
            "book_name": book.get("book_name", ""),
            "number_of_pages": book.get("number_of_pages", 0),
            "language": book.get("language", "ara"),
            "used_ocr": book.get("used_ocr", False),
            "processed_at": book.get("processed_at", "")
        }
        books.append(book_data)
    
    return books

def save_to_json(books: List[Dict], output_file: str):
    """
    حفظ الكتب في ملف JSON
    
    Args:
        books: قائمة الكتب
        output_file: اسم ملف الإخراج
    """
    # إضافة معلومات إضافية
    data = {
        "export_date": datetime.now().isoformat(),
        "total_books": len(books),
        "books": books
    }
    
    # حفظ الملف
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم حفظ {len(books)} كتاب في {output_file}")

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("📚 جلب الكتب المفحوصة من MongoDB")
    print("=" * 70)
    
    # الاتصال بـ MongoDB
    print("\n📡 جاري الاتصال بـ MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("✅ تم الاتصال بـ MongoDB بنجاح")
    except Exception as e:
        print(f"❌ فشل الاتصال بـ MongoDB: {e}")
        return
    
    # جلب الكتب
    print(f"\n🔍 جاري جلب الكتب المفحوصة...")
    books = get_checked_books(collection)
    
    if not books:
        print("❌ لم يتم العثور على كتب مفحوصة")
        client.close()
        return
    
    print(f"✅ تم العثور على {len(books)} كتاب مفحوص")
    
    # عرض عينة
    print(f"\n📋 عينة من الكتب (أول 5):")
    for i, book in enumerate(books[:5], 1):
        print(f"  {i}. {book.get('title', 'بدون عنوان')[:60]}")
        print(f"     الرابط: {book.get('pdfLink', 'N/A')[:80]}")
        print(f"     الصفحات: {book.get('number_of_pages', 0)}")
        print()
    
    # حفظ في ملف JSON
    print(f"\n💾 جاري حفظ الكتب في {OUTPUT_FILE}...")
    save_to_json(books, OUTPUT_FILE)
    
    # إحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"📚 إجمالي الكتب: {len(books)}")
    
    # إحصائيات حسب اللغة
    languages = {}
    for book in books:
        lang = book.get("language", "ara")
        languages[lang] = languages.get(lang, 0) + 1
    
    print(f"\n🌐 حسب اللغة:")
    for lang, count in languages.items():
        lang_name = "عربي" if lang == "ara" else "فرنسي" if lang == "fra" else lang
        print(f"  - {lang_name}: {count} كتاب")
    
    # إحصائيات حسب OCR
    ocr_count = sum(1 for book in books if book.get("used_ocr", False))
    print(f"\n🔍 استخدام OCR: {ocr_count} كتاب")
    
    # إجمالي الصفحات
    total_pages = sum(book.get("number_of_pages", 0) for book in books)
    print(f"📄 إجمالي الصفحات: {total_pages} صفحة")
    
    file_path = os.path.abspath(OUTPUT_FILE)
    print(f"\n{'='*70}")
    print(f"✅ تم حفظ الملف في المجلد الحالي:")
    print(f"   📁 {file_path}")
    print(f"{'='*70}")
    
    client.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()

