#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإنشاء ملف JSON جديد بالكتب التي لم تفحص بعد
واستبدال الملف الأصلي بالملف الجديد
"""

import json
import os
import shutil
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict, Set

# إعدادات
ORIGINAL_FILE = "books-2025-11-09T23-13-42-652Z.json"
BACKUP_FILE = "books-2025-11-09T23-13-42-652Z.json.backup"
NEW_FILE = "books-2025-11-09T23-13-42-652Z.json"

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"

def load_original_books(file_path: str) -> Dict:
    """تحميل الملف الأصلي"""
    if not os.path.exists(file_path):
        print(f"❌ الملف غير موجود: {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_checked_book_ids(collection) -> Set[str]:
    """الحصول على قائمة IDs الكتب المفحوصة من MongoDB"""
    checked_ids = set()
    for book in collection.find({}, {"_id": 1}):
        checked_ids.add(str(book["_id"]))
    return checked_ids

def filter_unchecked_books(books: List[Dict], checked_ids: Set[str]) -> List[Dict]:
    """تصفية الكتب غير المفحوصة"""
    unchecked = []
    for book in books:
        book_id = str(book.get("_id", ""))
        if book_id not in checked_ids:
            unchecked.append(book)
    return unchecked

def create_backup(original_file: str, backup_file: str):
    """إنشاء نسخة احتياطية من الملف الأصلي"""
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✅ تم إنشاء نسخة احتياطية: {backup_file}")

def save_new_file(data: Dict, unchecked_books: List[Dict], output_file: str):
    """حفظ الملف الجديد بالكتب غير المفحوصة"""
    new_data = {
        "exportedAt": datetime.now().isoformat(),
        "total": len(unchecked_books),
        "original_total": data.get("total", 0),
        "checked_count": data.get("total", 0) - len(unchecked_books),
        "unchecked_count": len(unchecked_books),
        "books": unchecked_books
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ تم حفظ الملف الجديد: {output_file}")

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("📚 إنشاء ملف بالكتب غير المفحوصة")
    print("=" * 70)
    
    # تحميل الملف الأصلي
    print(f"\n📖 جاري تحميل الملف الأصلي: {ORIGINAL_FILE}")
    original_data = load_original_books(ORIGINAL_FILE)
    if not original_data:
        return
    
    books = original_data.get("books", [])
    total_books = len(books)
    print(f"✅ تم تحميل {total_books} كتاب من الملف الأصلي")
    
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
    
    # جلب الكتب المفحوصة
    print(f"\n🔍 جاري فحص الكتب المفحوصة في MongoDB...")
    checked_ids = get_checked_book_ids(collection)
    checked_count = len(checked_ids)
    print(f"✅ تم العثور على {checked_count} كتاب مفحوص")
    
    # تصفية الكتب غير المفحوصة
    print(f"\n🔍 جاري تصفية الكتب غير المفحوصة...")
    unchecked_books = filter_unchecked_books(books, checked_ids)
    unchecked_count = len(unchecked_books)
    print(f"✅ تم العثور على {unchecked_count} كتاب غير مفحوص")
    
    # الإحصائيات
    print(f"\n{'='*70}")
    print("📊 الإحصائيات:")
    print(f"{'='*70}")
    print(f"📚 إجمالي الكتب في الملف الأصلي: {total_books}")
    print(f"✅ الكتب المفحوصة: {checked_count}")
    print(f"❌ الكتب غير المفحوصة: {unchecked_count}")
    print(f"📊 نسبة الإنجاز: {(checked_count / total_books * 100):.1f}%")
    
    if unchecked_count == 0:
        print(f"\n🎉 جميع الكتب تم فحصها!")
        client.close()
        return
    
    # تأكيد
    print(f"\n{'='*70}")
    print(f"⚠️  سيتم:")
    print(f"   1. إنشاء نسخة احتياطية من الملف الأصلي")
    print(f"   2. استبدال الملف الأصلي بملف جديد يحتوي على {unchecked_count} كتاب غير مفحوص")
    print(f"{'='*70}")
    confirm = input(f"\nهل تريد المتابعة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        client.close()
        return
    
    # إنشاء نسخة احتياطية
    print(f"\n💾 جاري إنشاء نسخة احتياطية...")
    create_backup(ORIGINAL_FILE, BACKUP_FILE)
    
    # حفظ الملف الجديد
    print(f"\n💾 جاري حفظ الملف الجديد...")
    save_new_file(original_data, unchecked_books, NEW_FILE)
    
    print(f"\n{'='*70}")
    print("✅ اكتملت العملية!")
    print(f"{'='*70}")
    print(f"\n📁 الملفات:")
    print(f"   📄 الملف الجديد: {NEW_FILE} ({unchecked_count} كتاب)")
    print(f"   💾 النسخة الاحتياطية: {BACKUP_FILE} ({total_books} كتاب)")
    print(f"\n💡 يمكنك الآن:")
    print(f"   - استخدام الملف الجديد لفحص الكتب المتبقية")
    print(f"   - استرجاع الملف الأصلي من النسخة الاحتياطية إذا لزم الأمر")
    
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

