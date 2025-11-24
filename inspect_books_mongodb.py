#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت فحص الكتب وحفظها مباشرة في MongoDB
يقوم بفحص الكتب من ملف JSON ويحفظها مباشرة في MongoDB أثناء الفحص
"""

import json
import os
import sys
import tempfile
import requests
import re
import subprocess
import time
import platform
import signal
import warnings
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

# قمع تحذيرات PyPDF2 حول التعريفات المكررة
warnings.filterwarnings("ignore", message=".*Multiple definitions in dictionary.*")
warnings.filterwarnings("ignore", category=UserWarning, module="PyPDF2")

# استيراد PyPDF2
try:
    import PyPDF2
except ImportError:
    print("خطأ: يجب تثبيت PyPDF2 أولاً")
    print("قم بتشغيل: pip install PyPDF2")
    sys.exit(1)

# استيراد pymongo
try:
    from pymongo import MongoClient
    from pymongo.errors import DuplicateKeyError, ConnectionFailure
except ImportError:
    print("خطأ: يجب تثبيت pymongo أولاً")
    print("قم بتشغيل: pip install pymongo")
    sys.exit(1)

# استيراد من i2pdf (النظام الأساسي)
from i2pdf import (
    _run_ocr_sidecar,
    _pdftotext_layout,
    _arabic_ratio,
)

# إصلاح مشكلة الترميز في Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# تعريف المجلد المؤقت (TMP_ROOT غير موجود في i2pdf.py بعد git reset)
TMP_ROOT = os.path.join(tempfile.gettempdir(), "i2pdf_temp")
# التأكد من وجود المجلد المؤقت
os.makedirs(TMP_ROOT, exist_ok=True)

# إعدادات MongoDB
MONGO_URI = "mongodb+srv://vall:VVVVvvvv24@cluster0.rzpzrnn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "test"
COLLECTION_NAME = "book_summaries"


# ============================================================================
# دوال مساعدة (مستقلة - لا تعتمد على inspect_books.py)
# ============================================================================

def fix_arabic_text(text: str) -> str:
    """
    تصحيح النص العربي المعكوس
    يقوم بعكس النص العربي بالكامل لأن OCR يخرجه معكوساً أحياناً
    
    Args:
        text: النص المراد تصحيحه
        
    Returns:
        النص المصحح
    """
    if not text:
        return text
    
    # التحقق من وجود نص عربي
    arabic_pattern = re.compile(r'[\u0600-\u06FF]+')
    if not arabic_pattern.search(text):
        return text  # لا يوجد نص عربي، إرجاع النص كما هو
    
    # تقسيم النص إلى أسطر
    lines = text.split('\n')
    fixed_lines = []
    
    for line in lines:
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # عكس السطر بالكامل (لأن OCR يخرجه معكوساً)
        # نحافظ على المسافات والأرقام في أماكنها
        fixed_line = line[::-1]
        fixed_lines.append(fixed_line)
    
    # إعادة تجميع النص
    return '\n'.join(fixed_lines)


def detect_language_from_pdf_name(pdf_name: str) -> str:
    """
    تحديد اللغة بناءً على اسم ملف PDF
    
    القواعد:
    - إذا كان اسم الملف يحتوي على "--" (شرطتان متتاليتان) في أي مكان = فرنسي (fra)
    - خلاف ذلك = عربي (ara)
    
    أمثلة:
    - "--1463.pdf" = فرنسي
    - "778--.pdf" = فرنسي
    - "-1463.pdf" = عربي
    - "1463.pdf" = عربي
    
    Args:
        pdf_name: اسم ملف PDF (مثلاً: "-1463.pdf" أو "--1463.pdf" أو "778--.pdf")
        
    Returns:
        كود اللغة: "ara" للعربية أو "fra" للفرنسية
    """
    if not pdf_name:
        return "ara"  # افتراضي: عربي
    
    # إزالة الامتداد
    name_without_ext = pdf_name.replace(".pdf", "").strip()
    
    # التحقق من وجود "--" (شرطتان متتاليتان) في أي مكان في الاسم
    if "--" in name_without_ext:
        # يحتوي على شرطتين = فرنسي
        return "fra"
    else:
        # لا يحتوي على شرطتين = عربي
        return "ara"


def download_pdf(url: str, output_path: str, timeout: int = 300) -> bool:
    """
    تحميل ملف PDF من رابط URL
    
    Args:
        url: رابط PDF
        output_path: مسار حفظ الملف
        timeout: مهلة التحميل بالثواني
        
    Returns:
        True إذا نجح التحميل، False خلاف ذلك
    """
    try:
        print(f"  ⬇️  جاري تحميل PDF من: {url[:80]}...")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # بالميجابايت
        print(f"  ✅ تم التحميل بنجاح ({file_size:.2f} MB)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ❌ فشل التحميل: {e}")
        return False
    except Exception as e:
        print(f"  ❌ خطأ غير متوقع: {e}")
        return False


def kill_ocr_processes():
    """
    إنهاء جميع عمليات OCR المتعطلة (tesseract, ocrmypdf)
    """
    try:
        system = platform.system()
        if system == "Windows":
            # Windows: استخدام taskkill
            processes = ["tesseract.exe", "ocrmypdf.exe"]
            for proc_name in processes:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/IM", proc_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                except:
                    pass
        else:
            # Linux/Mac: استخدام pkill
            processes = ["tesseract", "ocrmypdf"]
            for proc_name in processes:
                try:
                    subprocess.run(
                        ["pkill", "-9", proc_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                except:
                    pass
        time.sleep(1)  # انتظار قصير للتأكد من إنهاء العمليات
    except Exception as e:
        print(f"  ⚠️  تحذير: فشل في تنظيف عمليات OCR: {e}")


def reset_ocr_if_needed():
    """
    إعادة تشغيل OCR إذا لزم الأمر (تنظيف وقائي)
    """
    print(f"  🔄 تنظيف وقائي لعمليات OCR...")
    kill_ocr_processes()
    time.sleep(1)


def extract_pdf_with_ocr_only(pdf_path: str, lang: str = "ara") -> Dict[str, Any]:
    """
    استخراج النص من PDF باستخدام OCR فقط (لا يستخدم الطبقة النصية)
    يستخدم نفس منطق pdf_best_cmd من i2pdf.py
    
    Args:
        pdf_path: مسار ملف PDF (يجب أن يكون مطلق)
        lang: اللغة (افتراضي: ara)
        
    Returns:
        بيانات الاستخراج في نفس تنسيق extract_pdf_summary:
        {
            "number_of_pages": int,
            "language": str,
            "used_ocr": bool,
            "pages": [{"content": str, "page_number": int}, ...],
            "book_name": str
        }
    """
    # التأكد من أن المسار مطلق
    pdf_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"الملف غير موجود: {pdf_path}")
    
    # الحصول على عدد الصفحات
    num_pages = 0
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="PyPDF2")
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
    except Exception as e:
        print(f"  ⚠️  تحذير: فشل قراءة عدد الصفحات: {e}")
        num_pages = 0
    
    # استخراج النص باستخدام OCR فقط
    candidates = []
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # pass A: primary lang
            sidecar_a = os.path.join(tmpdir, f"{base}.a.txt")
            ocr_a_pdf = os.path.join(tmpdir, f"{base}.a.pdf")
            layout_a = None
            ocr_success_a = False
            
            try:
                _run_ocr_sidecar(pdf_path, sidecar_a, ocr_a_pdf, lang=lang)
                ocr_success_a = True
                # layout from pass A
                if os.path.exists(ocr_a_pdf):
                    layout_a = os.path.join(tmpdir, f"{base}.a.layout.txt")
                    _pdftotext_layout(ocr_a_pdf, layout_a)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"  ⚠️  OCR pass A failed: {e}")
            
            # pass B: lang + eng
            sidecar_b = os.path.join(tmpdir, f"{base}.b.txt")
            ocr_b_pdf = os.path.join(tmpdir, f"{base}.b.pdf")
            layout_b = None
            ocr_success_b = False
            lang_b = f"{lang}+eng" if "eng" not in lang else lang
            
            try:
                _run_ocr_sidecar(pdf_path, sidecar_b, ocr_b_pdf, lang=lang_b)
                ocr_success_b = True
                # layout from pass B
                if os.path.exists(ocr_b_pdf):
                    layout_b = os.path.join(tmpdir, f"{base}.b.layout.txt")
                    _pdftotext_layout(ocr_b_pdf, layout_b)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"  ⚠️  OCR pass B failed: {e}")
            
            # collect candidates
            candidate_paths = [
                (sidecar_a, "ocr-sidecar-a"),
                (sidecar_b, "ocr-sidecar-b"),
            ]
            if layout_a:
                candidate_paths.append((layout_a, "ocr-layout-a"))
            if layout_b:
                candidate_paths.append((layout_b, "ocr-layout-b"))
            
            for path, source in candidate_paths:
                if os.path.exists(path):
                    try:
                        txt = open(path, encoding="utf-8").read()
                        if txt.strip():  # Only add non-empty text
                            candidates.append((txt, {
                                "source": source,
                                "length": len(txt),
                                "arabic_ratio": round(_arabic_ratio(txt), 4)
                            }))
                    except Exception as e:
                        print(f"  ⚠️  فشل قراءة {source}: {e}")
    
    except Exception as e:
        print(f"  ⚠️  فشل عملية OCR: {e}")
    
    # اختيار أفضل مرشح
    if not candidates:
        raise RuntimeError("OCR failed completely. No text could be extracted. Please ensure Tesseract OCR with Arabic language data is installed.")
    
    # select best: highest arabic_ratio, then longer length
    best_text, best_metrics = sorted(
        candidates,
        key=lambda x: (x[1]["arabic_ratio"], x[1]["length"])
    )[-1]
    
    print(f"  ✅ تم اختيار أفضل مرشح: {best_metrics['source']} (نسبة العربية: {best_metrics['arabic_ratio']:.4f})")
    
    # OCR يخرج النص بشكل صحيح، لا حاجة لعكسه
    # تقسيم النص إلى صفحات (تقريبي - كل 3000 حرف = صفحة)
    pages = []
    if num_pages > 0:
        chars_per_page = max(1, len(best_text) // num_pages) if num_pages > 0 else len(best_text)
        for i in range(num_pages):
            start_idx = i * chars_per_page
            end_idx = (i + 1) * chars_per_page if i < num_pages - 1 else len(best_text)
            page_text = best_text[start_idx:end_idx]
            pages.append({
                "content": page_text,
                "page_number": i + 1
            })
    else:
        # إذا لم نتمكن من تحديد عدد الصفحات، نضع كل النص في صفحة واحدة
        pages.append({
            "content": best_text,
            "page_number": 1
        })
    
    return {
        "number_of_pages": num_pages if num_pages > 0 else len(pages),
        "language": lang,
        "used_ocr": True,  # دائماً OCR
        "pages": pages,
        "book_name": base
    }


def get_mongodb_collection():
    """
    الاتصال بـ MongoDB وإرجاع المجموعة (Collection)
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # اختبار الاتصال
        client.admin.command('ping')
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # ملاحظة: _id فريد تلقائياً في MongoDB، لا حاجة لإنشاء فهرس
        
        print("✅ تم الاتصال بـ MongoDB بنجاح")
        return collection, client
    except ConnectionFailure as e:
        print(f"❌ فشل الاتصال بـ MongoDB: {e}")
        print("تأكد من:")
        print("  1. الاتصال بالإنترنت")
        print("  2. صحة رابط الاتصال")
        print("  3. أن IP الخاص بك مسموح في MongoDB Atlas")
        sys.exit(1)
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        sys.exit(1)


