#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإعادة تشغيل الجلسات التي لم تبدأ بعد
"""

import subprocess
import sys
import time
import os

# الجلسات التي لم تبدأ (من التقرير)
FAILED_SCREENS = [
    (2, 151, 191),   # book_script_2
    (3, 192, 232),   # book_script_3
    (4, 233, 273),   # book_script_4
    (7, 356, 396),   # book_script_7
    (8, 397, 436),   # book_script_8
    (18, 797, 836),  # book_script_18
    (20, 877, 916),  # book_script_20
    (22, 957, 996),  # book_script_22
    (24, 1037, 1076), # book_script_24
    (26, 1117, 1156), # book_script_26
    (27, 1157, 1196), # book_script_27
    (28, 1197, 1236), # book_script_28
    (29, 1237, 1276), # book_script_29
    (32, 1357, 1396), # book_script_32
    (34, 1437, 1476), # book_script_34
    (35, 1477, 1516), # book_script_35
    (37, 1557, 1596), # book_script_37
    (38, 1597, 1636), # book_script_38
    (39, 1637, 1676), # book_script_39
    (40, 1677, 1716), # book_script_40
    (41, 1717, 1756), # book_script_41
    (42, 1757, 1796), # book_script_42
    (43, 1797, 1836), # book_script_43
    (44, 1837, 1876), # book_script_44
    (47, 1957, 1996), # book_script_47
    (49, 2037, 2076), # book_script_49
    (50, 2077, 2116), # book_script_50
]

SCRIPT_NAME = "inspect_books_mongodb.py"

def kill_existing_session(session_name: str):
    """إنهاء جلسة موجودة إذا كانت موجودة"""
    try:
        # التحقق من وجود الجلسة
        result = subprocess.run(['screen', '-list'], capture_output=True, text=True)
        if session_name in result.stdout:
            # إنهاء الجلسة
            subprocess.run(['screen', '-X', '-S', session_name, 'quit'], 
                         capture_output=True, timeout=5)
            time.sleep(0.5)
            return True
    except:
        pass
    return False

def create_screen_session(session_name: str, start: int, end: int, script_num: int, total: int):
    """إنشاء جلسة screen جديدة"""
    # إنشاء script مؤقت
    script_content = f"""#!/bin/bash
cd /root/i2pdf
source venv/bin/activate
echo "🚀 السكربت {script_num}/{total}: من الكتاب {start} إلى {end}"
echo "📅 بدء العملية: $(date)"
python {SCRIPT_NAME} << EOF
{start}
{end}
y
EOF
echo "✅ اكتمل السكربت {script_num}/{total}"
echo "📅 انتهاء العملية: $(date)"
"""
    
    # حفظ السكربت المؤقت
    temp_script = f"/tmp/run_script_{script_num}.sh"
    with open(temp_script, 'w') as f:
        f.write(script_content)
    
    # جعل السكربت قابل للتنفيذ
    os.chmod(temp_script, 0o755)
    
    # إنشاء جلسة screen جديدة
    screen_cmd = [
        'screen',
        '-dmS', session_name,
        'bash', temp_script
    ]
    
    try:
        subprocess.run(screen_cmd, check=True, capture_output=True, timeout=10)
        return True
    except Exception as e:
        print(f"❌ فشل إنشاء جلسة {session_name}: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔄 إعادة تشغيل الجلسات التي لم تبدأ")
    print("=" * 70)
    
    total = len(FAILED_SCREENS)
    print(f"\n📊 عدد الجلسات لإعادة التشغيل: {total}")
    
    # عرض الجلسات
    print("\n📋 الجلسات التي سيتم إعادة تشغيلها:")
    for script_num, start, end in FAILED_SCREENS:
        count = end - start + 1
        print(f"   - الجلسة {script_num}: من {start} إلى {end} ({count} كتاب)")
    
    # تأكيد
    print(f"\n{'='*70}")
    confirm = input(f"هل تريد إعادة تشغيل {total} جلسة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        return
    
    # إعادة تشغيل الجلسات
    print(f"\n🔄 بدء إعادة تشغيل {total} جلسة...\n")
    success_count = 0
    fail_count = 0
    
    for i, (script_num, start, end) in enumerate(FAILED_SCREENS, 1):
        session_name = f"book_script_{script_num}"
        print(f"🔄 [{i}/{total}] إعادة تشغيل {session_name} (الكتب {start}-{end})...")
        
        # إنهاء الجلسة القديمة إن وجدت
        if kill_existing_session(session_name):
            print(f"   ⚠️  تم إنهاء الجلسة القديمة")
        
        # إنشاء جلسة جديدة
        if create_screen_session(session_name, start, end, script_num, total):
            print(f"   ✅ تم إنشاء الجلسة بنجاح")
            success_count += 1
        else:
            print(f"   ❌ فشل إنشاء الجلسة")
            fail_count += 1
        
        time.sleep(0.3)  # تأخير قصير
    
    # الملخص
    print(f"\n{'='*70}")
    print("📊 الملخص:")
    print(f"{'='*70}")
    print(f"✅ نجح: {success_count} جلسة")
    print(f"❌ فشل: {fail_count} جلسة")
    print(f"📊 إجمالي: {total} جلسة")
    
    print(f"\n{'='*70}")
    print("✅ اكتملت العملية!")
    print(f"{'='*70}")
    print("\n💡 يمكنك فحص التقدم باستخدام:")
    print("   python check_screens_progress.py")
    print("   screen -ls")

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

