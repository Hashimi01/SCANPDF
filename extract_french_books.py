#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لاستخراج جميع الكتب الفرنسية (التي تحتوي على "--" في الاسم)
وإنشاء ملف جديد بها للفحص
"""

import json
import os
from datetime import datetime

# إعدادات
ORIGINAL_FILE = "books-2025-11-09T23-13-42-652Z.json"
FRENCH_BOOKS_FILE = "french_books.json"

def is_french_book(pdf_name: str) -> bool:
    """
    التحقق من أن الكتاب فرنسي (يحتوي على "--" في الاسم)
    
    Args:
        pdf_name: اسم ملف PDF
        
    Returns:
        True إذا كان فرنسي، False خلاف ذلك
    """
    if not pdf_name:
        return False
    
    # التحقق من وجود "--" في أي مكان في الاسم
    return "--" in pdf_name

def extract_french_books():
    """استخراج الكتب الفرنسية من الملف الأصلي"""
    print("=" * 70)
    print("🇫🇷 استخراج الكتب الفرنسية")
    print("=" * 70)
    
    # تحميل الملف الأصلي
    print(f"\n📖 جاري تحميل الملف: {ORIGINAL_FILE}")
    if not os.path.exists(ORIGINAL_FILE):
        print(f"❌ الملف غير موجود: {ORIGINAL_FILE}")
        return
    
    with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    books = data.get("books", [])
    total_books = len(books)
    print(f"✅ تم تحميل {total_books} كتاب")
    
    # استخراج الكتب الفرنسية
    print(f"\n🔍 جاري البحث عن الكتب الفرنسية...")
    french_books = []
    
    for book in books:
        pdf_name = book.get("pdfName", "")
        if is_french_book(pdf_name):
            french_books.append(book)
    
    french_count = len(french_books)
    print(f"✅ تم العثور على {french_count} كتاب فرنسي")
    
    if french_count == 0:
        print("❌ لم يتم العثور على كتب فرنسية")
        return
    
    # عرض عينة
    print(f"\n📋 عينة من الكتب الفرنسية (أول 5):")
    for i, book in enumerate(french_books[:5], 1):
        pdf_name = book.get("pdfName", "N/A")
        title = book.get("title", "بدون عنوان")[:60]
        print(f"  {i}. {pdf_name}: {title}")
    
    # حفظ الملف الجديد
    print(f"\n💾 جاري حفظ الكتب الفرنسية في {FRENCH_BOOKS_FILE}...")
    new_data = {
        "exportedAt": datetime.now().isoformat(),
        "total": french_count,
        "original_total": total_books,
        "description": "كتب فرنسية فقط (تحتوي على '--' في اسم الملف)",
        "books": french_books
    }
    
    with open(FRENCH_BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم حفظ {french_count} كتاب فرنسي في {FRENCH_BOOKS_FILE}")
    
    # الإحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"📚 إجمالي الكتب في الملف الأصلي: {total_books}")
    print(f"🇫🇷 الكتب الفرنسية: {french_count}")
    print(f"📄 الكتب الأخرى: {total_books - french_count}")
    print(f"📊 نسبة الكتب الفرنسية: {(french_count / total_books * 100):.1f}%")
    
    print(f"\n{'='*70}")
    print(f"✅ اكتملت العملية!")
    print(f"{'='*70}")
    print(f"\n📁 الملف الجديد: {os.path.abspath(FRENCH_BOOKS_FILE)}")
    print(f"💡 يمكنك الآن استخدام هذا الملف لفحص الكتب الفرنسية")

if __name__ == "__main__":
    try:
        extract_french_books()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()

