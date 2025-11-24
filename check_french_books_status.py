#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لفحص حالة الكتب الفرنسية في MongoDB
يحدد الكتب الفرنسية التي تم فحصها بشكل خاطئ (كعربية بدلاً من فرنسية)
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict
from collections import defaultdict

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

def is_french_book(pdf_name: str) -> bool:
    """
    التحقق من أن الكتاب فرنسي
    أي كتاب يحتوي على "--" في اسمه هو فرنسي
    """
    if not pdf_name:
        return False
    return "--" in pdf_name

def check_french_books_in_mongodb(collection):
    """
    فحص جميع الكتب الفرنسية في MongoDB
    يحدد الكتب التي تم فحصها بشكل خاطئ
    """
    print("🔍 جاري فحص جميع الكتب في MongoDB...")
    
    french_books = []
    incorrectly_processed = []  # كتب فرنسية تم فحصها كعربية
    correctly_processed = []    # كتب فرنسية تم فحصها كفرنسية
    not_processed = []          # كتب فرنسية لم يتم فحصها بعد
    
    total_books = 0
    total_french = 0
    
    for book in collection.find({}):
        total_books += 1
        pdf_name = book.get("pdfName", "")
        book_id = str(book.get("_id", ""))
        title = book.get("title", "")
        language = book.get("language", "ara")  # اللغة المحفوظة في MongoDB
        
        # التحقق من أن الكتاب فرنسي
        if is_french_book(pdf_name):
            total_french += 1
            book_info = {
                "_id": book_id,
                "title": title,
                "pdfName": pdf_name,
                "pdfLink": book.get("pdfLink", ""),
                "saved_language": language,
                "number_of_pages": book.get("number_of_pages", 0),
                "processed_at": book.get("processed_at", "")
            }
            french_books.append(book_info)
            
            # تصنيف حسب اللغة المحفوظة
            if language == "fra":
                correctly_processed.append(book_info)
            elif language == "ara":
                incorrectly_processed.append(book_info)
            else:
                # لغة أخرى أو غير محدد
                incorrectly_processed.append(book_info)
    
    return {
        "total_books": total_books,
        "total_french": total_french,
        "french_books": french_books,
        "correctly_processed": correctly_processed,
        "incorrectly_processed": incorrectly_processed,
    }

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🇫🇷 فحص حالة الكتب الفرنسية في MongoDB")
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
    
    # فحص الكتب الفرنسية
    results = check_french_books_in_mongodb(collection)
    
    # عرض الإحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"📚 إجمالي الكتب في MongoDB: {results['total_books']}")
    print(f"🇫🇷 إجمالي الكتب الفرنسية: {results['total_french']}")
    print(f"✅ تم فحصها بشكل صحيح (fra): {len(results['correctly_processed'])}")
    print(f"❌ تم فحصها بشكل خاطئ (ara): {len(results['incorrectly_processed'])}")
    
    if results['total_french'] > 0:
        correct_percent = (len(results['correctly_processed']) / results['total_french']) * 100
        incorrect_percent = (len(results['incorrectly_processed']) / results['total_french']) * 100
        print(f"\n📊 النسب:")
        print(f"   ✅ صحيح: {correct_percent:.1f}%")
        print(f"   ❌ خاطئ: {incorrect_percent:.1f}%")
    
    # عرض الكتب التي تم فحصها بشكل خاطئ
    if results['incorrectly_processed']:
        print(f"\n{'='*70}")
        print(f"❌ الكتب الفرنسية التي تم فحصها بشكل خاطئ ({len(results['incorrectly_processed'])} كتاب):")
        print(f"{'='*70}")
        print(f"{'ID':<15} {'اسم الملف':<30} {'العنوان':<50} {'الصفحات':<10} {'اللغة المحفوظة'}")
        print("-" * 70)
        
        for book in results['incorrectly_processed'][:20]:  # أول 20 فقط
            pdf_name = book['pdfName'][:28]
            title = book['title'][:48]
            print(f"{book['_id']:<15} {pdf_name:<30} {title:<50} {book['number_of_pages']:<10} {book['saved_language']}")
        
        if len(results['incorrectly_processed']) > 20:
            print(f"\n... و {len(results['incorrectly_processed']) - 20} كتاب آخر")
    
    # عرض عينة من الكتب الصحيحة
    if results['correctly_processed']:
        print(f"\n{'='*70}")
        print(f"✅ عينة من الكتب الفرنسية التي تم فحصها بشكل صحيح (أول 5):")
        print(f"{'='*70}")
        for i, book in enumerate(results['correctly_processed'][:5], 1):
            print(f"  {i}. {book['pdfName']}: {book['title'][:60]}")
    
    # حفظ الكتب التي تحتاج إعادة فحص
    if results['incorrectly_processed']:
        print(f"\n{'='*70}")
        print("💾 حفظ الكتب التي تحتاج إعادة فحص...")
        
        output_file = "french_books_incorrectly_processed.json"
        output_data = {
            "description": "كتب فرنسية تم فحصها بشكل خاطئ (كعربية بدلاً من فرنسية)",
            "total": len(results['incorrectly_processed']),
            "exported_at": datetime.now().isoformat(),
            "books": results['incorrectly_processed']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم حفظ {len(results['incorrectly_processed'])} كتاب في {output_file}")
        print(f"💡 يمكنك استخدام هذا الملف لإعادة فحص الكتب الفرنسية")
    
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

