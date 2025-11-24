#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لعرض محتوى كتاب من MongoDB
"""

import sys
import re
from pymongo import MongoClient

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

def find_book_by_pdf_name(collection, pdf_name: str, exact_match: bool = False):
    """
    البحث عن كتاب باسم ملف PDF
    يدعم البحث الجزئي (يحتوي على) أو المطابقة الكاملة
    """
    if exact_match:
        # البحث المطابق الكامل
        book = collection.find_one({"pdfName": pdf_name})
        return book
    else:
        # البحث الجزئي (يحتوي على)
        # استخدام regex للبحث غير حساس لحالة الأحرف
        regex_pattern = re.compile(re.escape(pdf_name), re.IGNORECASE)
        books = list(collection.find({"pdfName": {"$regex": regex_pattern}}))
        
        if len(books) == 0:
            return None
        elif len(books) == 1:
            return books[0]
        else:
            # إذا وجد أكثر من كتاب، عرض القائمة
            print(f"\n⚠️  تم العثور على {len(books)} كتاب مطابق:")
            for i, b in enumerate(books[:10], 1):  # أول 10 فقط
                print(f"  {i}. {b.get('pdfName', 'N/A')} - {b.get('title', 'N/A')[:50]}")
            if len(books) > 10:
                print(f"  ... و {len(books) - 10} كتاب آخر")
            
            # إرجاع الأول (أو يمكن طلب اختيار)
            print(f"\n💡 سيتم عرض أول نتيجة: {books[0].get('pdfName', 'N/A')}")
            return books[0]

def find_book_by_id(collection, book_id: str):
    """البحث عن كتاب بـ ID"""
    book = collection.find_one({"_id": book_id})
    return book

def display_book_content(book):
    """عرض محتوى الكتاب"""
    if not book:
        print("❌ لم يتم العثور على الكتاب")
        return
    
    print("=" * 70)
    print("📖 معلومات الكتاب:")
    print("=" * 70)
    print(f"ID: {book.get('_id', 'N/A')}")
    print(f"العنوان: {book.get('title', 'N/A')}")
    print(f"اسم الملف: {book.get('pdfName', 'N/A')}")
    print(f"اللغة: {book.get('language', 'N/A')}")
    print(f"عدد الصفحات: {book.get('number_of_pages', 0)}")
    print(f"استخدم OCR: {book.get('used_ocr', False)}")
    print(f"تاريخ المعالجة: {book.get('processed_at', 'N/A')}")
    
    pages = book.get('pages', [])
    if not pages:
        print("\n⚠️  لا يوجد محتوى صفحات")
        return
    
    print(f"\n{'='*70}")
    print(f"📄 المحتوى ({len(pages)} صفحة):")
    print("=" * 70)
    
    # عرض أول 3 صفحات كاملة وباقي الصفحات مختصرة
    for i, page in enumerate(pages[:3], 1):
        content = page.get('content', '')
        page_num = page.get('page_number', i)
        print(f"\n{'─'*70}")
        print(f"📄 الصفحة {page_num}:")
        print(f"{'─'*70}")
        print(content[:2000])  # أول 2000 حرف
        if len(content) > 2000:
            print(f"\n... (تم اختصار المحتوى، الطول الكامل: {len(content)} حرف)")
    
    # عرض باقي الصفحات مختصرة
    if len(pages) > 3:
        print(f"\n{'─'*70}")
        print(f"📄 باقي الصفحات ({len(pages) - 3} صفحة):")
        print(f"{'─'*70}")
        for page in pages[3:]:
            content = page.get('content', '')
            page_num = page.get('page_number', 'N/A')
            preview = content[:200] if content else "(فارغة)"
            print(f"  الصفحة {page_num}: {preview}... ({len(content)} حرف)")

def main():
    """الدالة الرئيسية"""
    if len(sys.argv) < 2:
        print("الاستخدام:")
        print("  python view_book_content.py <pdf_name>          # بحث جزئي (افتراضي)")
        print("  python view_book_content.py --exact <pdf_name>   # بحث مطابق كامل")
        print("  python view_book_content.py --id <book_id>       # بحث بـ ID")
        print("\nأمثلة:")
        print("  python view_book_content.py 798                    # يبحث عن أي ملف يحتوي على '798'")
        print("  python view_book_content.py 798--.pdf             # بحث جزئي")
        print("  python view_book_content.py --exact 798--.pdf     # مطابقة كاملة")
        print("  python view_book_content.py --id 68f8cd0e9a41262d8d5af502")
        sys.exit(1)
    
    # الاتصال بـ MongoDB
    print("📡 جاري الاتصال بـ MongoDB...")
    try:
        # زيادة timeout وإضافة خيارات اتصال أفضل
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,  # 30 ثانية
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True
        )
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("✅ تم الاتصال بنجاح\n")
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}")
        print("\n💡 نصائح:")
        print("   - تحقق من الاتصال بالإنترنت")
        print("   - تحقق من أن IP الخاص بك مسموح في MongoDB Atlas")
        print("   - جرب مرة أخرى بعد قليل")
        sys.exit(1)
    
    # البحث عن الكتاب
    if sys.argv[1] == "--id" and len(sys.argv) >= 3:
        book_id = sys.argv[2]
        print(f"🔍 البحث عن الكتاب بـ ID: {book_id}")
        book = find_book_by_id(collection, book_id)
    elif sys.argv[1] == "--exact" and len(sys.argv) >= 3:
        # البحث المطابق الكامل
        pdf_name = sys.argv[2]
        print(f"🔍 البحث المطابق الكامل عن: {pdf_name}")
        book = find_book_by_pdf_name(collection, pdf_name, exact_match=True)
    else:
        # البحث الجزئي (افتراضي)
        pdf_name = sys.argv[1]
        print(f"🔍 البحث الجزئي عن: {pdf_name}")
        book = find_book_by_pdf_name(collection, pdf_name, exact_match=False)
    
    # عرض المحتوى
    display_book_content(book)
    
    client.close()
    print(f"\n{'='*70}")
    print("✅ اكتمل العرض")
    print("=" * 70)

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

