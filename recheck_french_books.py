#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإعادة فحص الكتب الفرنسية من MongoDB
يجد جميع الكتب الفرنسية (التي تحتوي على "--" في pdfName) ويعيد فحصها
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

# إعدادات
BOOKS_FILE = "books-2025-11-09T23-13-42-652Z.json"
OUTPUT_FILE = "french_books_to_recheck.json"

def is_french_book(pdf_name: str) -> bool:
    """التحقق من أن الكتاب فرنسي"""
    if not pdf_name:
        return False
    return "--" in pdf_name

def get_french_books_from_mongodb(collection) -> List[Dict]:
    """جلب جميع الكتب الفرنسية من MongoDB"""
    french_books = []
    
    for book in collection.find({}):
        pdf_name = book.get("pdfName", "")
        if is_french_book(pdf_name):
            # إضافة معلومات الكتاب
            book_data = {
                "_id": str(book.get("_id", "")),
                "title": book.get("title", ""),
                "pdfName": pdf_name,
                "pdfLink": book.get("pdfLink", ""),
                "url": book.get("url", book.get("pdfLink", "")),
            }
            french_books.append(book_data)
    
    return french_books

def get_french_books_from_file() -> List[Dict]:
    """جلب جميع الكتب الفرنسية من ملف JSON"""
    if not os.path.exists(BOOKS_FILE):
        return []
    
    with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    books = data.get("books", [])
    french_books = []
    
    for book in books:
        pdf_name = book.get("pdfName", "")
        if is_french_book(pdf_name):
            french_books.append(book)
    
    return french_books

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🇫🇷 إعادة فحص الكتب الفرنسية")
    print("=" * 70)
    
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
    
    # جلب الكتب الفرنسية من MongoDB
    print(f"\n🔍 جاري البحث عن الكتب الفرنسية في MongoDB...")
    french_in_mongo = get_french_books_from_mongodb(collection)
    print(f"✅ تم العثور على {len(french_in_mongo)} كتاب فرنسي في MongoDB")
    
    # جلب الكتب الفرنسية من الملف
    print(f"\n🔍 جاري البحث عن الكتب الفرنسية في الملف...")
    french_in_file = get_french_books_from_file()
    print(f"✅ تم العثور على {len(french_in_file)} كتاب فرنسي في الملف")
    
    # دمج القوائم (إزالة التكرارات)
    all_french_books = {}
    for book in french_in_file:
        book_id = str(book.get("_id", ""))
        all_french_books[book_id] = book
    
    # إضافة الكتب من MongoDB إذا لم تكن موجودة
    for book in french_in_mongo:
        book_id = book.get("_id", "")
        if book_id not in all_french_books:
            all_french_books[book_id] = book
    
    french_books_list = list(all_french_books.values())
    total_french = len(french_books_list)
    
    # عرض عينة
    print(f"\n📋 عينة من الكتب الفرنسية (أول 5):")
    for i, book in enumerate(french_books_list[:5], 1):
        pdf_name = book.get("pdfName", "N/A")
        title = book.get("title", "بدون عنوان")[:60]
        print(f"  {i}. {pdf_name}: {title}")
    
    # حفظ الملف
    print(f"\n💾 جاري حفظ الكتب الفرنسية في {OUTPUT_FILE}...")
    output_data = {
        "exportedAt": datetime.now().isoformat(),
        "total": total_french,
        "description": "كتب فرنسية لإعادة الفحص (تحتوي على '--' في اسم الملف)",
        "note": "هذه الكتب تحتاج إعادة فحص باللغة الفرنسية (fra) بدل العربية (ara)",
        "books": french_books_list
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم حفظ {total_french} كتاب فرنسي في {OUTPUT_FILE}")
    
    # الإحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"🇫🇷 إجمالي الكتب الفرنسية: {total_french}")
    print(f"📄 من MongoDB: {len(french_in_mongo)}")
    print(f"📄 من الملف: {len(french_in_file)}")
    
    print(f"\n{'='*70}")
    print(f"✅ اكتملت العملية!")
    print(f"{'='*70}")
    print(f"\n📁 الملف الجديد: {os.path.abspath(OUTPUT_FILE)}")
    print(f"💡 يمكنك الآن:")
    print(f"   1. استبدال الملف الأصلي بهذا الملف")
    print(f"   2. أو استخدامه لفحص الكتب الفرنسية فقط")
    print(f"   3. السكربتات ستكتشف تلقائياً أنها فرنسية (-- في الاسم)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()

