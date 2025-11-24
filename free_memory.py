#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لتحرير الذاكرة (RAM) والقرص
"""

import subprocess
import os
import sys

def get_memory_usage():
    """الحصول على استخدام الذاكرة"""
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def get_disk_usage():
    """الحصول على استخدام القرص"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def clear_cache():
    """تنظيف cache النظام"""
    try:
        # تنظيف page cache, dentries, and inodes
        subprocess.run(['sync'], check=True, timeout=10)
        subprocess.run(['echo', '3'], stdout=open('/proc/sys/vm/drop_caches', 'w'), timeout=5)
        return True
    except Exception as e:
        print(f"⚠️  خطأ في تنظيف cache: {e}")
        return False

def clean_temp_files():
    """تنظيف الملفات المؤقتة"""
    cleaned = 0
    temp_dirs = [
        '/tmp',
        '/root/i2pdf/temp_i2pdf_old.py',  # إذا كان ملف
        '/tmp/i2pdf_temp',
    ]
    
    for temp_path in temp_dirs:
        if os.path.exists(temp_path):
            try:
                if os.path.isdir(temp_path):
                    # حذف الملفات القديمة فقط (أكثر من ساعة)
                    result = subprocess.run(
                        ['find', temp_path, '-type', 'f', '-mmin', '+60', '-delete'],
                        capture_output=True,
                        timeout=30
                    )
                    # عد الملفات المحذوفة
                    cleaned += result.returncode == 0
                elif os.path.isfile(temp_path):
                    os.remove(temp_path)
                    cleaned += 1
            except Exception as e:
                print(f"⚠️  خطأ في تنظيف {temp_path}: {e}")
    
    return cleaned

def kill_idle_processes():
    """إنهاء العمليات المتوقفة/المتعطلة"""
    killed = 0
    processes_to_check = ['tesseract', 'ocrmypdf', 'python']
    
    try:
        # الحصول على قائمة العمليات
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        
        for line in result.stdout.split('\n'):
            for proc_name in processes_to_check:
                if proc_name in line.lower():
                    # استخراج PID
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            # التحقق من أن العملية متوقفة (zombie أو استخدام CPU 0%)
                            cpu_usage = float(parts[2]) if len(parts) > 2 else 0
                            if cpu_usage == 0 and 'zombie' in line.lower():
                                subprocess.run(['kill', '-9', str(pid)], timeout=5)
                                killed += 1
                        except:
                            pass
    except Exception as e:
        print(f"⚠️  خطأ في إنهاء العمليات: {e}")
    
    return killed

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🧹 تنظيف الذاكرة والقرص")
    print("=" * 70)
    
    # عرض الاستخدام الحالي
    print("\n📊 الاستخدام الحالي:")
    print("-" * 70)
    
    memory = get_memory_usage()
    if memory:
        print("💾 الذاكرة (RAM):")
        print(memory)
    
    disk = get_disk_usage()
    if disk:
        print("\n💿 القرص:")
        print(disk)
    
    # الخيارات
    print(f"\n{'='*70}")
    print("🔧 خيارات التنظيف:")
    print(f"{'='*70}")
    print("1. تنظيف cache النظام (يحرر RAM)")
    print("2. تنظيف الملفات المؤقتة (يحرر Disk)")
    print("3. إنهاء العمليات المتوقفة (يحرر RAM)")
    print("4. كل ما سبق")
    print("5. إلغاء")
    
    choice = input("\nاختر الخيار (1-5): ").strip()
    
    if choice == '5':
        print("❌ تم الإلغاء")
        return
    
    cleaned = False
    
    if choice in ['1', '4']:
        print("\n🧹 جاري تنظيف cache النظام...")
        if clear_cache():
            print("✅ تم تنظيف cache النظام")
            cleaned = True
        else:
            print("❌ فشل تنظيف cache")
    
    if choice in ['2', '4']:
        print("\n🧹 جاري تنظيف الملفات المؤقتة...")
        cleaned_count = clean_temp_files()
        if cleaned_count > 0:
            print(f"✅ تم تنظيف {cleaned_count} ملف/مجلد مؤقت")
            cleaned = True
        else:
            print("ℹ️  لا توجد ملفات مؤقتة للتنظيف")
    
    if choice in ['3', '4']:
        print("\n🧹 جاري إنهاء العمليات المتوقفة...")
        killed_count = kill_idle_processes()
        if killed_count > 0:
            print(f"✅ تم إنهاء {killed_count} عملية متوقفة")
            cleaned = True
        else:
            print("ℹ️  لا توجد عمليات متوقفة")
    
    if cleaned:
        # عرض الاستخدام بعد التنظيف
        print(f"\n{'='*70}")
        print("📊 الاستخدام بعد التنظيف:")
        print("-" * 70)
        
        memory = get_memory_usage()
        if memory:
            print("💾 الذاكرة (RAM):")
            print(memory)
        
        disk = get_disk_usage()
        if disk:
            print("\n💿 القرص:")
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

