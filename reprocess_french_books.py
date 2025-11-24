#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإعادة فحص الكتب الفرنسية التي تم فحصها بشكل خاطئ
يقرأ من french_books_incorrectly_processed.json ويعيد فحصها باللغة الفرنسية
"""

import json
import os
import sys
from inspect_books_mongodb import (
    get_mongodb_collection,
    process_book_with_mongodb,
    kill_ocr_processes,
    reset_ocr_if_needed
)

# إعدادات
INPUT_FILE = "french_books_incorrectly_processed.json"

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🇫🇷 إعادة فحص الكتب الفرنسية")
    print("=" * 70)
    
    # قراءة ملف الكتب الفرنسية
    if not os.path.exists(INPUT_FILE):
        print(f"❌ الملف غير موجود: {INPUT_FILE}")
        print(f"💡 قم بتشغيل check_french_books_status.py أولاً")
        sys.exit(1)
    
    print(f"\n📚 جاري قراءة ملف الكتب: {INPUT_FILE}")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        sys.exit(1)
    
    books = data.get("books", [])
    if not books:
        print("❌ لم يتم العثور على كتب في الملف")
        sys.exit(1)
    
    total_books = len(books)
    print(f"✅ تم العثور على {total_books} كتاب فرنسي يحتاج إعادة فحص")
    
    # الاتصال بـ MongoDB
    print("\n📡 جاري الاتصال بـ MongoDB...")
    collection, client = get_mongodb_collection()
    
    # تأكيد
    print("\n" + "=" * 70)
    print(f"⚠️  سيتم إعادة فحص {total_books} كتاب فرنسي")
    print("⚠️  سيتم استبدال البيانات القديمة بالبيانات الجديدة (باللغة الفرنسية)")
    print("=" * 70)
    confirm = input("\nهل تريد المتابعة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        client.close()
        sys.exit(0)
    
    # معالجة الكتب
    print("\n" + "=" * 70)
    print("🚀 بدء عملية إعادة الفحص...")
    print("=" * 70)
    
    # تنظيف أي عمليات OCR متعطلة في البداية
    print("🧹 تنظيف عمليات OCR المتعطلة...")
    kill_ocr_processes()
    
    success_count = 0
    fail_count = 0
    saved_count = 0
    
    try:
        for idx, book in enumerate(books):
            # إضافة pdfLink إذا لم يكن موجوداً
            if not book.get("pdfLink") and book.get("pdfLink") is None:
                book["pdfLink"] = book.get("url", "")
            
            # معالجة الكتاب (auto_detect_lang=True سيكتشف أنها فرنسية من الاسم)
            result = process_book_with_mongodb(book, idx, total_books, collection, auto_detect_lang=True)
            if result:
                success_count += 1
                saved_count += 1
            else:
                fail_count += 1
            
            # تنظيف وقائي كل 5 كتب
            if (idx + 1) % 5 == 0:
                reset_ocr_if_needed()
                
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    finally:
        # تنظيف نهائي
        print("\n🧹 تنظيف نهائي لعمليات OCR...")
        kill_ocr_processes()
        
        # إغلاق الاتصال
        client.close()
        print("✅ تم إغلاق الاتصال بـ MongoDB")
    
    # الإحصائيات النهائية
    print("\n" + "=" * 70)
    print("📊 الإحصائيات النهائية:")
    print("=" * 70)
    print(f"   ✅ نجح: {success_count}")
    print(f"   💾 محفوظ في MongoDB: {saved_count}")
    print(f"   ❌ فشل: {fail_count}")
    print(f"   📄 إجمالي: {total_books}")
    
    print("\n" + "=" * 70)
    print("✅ اكتملت العملية!")
    print("=" * 70)
    print(f"\n💡 يمكنك التحقق من النتائج:")
    print(f"   - قم بتشغيل check_french_books_status.py مرة أخرى")
    print(f"   - يجب أن تتحسن نسبة الكتب الصحيحة")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم الإلغاء من قبل المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

