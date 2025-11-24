#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإنهاء جميع جلسات screen
"""

import subprocess
import re
import sys

def get_all_screens() -> list:
    """الحصول على قائمة جميع جلسات screen"""
    try:
        result = subprocess.run(['screen', '-ls'], capture_output=True, text=True, timeout=5)
        screens = []
        for line in result.stdout.split('\n'):
            if 'book_script_' in line or 'Detached' in line or 'Attached' in line:
                # استخراج اسم الجلسة (مثلاً: 7108.book_script_1)
                match = re.search(r'(\d+)\.(book_script_\d+)', line)
                if match:
                    screens.append(match.group(2))
        return screens
    except Exception as e:
        print(f"❌ خطأ في فحص screen: {e}")
        return []

def kill_screen(session_name: str) -> bool:
    """إنهاء جلسة screen واحدة"""
    try:
        subprocess.run(
            ['screen', '-X', '-S', session_name, 'quit'],
            capture_output=True,
            timeout=5,
            check=True
        )
        return True
    except:
        return False

def kill_all_screens():
    """إنهاء جميع جلسات screen"""
    try:
        # محاولة إنهاء جميع الجلسات دفعة واحدة
        result = subprocess.run(['screen', '-X', 'quit'], capture_output=True, timeout=5)
        return True
    except:
        return False

def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🛑 إنهاء جميع جلسات Screen")
    print("=" * 70)
    
    # الحصول على الجلسات النشطة
    print("\n📺 جاري فحص الجلسات النشطة...")
    screens = get_all_screens()
    
    if not screens:
        print("✅ لا توجد جلسات screen نشطة")
        return
    
    print(f"✅ تم العثور على {len(screens)} جلسة نشطة")
    print(f"\n📋 الجلسات:")
    for screen in sorted(screens, key=lambda x: int(x.split('_')[-1])):
        print(f"   - {screen}")
    
    # تأكيد
    print(f"\n{'='*70}")
    print(f"⚠️  سيتم إنهاء {len(screens)} جلسة screen")
    print(f"{'='*70}")
    confirm = input(f"\nهل تريد المتابعة؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        return
    
    # إنهاء جميع الجلسات
    print(f"\n🛑 جاري إنهاء جميع الجلسات...")
    
    # محاولة إنهاء جميع الجلسات دفعة واحدة
    if kill_all_screens():
        print("✅ تم إنهاء جميع الجلسات")
    else:
        # إنهاء كل جلسة على حدة
        print("🔄 جاري إنهاء الجلسات واحدة تلو الأخرى...")
        killed = 0
        failed = 0
        
        for screen in screens:
            if kill_screen(screen):
                print(f"   ✅ تم إنهاء {screen}")
                killed += 1
            else:
                print(f"   ❌ فشل إنهاء {screen}")
                failed += 1
        
        print(f"\n📊 الملخص:")
        print(f"   ✅ تم إنهاء: {killed} جلسة")
        if failed > 0:
            print(f"   ❌ فشل: {failed} جلسة")
    
    # التحقق النهائي
    print(f"\n🔍 التحقق من الجلسات المتبقية...")
    remaining = get_all_screens()
    if remaining:
        print(f"⚠️  لا تزال هناك {len(remaining)} جلسة نشطة:")
        for screen in remaining:
            print(f"   - {screen}")
        print("\n💡 يمكنك محاولة إنهائها يدوياً:")
        print("   screen -X -S <session_name> quit")
    else:
        print("✅ تم إنهاء جميع الجلسات بنجاح!")
    
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

