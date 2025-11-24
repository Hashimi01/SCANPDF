#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت سريع لتفريغ مساحة القرص
"""

import subprocess
import os
import sys

def get_disk_usage():
    """الحصول على استخدام القرص"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def clean_temp_files():
    """تنظيف الملفات المؤقتة"""
    cleaned_size = 0
    temp_paths = [
        '/tmp',
        '/tmp/i2pdf_temp',
        '/root/i2pdf/temp_i2pdf_old.py',
    ]
    
    print("🧹 جاري تنظيف الملفات المؤقتة...")
    
    for temp_path in temp_paths:
        if os.path.exists(temp_path):
            try:
                if os.path.isdir(temp_path):
                    # حذف جميع الملفات في المجلد المؤقت
                    result = subprocess.run(
                        ['du', '-sh', temp_path],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        size_str = result.stdout.split()[0]
                        print(f"   📁 {temp_path}: {size_str}")
                    
                    # حذف الملفات
                    subprocess.run(['rm', '-rf', f'{temp_path}/*'], timeout=30)
                    print(f"   ✅ تم تنظيف {temp_path}")
            except Exception as e:
                print(f"   ⚠️  خطأ في {temp_path}: {e}")

def clean_old_logs():
    """تنظيف ملفات السجلات القديمة"""
    try:
        # حذف ملفات log القديمة
        subprocess.run(['find', '/var/log', '-type', 'f', '-mtime', '+7', '-delete'], timeout=30)
        print("   ✅ تم تنظيف ملفات السجلات القديمة")
    except:
        pass

def clean_python_cache():
    """تنظيف Python cache"""
    try:
        # حذف __pycache__
        subprocess.run(['find', '/root', '-type', 'd', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'], timeout=30)
        print("   ✅ تم تنظيف Python cache")
    except:
        pass

def clean_apt_cache():
    """تنظيف apt cache"""
    try:
        subprocess.run(['apt', 'clean'], timeout=30)
        print("   ✅ تم تنظيف apt cache")
    except:
        pass

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🧹 تفريغ مساحة القرص")
    print("=" * 70)
    
    # عرض الاستخدام الحالي
    print("\n📊 الاستخدام الحالي:")
    disk = get_disk_usage()
    if disk:
        print(disk)
    
    # تأكيد
    print(f"\n{'='*70}")
    confirm = input("هل تريد تفريغ مساحة القرص؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        return
    
    # التنظيف
    print(f"\n🧹 بدء التنظيف...\n")
    
    # 1. تنظيف الملفات المؤقتة
    clean_temp_files()
    
    # 2. تنظيف Python cache
    clean_python_cache()
    
    # 3. تنظيف apt cache
    clean_apt_cache()
    
    # 4. تنظيف السجلات القديمة
    clean_old_logs()
    
    # عرض الاستخدام بعد التنظيف
    print(f"\n{'='*70}")
    print("📊 الاستخدام بعد التنظيف:")
    disk = get_disk_usage()
    if disk:
        print(disk)
    
    print(f"\n{'='*70}")
    print("✅ اكتملت العملية!")
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

