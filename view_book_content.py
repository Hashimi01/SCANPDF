#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لعرض محتوى كتاب من MongoDB
"""

import sys
from pymongo import MongoClient

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

def find_book_by_pdf_name(collection, pdf_name: str):
    """البحث عن كتاب باسم ملف PDF"""
    book = collection.find_one({"pdfName": pdf_name})
    return book

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
        print("  python view_book_content.py <pdf_name>")
        print("  python view_book_content.py --id <book_id>")
        print("\nأمثلة:")
        print("  python view_book_content.py 798--.pdf")
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
    else:
        pdf_name = sys.argv[1]
        print(f"🔍 البحث عن الكتاب: {pdf_name}")
        book = find_book_by_pdf_name(collection, pdf_name)
    
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