def save_book_to_mongodb(collection, book_data: Dict[str, Any]) -> bool:
    """
    حفظ كتاب واحد في MongoDB
    
    Args:
        collection: مجموعة MongoDB
        book_data: بيانات الكتاب
        
    Returns:
        True إذا نجح الحفظ، False إذا فشل
    """
    try:
        # تنظيف البيانات
        processed_at = book_data.get("processed_at", datetime.now(timezone.utc))
        # إذا كان string، نحوله إلى datetime
        if isinstance(processed_at, str):
            try:
                processed_at = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
            except:
                processed_at = datetime.now(timezone.utc)
        
        cleaned_data = {
            "_id": str(book_data.get("_id", "")),
            "title": book_data.get("title", ""),
            "pdfName": book_data.get("pdfName", ""),
            "pdfLink": book_data.get("pdfLink", ""),
            "book_name": book_data.get("book_name", ""),
            "url": book_data.get("url", book_data.get("pdfLink", "")),
            "number_of_pages": int(book_data.get("number_of_pages", 0)),
            "language": book_data.get("language", "ara"),
            "used_ocr": bool(book_data.get("used_ocr", False)),
            "pages": book_data.get("pages", []),
            "processed_at": processed_at
        }
        
        # حفظ أو تحديث (upsert)
        collection.update_one(
            {"_id": cleaned_data["_id"]},
            {"$set": cleaned_data},
            upsert=True
        )
        return True
    except DuplicateKeyError:
        # الكتاب موجود بالفعل، تحديثه
        try:
            collection.update_one(
                {"_id": cleaned_data["_id"]},
                {"$set": cleaned_data}
            )
            return True
        except Exception as e:
            print(f"  ⚠️  فشل تحديث الكتاب في MongoDB: {e}")
            return False
    except Exception as e:
        print(f"  ⚠️  فشل حفظ الكتاب في MongoDB: {e}")
        return False


