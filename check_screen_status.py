#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت للتحقق من حالة الجلسات في screen
يحدد أي جلسات نشطة فعلياً وأيها متوقفة
"""

import subprocess
import re
from typing import List, Dict

def get_active_screens() -> List[str]:
    """الحصول على قائمة الجلسات النشطة في screen"""
    try:
        result = subprocess.run(['screen', '-ls'], capture_output=True, text=True, timeout=5)
        screens = []
        for line in result.stdout.split('\n'):
            if 'book_script_' in line:
                # استخراج اسم الجلسة (مثلاً: 7108.book_script_1)
                match = re.search(r'(\d+)\.(book_script_\d+)', line)
                if match:
                    screens.append(match.group(2))
        return screens
    except Exception as e:
        print(f"❌ خطأ في فحص screen: {e}")
        return []

def check_screen_content(session_name: str) -> Dict:
    """فحص محتوى جلسة screen"""
    try:
        # محاولة قراءة محتوى الجلسة
        result = subprocess.run(
            ['screen', '-S', session_name, '-X', 'hardcopy', '/tmp/screen_check.txt'],
            capture_output=True,
            timeout=5
        )
        
        try:
            with open('/tmp/screen_check.txt', 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # البحث عن علامات
            is_running = False
            has_error = False
            last_lines = content.split('\n')[-10:] if content else []
            
            # البحث عن علامات العمل
            if any('معالجة' in line for line in last_lines):
                is_running = True
            if any('✅' in line for line in last_lines):
                is_running = True
            if any('❌' in line for line in last_lines):
                has_error = True
            if any('خطأ' in line for line in last_lines):
                has_error = True
            if any('Error' in line for line in last_lines):
                has_error = True
            
            return {
                'exists': True,
                'running': is_running,
                'has_error': has_error,
                'last_line': last_lines[-1] if last_lines else 'فارغ'
            }
        except FileNotFoundError:
            return {'exists': False, 'running': False, 'has_error': False, 'last_line': 'غير موجود'}
    except:
        return {'exists': False, 'running': False, 'has_error': False, 'last_line': 'خطأ في الفحص'}

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔍 فحص حالة جلسات Screen")
    print("=" * 70)
    
    # الحصول على الجلسات النشطة
    print("\n📺 جاري فحص الجلسات النشطة...")
    active_screens = get_active_screens()
    print(f"✅ تم العثور على {len(active_screens)} جلسة نشطة")
    
    if not active_screens:
        print("❌ لا توجد جلسات نشطة")
        return
    
    # فحص كل جلسة
    print(f"\n{'='*70}")
    print("📊 تقرير حالة الجلسات:")
    print(f"{'='*70}\n")
    
    running_count = 0
    stopped_count = 0
    error_count = 0
    
    for session_name in sorted(active_screens, key=lambda x: int(x.split('_')[-1])):
        status = check_screen_content(session_name)
        script_num = session_name.split('_')[-1]
        
        if status['exists']:
            if status['running']:
                print(f"✅ الجلسة {script_num:>2} ({session_name}): 🟢 تعمل - {status['last_line'][:60]}")
                running_count += 1
            elif status['has_error']:
                print(f"❌ الجلسة {script_num:>2} ({session_name}): 🔴 خطأ - {status['last_line'][:60]}")
                error_count += 1
            else:
                print(f"⏳ الجلسة {script_num:>2} ({session_name}): 🟡 متوقفة/في الانتظار - {status['last_line'][:60]}")
                stopped_count += 1
        else:
            print(f"❓ الجلسة {script_num:>2} ({session_name}): غير موجودة")
            stopped_count += 1
    
    # الملخص
    print(f"\n{'='*70}")
    print("📊 الملخص:")
    print(f"{'='*70}")
    print(f"🟢 تعمل: {running_count} جلسة")
    print(f"🟡 متوقفة/في الانتظار: {stopped_count} جلسة")
    print(f"🔴 بها أخطاء: {error_count} جلسة")
    print(f"📊 إجمالي: {len(active_screens)} جلسة")
    
    # عرض الجلسات المتوقفة
    if stopped_count > 0:
        print(f"\n{'='*70}")
        print("⏳ الجلسات المتوقفة (قد تحتاج إعادة تشغيل):")
        print(f"{'='*70}")
        for session_name in sorted(active_screens, key=lambda x: int(x.split('_')[-1])):
            status = check_screen_content(session_name)
            script_num = session_name.split('_')[-1]
            if status['exists'] and not status['running'] and not status['has_error']:
                print(f"  - {session_name} (الجلسة {script_num})")
    
    print(f"\n{'='*70}")
    print("✅ اكتمل الفحص!")
    print(f"{'='*70}")
    print("\n💡 نصيحة: إذا كانت الجلسات متوقفة، انتظر 1-2 دقيقة ثم فحص مرة أخرى")
    print("💡 أو استخدم: python restart_failed_screens.py لإعادة تشغيلها")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  تم الإيقاف من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()

