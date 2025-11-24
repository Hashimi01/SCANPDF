#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت شامل لتفريغ المساحة وتخفيف الضغط على السيرفر
ينظف الملفات المؤقتة، الذاكرة، والعمليات غير الضرورية
"""

import subprocess
import os
import sys
import time

def run_cmd(cmd, description, timeout=30):
    """تنفيذ أمر مع معالجة الأخطاء"""
    try:
        print(f"   🔄 {description}...", end=' ')
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            print("✅")
            return True
        else:
            print("⚠️")
            return False
    except subprocess.TimeoutExpired:
        print("⏱️  timeout")
        return False
    except Exception as e:
        print(f"❌ {e}")
        return False

def get_disk_usage():
    """عرض استخدام القرص"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def get_memory_usage():
    """عرض استخدام الذاكرة"""
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def clean_temp_files():
    """تنظيف الملفات المؤقتة"""
    print("\n🧹 تنظيف الملفات المؤقتة:")
    print("-" * 70)
    
    # تنظيف /tmp
    run_cmd("rm -rf /tmp/* 2>/dev/null", "تنظيف /tmp")
    
    # تنظيف /tmp/i2pdf_temp
    run_cmd("rm -rf /tmp/i2pdf_temp/* 2>/dev/null", "تنظيف /tmp/i2pdf_temp")
    
    # تنظيف ملفات Python المؤقتة
    run_cmd("find /tmp -name '*.pyc' -delete 2>/dev/null", "حذف ملفات .pyc")
    run_cmd("find /tmp -name '*.pyo' -delete 2>/dev/null", "حذف ملفات .pyo")
    
    # تنظيف .cache
    run_cmd("rm -rf /root/.cache/* 2>/dev/null", "تنظيف /root/.cache")

def clean_python_cache():
    """تنظيف Python cache"""
    print("\n🐍 تنظيف Python cache:")
    print("-" * 70)
    
    run_cmd("find /root -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null", 
            "حذف __pycache__")
    run_cmd("find /root -name '*.pyc' -delete 2>/dev/null", "حذف ملفات .pyc")
    run_cmd("find /root -name '*.pyo' -delete 2>/dev/null", "حذف ملفات .pyo")

def clean_apt_cache():
    """تنظيف apt cache"""
    print("\n📦 تنظيف apt cache:")
    print("-" * 70)
    
    run_cmd("apt clean", "تنظيف apt cache")
    run_cmd("apt autoremove -y", "حذف الحزم غير المستخدمة")
    run_cmd("apt autoclean", "تنظيف apt autoclean")

def clean_logs():
    """تنظيف ملفات السجلات"""
    print("\n📋 تنظيف ملفات السجلات:")
    print("-" * 70)
    
    # تنظيف journal logs
    run_cmd("journalctl --vacuum-time=3d 2>/dev/null", "تنظيف journal logs (أكثر من 3 أيام)")
    
    # تنظيف ملفات log القديمة
    run_cmd("find /var/log -type f -mtime +7 -delete 2>/dev/null", 
            "حذف ملفات log القديمة (أكثر من 7 أيام)")
    
    # تنظيف ملفات log الكبيرة
    run_cmd("find /var/log -type f -size +100M -delete 2>/dev/null", 
            "حذف ملفات log الكبيرة (أكثر من 100MB)")

def clean_docker():
    """تنظيف Docker"""
    print("\n🐳 تنظيف Docker:")
    print("-" * 70)
    
    # التحقق من وجود Docker
    result = subprocess.run(['which', 'docker'], capture_output=True)
    if result.returncode == 0:
        run_cmd("docker system prune -a -f --volumes 2>/dev/null", 
                "تنظيف Docker (images, containers, volumes)")
        run_cmd("docker volume prune -f 2>/dev/null", "تنظيف Docker volumes")
    else:
        print("   ℹ️  Docker غير مثبت")

