#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للعثور على الملفات الكبيرة التي تستهلك مساحة القرص
"""

import subprocess
import os
import sys

def find_large_files(directory="/", min_size_mb=10, top_n=30):
    """
    البحث عن الملفات الكبيرة
    
    Args:
        directory: المجلد للبحث فيه
        min_size_mb: الحد الأدنى للحجم بالميجابايت
        top_n: عدد الملفات الكبيرة للعرض
    """
    print(f"🔍 البحث عن الملفات الأكبر من {min_size_mb} MB في {directory}...")
    
    try:
        # استخدام find مع du للعثور على الملفات الكبيرة
        cmd = [
            'find', directory,
            '-type', 'f',
            '-size', f'+{min_size_mb}M',
            '-exec', 'du', '-h', '{}', '+',
            '2>/dev/null'
        ]
        
        result = subprocess.run(
            ' '.join(cmd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            # ترتيب حسب الحجم
            files_with_sizes = []
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) == 2:
                        size, path = parts
                        try:
                            # تحويل الحجم إلى ميجابايت للترتيب
                            size_mb = parse_size_to_mb(size)
                            files_with_sizes.append((size_mb, size, path))
                        except:
                            pass
            
            # ترتيب تنازلي
            files_with_sizes.sort(reverse=True)
            
            print(f"\n📊 أكبر {min(top_n, len(files_with_sizes))} ملف:\n")
            print(f"{'الحجم':<12} {'المسار'}")
            print("-" * 70)
            
            for size_mb, size, path in files_with_sizes[:top_n]:
                print(f"{size:<12} {path}")
            
            total_size = sum(size_mb for size_mb, _, _ in files_with_sizes)
            print(f"\n📊 إجمالي حجم الملفات الكبيرة: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
            
            return files_with_sizes
        else:
            print("❌ لم يتم العثور على ملفات كبيرة")
            return []
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []

def parse_size_to_mb(size_str):
    """تحويل حجم من string إلى ميجابايت"""
    size_str = size_str.strip().upper()
    if size_str.endswith('K'):
        return float(size_str[:-1]) / 1024
    elif size_str.endswith('M'):
        return float(size_str[:-1])
    elif size_str.endswith('G'):
        return float(size_str[:-1]) * 1024
    elif size_str.endswith('T'):
        return float(size_str[:-1]) * 1024 * 1024
    else:
        # بايت
        return float(size_str) / (1024 * 1024)

def find_large_directories(directory="/root", top_n=10):
    """البحث عن المجلدات الكبيرة"""
    print(f"\n🔍 البحث عن المجلدات الكبيرة في {directory}...")
    
    try:
        cmd = [
            'du', '-h', '--max-depth=1', directory,
            '2>/dev/null', '|', 'sort', '-hr', '|', 'head', '-n', str(top_n + 1)
        ]
        
        result = subprocess.run(
            ' '.join(cmd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            print(f"\n📊 أكبر {top_n} مجلد:\n")
            print(f"{'الحجم':<12} {'المسار'}")
            print("-" * 70)
            lines = result.stdout.strip().split('\n')
            for line in lines[1:top_n+1]:  # تخطي السطر الأول (المجلد نفسه)
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        size = parts[0]
                        path = parts[-1]
                        print(f"{size:<12} {path}")
    except Exception as e:
        print(f"⚠️  خطأ في البحث عن المجلدات: {e}")

def get_disk_usage():
    """عرض استخدام القرص"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        return result.stdout
    except:
        return None

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔍 البحث عن الملفات الكبيرة")
    print("=" * 70)
    
    # عرض استخدام القرص
    print("\n📊 استخدام القرص الحالي:")
    disk = get_disk_usage()
    if disk:
        print(disk)
    
    # البحث عن الملفات الكبيرة في مجلدات محددة
    print("\n" + "=" * 70)
    search_dirs = ["/tmp", "/root", "/var", "/usr"]
    all_large_files = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            print(f"\n🔍 البحث في {search_dir}...")
            files = find_large_files(search_dir, min_size_mb=10, top_n=30)
            all_large_files.extend(files)
    
    # عرض أكبر الملفات من جميع المجلدات
    if all_large_files:
        all_large_files.sort(reverse=True)
        print(f"\n{'='*70}")
        print(f"📊 أكبر {min(20, len(all_large_files))} ملف من جميع المجلدات:\n")
        print(f"{'الحجم':<12} {'المسار'}")
        print("-" * 70)
        for size_mb, size, path in all_large_files[:20]:
            print(f"{size:<12} {path}")
    
    # البحث عن المجلدات الكبيرة
    find_large_directories("/root", top_n=10)
    
    # نصائح
    print(f"\n{'='*70}")
    print("💡 نصائح لتحرير المساحة:")
    print(f"{'='*70}")
    print("  1. حذف ملفات Docker القديمة:")
    print("     docker system prune -a --volumes")
    print("  2. حذف ملفات PDF المؤقتة:")
    print("     rm -rf /tmp/i2pdf_temp/*")
    print("  3. حذف ملفات log:")
    print("     journalctl --vacuum-time=7d")
    print("  4. تنظيف apt:")
    print("     apt autoremove && apt autoclean")
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

