#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للعثور على الكتب التي تحتوي على [skipped page] في محتواها
هذا يعني أن OCR لم يستخرج النص بشكل صحيح
"""

import json
import os
from pymongo import MongoClient
from typing import List, Dict

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

def find_books_with_skipped_pages(collection):
    """البحث عن الكتب التي تحتوي على [skipped page]"""
    print("🔍 جاري البحث عن الكتب التي تحتوي على [skipped page]...")
    
    books_with_skipped = []
    total_books = 0
    
    for book in collection.find({}):
        total_books += 1
        pages = book.get('pages', [])
        
        skipped_count = 0
        total_pages = len(pages)
        
        for page in pages:
            content = page.get('content', '')
            if '[skipped page]' in content.lower():
                skipped_count += 1
        
        if skipped_count > 0:
            skipped_percent = (skipped_count / total_pages * 100) if total_pages > 0 else 0
            book_info = {
                "_id": str(book.get("_id", "")),
                "title": book.get("title", ""),
                "pdfName": book.get("pdfName", ""),
                "language": book.get("language", "ara"),
                "total_pages": total_pages,
                "skipped_pages": skipped_count,
                "skipped_percent": skipped_percent,
                "processed_at": book.get("processed_at", "")
            }
            books_with_skipped.append(book_info)
    
    return books_with_skipped, total_books

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔍 البحث عن الكتب التي تحتوي على [skipped page]")
    print("=" * 70)
    
    # الاتصال بـ MongoDB
    print(f"\n📡 جاري الاتصال بـ MongoDB...")
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.admin.command('ping')
        collection = client[DB_NAME][COLLECTION_NAME]
        print("✅ تم الاتصال بنجاح")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        return
    
    # البحث عن الكتب
    books_with_skipped, total_books = find_books_with_skipped_pages(collection)
    
    # الإحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"📚 إجمالي الكتب في MongoDB: {total_books}")
    print(f"⚠️  كتب تحتوي على [skipped page]: {len(books_with_skipped)}")
    
    if len(books_with_skipped) > 0:
        percent = (len(books_with_skipped) / total_books * 100) if total_books > 0 else 0
        print(f"📊 النسبة: {percent:.1f}%")
    
    # تصنيف حسب اللغة
    if books_with_skipped:
        french_books = [b for b in books_with_skipped if b['language'] == 'fra']
        arabic_books = [b for b in books_with_skipped if b['language'] == 'ara']
        
        print(f"\n📊 التصنيف حسب اللغة:")
        print(f"   🇫🇷 فرنسية: {len(french_books)}")
        print(f"   🇸🇦 عربية: {len(arabic_books)}")
    
    # عرض الكتب
    if books_with_skipped:
        print(f"\n{'='*70}")
        print(f"⚠️  الكتب التي تحتوي على [skipped page] ({len(books_with_skipped)} كتاب):")
        print(f"{'='*70}")
        print(f"{'اسم الملف':<30} {'اللغة':<8} {'الصفحات':<12} {'مفقود':<10} {'النسبة':<10} {'العنوان'}")
        print("-" * 70)
        
        # ترتيب حسب نسبة الصفحات المفقودة
        books_sorted = sorted(books_with_skipped, key=lambda x: x['skipped_percent'], reverse=True)
        
        for book in books_sorted[:30]:  # أول 30 فقط
            pdf_name = book['pdfName'][:28]
            title = book['title'][:40]
            print(f"{pdf_name:<30} {book['language']:<8} {book['total_pages']:<4}/{book['skipped_pages']:<4} {'':<4} {book['skipped_percent']:.1f}%{'':<5} {title}")
        
        if len(books_sorted) > 30:
            print(f"\n... و {len(books_sorted) - 30} كتاب آخر")
        
        # حفظ الملف
        output_file = "books_with_skipped_pages.json"
        output_data = {
            "description": "كتب تحتوي على [skipped page] في محتواها - تحتاج إعادة فحص",
            "total": len(books_with_skipped),
            "total_books_in_db": total_books,
            "exported_at": str(os.popen('date').read().strip()),
            "books": books_with_skipped
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ {len(books_with_skipped)} كتاب في {output_file}")
        print(f"💡 يمكنك استخدام هذا الملف لإعادة فحص الكتب")
    else:
        print(f"\n✅ لا توجد كتب تحتوي على [skipped page]")
    
    client.close()
    print(f"\n{'='*70}")
    print("✅ اكتمل الفحص!")
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