def kill_zombie_processes():
    """إيقاف العمليات المتوقفة"""
    print("\n🛑 إيقاف العمليات المتوقفة:")
    print("-" * 70)
    
    # إيقاف عمليات OCR المتوقفة
    run_cmd("pkill -9 tesseract 2>/dev/null", "إيقاف عمليات tesseract")
    run_cmd("pkill -9 ocrmypdf 2>/dev/null", "إيقاف عمليات ocrmypdf")
    
    # إيقاف جلسات screen الميتة
    run_cmd("screen -wipe 2>/dev/null", "تنظيف جلسات screen الميتة")
    
    # إيقاف العمليات المتوقفة (zombie)
    run_cmd("killall -9 python3 2>/dev/null || true", "إيقاف عمليات Python المتوقفة")

def free_memory():
    """تحرير الذاكرة"""
    print("\n💾 تحرير الذاكرة:")
    print("-" * 70)
    
    # تنظيف page cache
    run_cmd("sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null", 
            "تنظيف page cache (يتطلب root)")
    
    # تنظيف swap
    run_cmd("swapoff -a && swapon -a 2>/dev/null", "إعادة تعيين swap")

def clean_old_pdf_temp():
    """تنظيف ملفات PDF المؤقتة القديمة"""
    print("\n📄 تنظيف ملفات PDF المؤقتة القديمة:")
    print("-" * 70)
    
    # حذف ملفات PDF المؤقتة القديمة (أكثر من 7 أيام)
    run_cmd("find /tmp/i2pdf_temp -type f -mtime +7 -delete 2>/dev/null", 
            "حذف ملفات PDF المؤقتة القديمة (أكثر من 7 أيام)")
    
    # حذف ملفات PDF المؤقتة الكبيرة (أكثر من 100MB)
    run_cmd("find /tmp/i2pdf_temp -type f -size +100M -delete 2>/dev/null", 
            "حذف ملفات PDF المؤقتة الكبيرة (أكثر من 100MB)")

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🧹 تفريغ المساحة وتخفيف الضغط على السيرفر")
    print("=" * 70)
    
    # عرض الاستخدام الحالي
    print("\n📊 الاستخدام الحالي:")
    print("-" * 70)
    
    disk = get_disk_usage()
    if disk:
        print("💾 استخدام القرص:")
        print(disk)
    
    memory = get_memory_usage()
    if memory:
        print("\n🧠 استخدام الذاكرة:")
        print(memory)
    
    # تأكيد
    print(f"\n{'='*70}")
    print("⚠️  سيتم تنفيذ العمليات التالية:")
    print("   1. تنظيف الملفات المؤقتة")
    print("   2. تنظيف Python cache")
    print("   3. تنظيف apt cache")
    print("   4. تنظيف ملفات السجلات")
    print("   5. تنظيف Docker (إن وجد)")
    print("   6. إيقاف العمليات المتوقفة")
    print("   7. تحرير الذاكرة")
    print("   8. تنظيف ملفات PDF المؤقتة القديمة")
    print(f"{'='*70}")
    confirm = input("\nهل تريد المتابعة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        return
    
    # بدء التنظيف
    print(f"\n{'='*70}")
    print("🚀 بدء عملية التنظيف...")
    print("=" * 70)
    
    start_time = time.time()
    
    # 1. تنظيف الملفات المؤقتة
    clean_temp_files()
    
    # 2. تنظيف Python cache
    clean_python_cache()
    
    # 3. تنظيف apt cache
    clean_apt_cache()
    
    # 4. تنظيف ملفات السجلات
    clean_logs()
    
    # 5. تنظيف Docker
    clean_docker()
    
    # 6. إيقاف العمليات المتوقفة
    kill_zombie_processes()
    
    # 7. تحرير الذاكرة
    free_memory()
    
    # 8. تنظيف ملفات PDF المؤقتة القديمة
    clean_old_pdf_temp()
    
    elapsed_time = time.time() - start_time
    
    # عرض الاستخدام بعد التنظيف
    print(f"\n{'='*70}")
    print("📊 الاستخدام بعد التنظيف:")
    print("-" * 70)
    
    disk = get_disk_usage()
    if disk:
        print("💾 استخدام القرص:")
        print(disk)
    
    memory = get_memory_usage()
    if memory:
        print("\n🧠 استخدام الذاكرة:")
        print(memory)
    
    print(f"\n{'='*70}")
    print(f"✅ اكتملت العملية! (استغرق {elapsed_time:.1f} ثانية)")
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