def process_book_with_mongodb(book: Dict[str, Any], index: int, total: int, 
                               collection, auto_detect_lang: bool = True) -> Dict[str, Any] | None:
    """
    معالجة كتاب واحد وحفظه مباشرة في MongoDB
    
    Args:
        book: بيانات الكتاب من JSON
        index: رقم الفهرس الحالي
        total: العدد الإجمالي
        collection: مجموعة MongoDB
        auto_detect_lang: تحديد اللغة تلقائياً من اسم الملف
        
    Returns:
        بيانات الكتاب مع المحتوى المستخرج أو None في حالة الفشل
    """
    book_id = book.get("_id", "")
    title = book.get("title", "بدون عنوان")
    pdf_link = book.get("pdfLink", "")
    pdf_name = book.get("pdfName", "").strip()
    
    # إصلاح خطأ إملائي في الرابط (ammazonaws -> amazonaws)
    if pdf_link and "ammazonaws.com" in pdf_link:
        pdf_link = pdf_link.replace("ammazonaws.com", "amazonaws.com")
        print(f"  🔧 تم إصلاح خطأ إملائي في الرابط")
    
    # التحقق من صحة اسم الملف
    if not pdf_name or pdf_name == ".pdf" or not pdf_name.endswith(".pdf"):
        # محاولة استخراج اسم الملف من الرابط
        if pdf_link:
            pdf_name = os.path.basename(pdf_link).split("?")[0]  # إزالة query parameters
            if not pdf_name or not pdf_name.endswith(".pdf"):
                pdf_name = f"book_{book_id}.pdf"
        else:
            pdf_name = f"book_{book_id}.pdf"
    
    print(f"\n[{index + 1}/{total}] معالجة الكتاب: {title[:60]}...")
    print(f"  📄 ID: {book_id}")
    print(f"  📁 اسم الملف: {pdf_name}")
    
    if not pdf_link:
        print(f"  ⚠️  لا يوجد رابط PDF لهذا الكتاب")
        return None
    
    # تحديد اللغة تلقائياً من اسم الملف
    if auto_detect_lang:
        lang = detect_language_from_pdf_name(pdf_name)
        lang_name = "عربي" if lang == "ara" else "فرنسي"
        print(f"  🌐 اللغة المكتشفة: {lang_name} ({lang})")
    else:
        lang = "ara"  # افتراضي
    
    # إنشاء ملف مؤقت للPDF (تنظيف اسم الملف)
    safe_pdf_name = os.path.basename(pdf_name).replace(" ", "_").replace("/", "_").replace("\\", "_")
    temp_pdf = os.path.join(TMP_ROOT, f"temp_{book_id}_{safe_pdf_name}")
    
    try:
        # تحميل PDF
        if not download_pdf(pdf_link, temp_pdf):
            return None
        
        # التحقق من وجود الملف بعد التحميل
        if not os.path.exists(temp_pdf):
            print(f"  ❌ فشل التحميل: الملف غير موجود بعد التحميل")
            return None
        
        # التحقق من حجم الملف
        file_size = os.path.getsize(temp_pdf)
        if file_size == 0:
            print(f"  ❌ الملف المحمل فارغ (0 bytes)")
            return None
        
        # التحقق مرة أخرى من وجود الملف قبل الاستخراج
        if not os.path.exists(temp_pdf):
            print(f"  ❌ الملف غير موجود قبل الاستخراج: {temp_pdf}")
            return None
        
        # نسخ الملف إلى موقع آمن (حماية من الحذف العرضي)
        import shutil
        safe_pdf_path = temp_pdf + ".safe"
        pdf_to_use = temp_pdf  # استخدام الملف الأصلي مباشرة
        
        # التحقق من وجود الملف قبل الاستخراج
        if not os.path.exists(pdf_to_use):
            print(f"  ❌ الملف غير موجود قبل الاستخراج: {pdf_to_use}")
            return None
        
        # التحقق من أن الملف قابل للقراءة
        if not os.access(pdf_to_use, os.R_OK):
            print(f"  ❌ الملف غير قابل للقراءة: {pdf_to_use}")
            return None
        
        # التأكد من أن المسار مطلق
        pdf_to_use_abs = os.path.abspath(pdf_to_use)
        
        # التحقق مرة أخرى من وجود الملف
        if not os.path.exists(pdf_to_use_abs):
            print(f"  ❌ الملف غير موجود بعد تحويل المسار: {pdf_to_use_abs}")
            return None
        
        # استخراج النص من PDF باستخدام OCR فقط (لا يستخدم الطبقة النصية)
        print(f"  🔍 جاري استخراج النص باستخدام OCR فقط (الفحص الضوئي)...")
        print(f"  📂 مسار الملف: {pdf_to_use_abs}")
        print(f"  📏 حجم الملف: {os.path.getsize(pdf_to_use_abs) / (1024*1024):.2f} MB")
        
        try:
            # استخدام extract_pdf_with_ocr_only (يستخدم OCR فقط - لا يستخدم الطبقة النصية)
            extraction_data = extract_pdf_with_ocr_only(
                pdf_path=pdf_to_use_abs,
                lang=lang,
            )
        except (FileNotFoundError, OSError) as file_error:
            # خطأ في الملف نفسه
            print(f"  ❌ خطأ في الملف: {file_error}")
            print(f"  📂 التحقق من وجود الملف: {pdf_to_use_abs}")
            if pdf_to_use_abs and os.path.exists(pdf_to_use_abs):
                print(f"  📏 حجم الملف: {os.path.getsize(pdf_to_use_abs)} bytes")
            else:
                print(f"  ❌ الملف غير موجود. قد يكون تم حذفه أو الرابط غير صحيح.")
            return None
        except (subprocess.CalledProcessError, RuntimeError) as ocr_error:
            # فشل OCR
            print(f"  ❌ فشل OCR: {ocr_error}")
            print(f"  💡 تأكد من تثبيت Tesseract OCR مع بيانات اللغة العربية")
            return None
        except Exception as e:
            print(f"  ❌ خطأ غير متوقع في استخراج النص: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # OCR يخرج النص بشكل صحيح، لا حاجة لعكسه
        pages = extraction_data.get("pages", [])
        book_name = extraction_data.get("book_name", title)
        
        # بناء البيانات النهائية (نفس تنسيق النظام القديم)
        result = {
            "_id": book_id,
            "title": title,
            "pdfName": pdf_name,
            "pdfLink": pdf_link,
            "book_name": book_name,
            "url": pdf_link,
            "number_of_pages": extraction_data.get("number_of_pages", 0),
            "language": extraction_data.get("language", lang),
            "used_ocr": extraction_data.get("used_ocr", False),
            "pages": pages,
            "processed_at": datetime.now(timezone.utc).isoformat(),  # نفس تنسيق النظام القديم
        }
        
        # حفظ مباشرة في MongoDB
        print(f"  💾 جاري حفظ الكتاب في MongoDB...")
        if save_book_to_mongodb(collection, result):
            print(f"  ✅ تم الاستخراج والحفظ بنجاح ({result['number_of_pages']} صفحة)")
        else:
            print(f"  ⚠️  تم الاستخراج بنجاح لكن فشل الحفظ في MongoDB ({result['number_of_pages']} صفحة)")
        
        return result
        
    except Exception as e:
        print(f"  ❌ خطأ في معالجة الكتاب: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # حذف الملف المؤقت فقط (لا حاجة للنسخة الآمنة)
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except:
                pass


def main():
    """الدالة الرئيسية"""
    print("=" * 70)
    print("🔍 سكريبت فحص الكتب وحفظها في MongoDB")
    print("=" * 70)
    
    # الاتصال بـ MongoDB
    print("\n📡 جاري الاتصال بـ MongoDB...")
    collection, client = get_mongodb_collection()
    
    # قراءة ملف الكتب
    books_file = "books-2025-11-09T23-13-42-652Z.json"
    if not os.path.exists(books_file):
        print(f"❌ الملف غير موجود: {books_file}")
        sys.exit(1)
    
    print(f"\n📚 جاري قراءة ملف الكتب: {books_file}")
    try:
        with open(books_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        sys.exit(1)
    
    books = data.get("books", [])
    if not books:
        print("❌ لم يتم العثور على كتب في الملف")
        sys.exit(1)
    
    total_books = len(books)
    print(f"✅ تم العثور على {total_books} كتاب")
    
    # تحديد النطاق
    print("\n" + "=" * 70)
    print("📋 حدد نطاق الكتب التي تريد فحصها:")
    print("=" * 70)
    
    try:
        start_input = input(f"من الكتاب رقم (1-{total_books}): ").strip()
        end_input = input(f"إلى الكتاب رقم (1-{total_books}): ").strip()
        
        start_idx = int(start_input) - 1
        end_idx = int(end_input)
        
        if start_idx < 0 or start_idx >= total_books:
            print("❌ رقم البداية غير صحيح")
            sys.exit(1)
        if end_idx < 1 or end_idx > total_books:
            print("❌ رقم النهاية غير صحيح")
            sys.exit(1)
        if start_idx >= end_idx:
            print("❌ رقم البداية يجب أن يكون أقل من رقم النهاية")
            sys.exit(1)
        
        selected_books = books[start_idx:end_idx]
        count = len(selected_books)
        
    except ValueError:
        print("❌ يرجى إدخال أرقام صحيحة")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ تم الإلغاء من قبل المستخدم")
        sys.exit(1)
    
    print(f"\n✅ سيتم فحص {count} كتاب (من {start_idx + 1} إلى {end_idx})")
    print("ℹ️  سيتم تحديد اللغة تلقائياً من اسم ملف PDF")
    print("ℹ️  سيتم حفظ الكتب مباشرة في MongoDB أثناء الفحص")
    
    # تأكيد البدء
    print("\n" + "=" * 70)
    confirm = input("هل تريد البدء في الفحص؟ (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 'نعم', 'ن']:
        print("❌ تم الإلغاء")
        client.close()
        sys.exit(0)
    
    # معالجة الكتب
    print("\n" + "=" * 70)
    print("🚀 بدء عملية الفحص والحفظ...")
    print("=" * 70)
    
    # تنظيف أي عمليات OCR متعطلة في البداية
    print("🧹 تنظيف عمليات OCR المتعطلة...")
    kill_ocr_processes()
    time.sleep(1)
    
    success_count = 0
    fail_count = 0
    saved_count = 0
    
    try:
        for idx, book in enumerate(selected_books):
            result = process_book_with_mongodb(book, idx, count, collection, auto_detect_lang=True)
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
    print(f"   📄 إجمالي: {count}")
    
    print("\n" + "=" * 70)
    print("✅ اكتملت العملية!")
    print("=" * 70)
    print(f"\n📝 يمكنك التحقق من البيانات في MongoDB:")
    print(f"   - قاعدة البيانات: {DB_NAME}")
    print(f"   - المجموعة: {COLLECTION_NAME}")


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

