# Standard
import datetime
import os
import platform
import subprocess
import sys
import tempfile
import json
import re

from typing import Optional

# Pip
import typer
import yaml

from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from yaml.scanner import ScannerError
from yaml.loader import SafeLoader
from pdf2docx import Converter

# Custom
from auxiliary.message_keys import MessageKeys as Mk
from auxiliary.file_explorer import FileExplorer

# Typer app
app = typer.Typer(no_args_is_help=True)

# Files
current_dir = os.getcwd()
files = FileExplorer(home_dir=current_dir)

# Message keys
generate = Mk.GeneratePdf
add_meta = Mk.AddMetadata
gen_dir = Mk.GenerateDir
pdf_docx = Mk.PdfToDocx
pdf_text = Mk.PdfToText
pdf_verify = Mk.PdfVerify
pdf_best = Mk.PdfBest

# Mac and Windows use different slashes.
system: str = platform.system()
if system == "Darwin":
    slash = "/"
elif system == "Windows":
    slash = "\\"

now = datetime.datetime.now()
timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")


@app.command(name=gen_dir.generate_dir, help=gen_dir.generate_dir_help)
def generate_directories() -> None:
    """
    Generating directories wherein the files that should be combined
    are to reside.

        example:
        python main_app.py gen-dir
    :return:
        None
    """
    try:
        typer.echo(gen_dir.generating_dir)
        [
            os.makedirs(folder_dir)
            for folder_dir in ["config", "images", "pdfs", "results"]
        ]
        typer.echo(gen_dir.directory_generated)
    except FileExistsError:
        typer.echo(gen_dir.folders_exists)


@app.command(name=generate.generate_pdf_name,
             help=generate.generate_pdf_command)
def generate_pdf(
    dir_name: Optional[str] = typer.Option(
        current_dir,
        generate.generate_custom_dir_long,
        generate.generate_custom_dir_short,
        help=generate.generate_pdf_help,
    ),
    save_name: Optional[str] = typer.Option(
        f"generated_{timestamp}",
        generate.generated_file_name_long,
        generate.generated_file_name_short,
        help=generate.generate_pdf_help,
    ),
) -> None:
    """
    Description:
         Images gathered from the images directory are combined into a single
        .pdf file that is then placed in the pdfs directory. Using the PIL
        library, .jpg, .gif, .png and .tga are supported.
    Example:
        python main_app.py gen-pdf

    :arg:
         save_name: str the name of the .pdf file being saved.

    :returns
        no returns
    """

    if dir_name != "images":
        image_dir = dir_name
    else:
        image_dir: str = files.get_folders().get("images", current_dir)

    path_exist: bool = os.path.exists(image_dir)

    if not path_exist:
        raise SystemExit(typer.echo(generate.missing_directory))

    image_collection: list = []
    image_path_names: list = []
    valid_images: list = [".jpg", ".jpeg", ".gif", ".png", ".tga"]
    for file_name in sorted(os.listdir(image_dir)):

        ext: str = os.path.splitext(file_name)[1]
        if ext.lower() not in valid_images:
            continue

        img: str = os.path.join(image_dir, file_name)
        image_path_names.append(img)
        image_collection.append(Image.open(img))

    if image_collection:
        first_image = image_collection[0]
        folders = files.get_folders()

        if not image_dir:
            generated_pdf: str = rf"{folders.get('pdfs')}{slash}{save_name}.pdf"
        else:
            generated_pdf: str = rf"{image_dir}{slash}{save_name}.pdf"

        # .pdf generation
        typer.echo(generate.images_generate)
        first_image.save(generated_pdf, save_all=True,
                         append_images=image_collection[1:])
        typer.echo(generate.file_created)

        # Deleting images from directory
        answer = typer.prompt("Delete files ?: yes/y ")
        confirmation = ("y", "yes")

        if answer.lower() in confirmation:
            for image in image_path_names:
                os.remove(image)
            typer.echo(generate.images_removed)
        else:
            typer.echo(generate.retain_images)
    else:
        dir_echo_name = typer.style(dir_name, fg=typer.colors.BRIGHT_YELLOW)
        typer.echo(f"{generate.no_images} '{dir_echo_name}'")


@app.command(name=add_meta.add_metadata_name, help=add_meta.add_metadata_help)
def add_metadata(
    pdf_name: str = typer.Argument("", help=add_meta.meta_pdf),
    config_name: str = typer.Argument("", help=add_meta.yaml_config),
    save_name: str = typer.Argument(add_meta.results, help=add_meta.save_name),
) -> None:
    """
    description:
        the data from the .yaml file is added to the respective .pdf file
        as metadata

    example:
        python main_app.py add-metadata gen.pdf test.yaml

    :arg:
        pdf_name: str is the name of the .pdf which should have metadata added
        to it

        config_name: str is the name of the .yaml file which contains the
        metadata.

    :returns
        None
    """

    # Loading .pdf file
    try:
        pdf: str = files.get_files("pdfs").get(pdf_name)
        pdf_in = open(pdf, "rb")
    except TypeError:
        raise SystemExit((typer.echo(add_meta.pdf_not_exists)))

    # Loading .yaml file
    try:
        config_file: str = files.get_files("config").get(config_name)
        yfile = open(config_file, mode="r")
        yaml_meta = yaml.load(yfile, Loader=SafeLoader)
    except (TypeError, ScannerError, AttributeError) as error:
        if "yaml" in str(error):
            raise SystemExit(typer.echo(add_meta.yaml_error))
        else:
            raise SystemExit(typer.echo(add_meta.yaml_not_exist))

    try:
        # Loading .pdf
        reader = PdfFileReader(pdf_in)
        writer = PdfFileWriter()
        writer.appendPagesFromReader(reader)
        metadata = reader.getDocumentInfo()
        writer.addMetadata(metadata)

        typer.echo(f"The following metadata has been added:")
        for data in dict(yaml_meta):
            typer.echo(dict(yaml_meta).get(data))

        # config file
        writer.addMetadata(
            {
                '/Author': yaml_meta.get('/Author', 'Author unknown'),
                '/Title': yaml_meta.get('/Title', 'Title unknown'),
                '/Keywords': yaml_meta.get('/Keywords', 'Keywords unknown')
            }
        )

        # .pdf with metadata
        save_path: str = files.get_folders().get("results")
        pdf_out = open(rf"{save_path}{slash}{save_name}_{pdf_name}", "wb")
        writer.write(pdf_out)

        # Closing files
        pdf_out.close()
        pdf_in.close()

        # Added metadata
        typer.echo(add_meta.metadata_added)

    except OSError:
        raise SystemExit((typer.echo(add_meta.pdf_corrupt)))


@app.command(name=pdf_docx.pdf_to_docx_name, help=pdf_docx.pdf_to_docx_help)
def pdf_to_docx(
    pdf_path: str = typer.Argument("", help=pdf_docx.input_pdf_help),
    output_docx: str = typer.Option(
        "", "--save", "-s", help=pdf_docx.output_docx_help
    ),
) -> None:
    """
    Convert an input PDF to a DOCX file using pdf2docx.

    :arg:
        pdf_path: str path to the PDF file
        output_docx: optional DOCX file name
    :returns:
        None
    """
    try:
        if not pdf_path:
            raise SystemExit(typer.echo(pdf_docx.pdf_missing))

        if not os.path.isabs(pdf_path):
            pdf_path = os.path.join(current_dir, pdf_path)

        if not os.path.exists(pdf_path):
            raise SystemExit(typer.echo(pdf_docx.pdf_missing))

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        docx_name = output_docx if output_docx else f"{base_name}.docx"
        docx_path = os.path.join(os.path.dirname(pdf_path), docx_name)

        typer.echo(pdf_docx.converting)
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        typer.echo(pdf_docx.converted)
    except Exception:
        raise SystemExit(typer.echo(pdf_docx.conversion_error))


@app.command(name=pdf_text.pdf_to_text_name, help=pdf_text.pdf_to_text_help)
def pdf_to_text(
    pdf_path: str = typer.Argument("", help=pdf_text.input_pdf_help),
    output_txt: str = typer.Option("", "--save", "-s", help=pdf_text.output_txt_help),
    lang: str = typer.Option("ara", "--lang", "-l", help=pdf_text.lang_help),
    psm: int = typer.Option(6, "--psm", help="Tesseract page segmentation mode."),
    oem: int = typer.Option(1, "--oem", help="Tesseract OCR Engine mode."),
) -> None:
    """
    Extract plain text using ocrmypdf sidecar (Tesseract order of reading).
    Creates a temporary OCR PDF and writes text to output_txt.
    """
    try:
        if not pdf_path:
            raise SystemExit(typer.echo(pdf_text.pdf_missing))

        if not os.path.isabs(pdf_path):
            pdf_path = os.path.join(current_dir, pdf_path)
        if not os.path.exists(pdf_path):
            raise SystemExit(typer.echo(pdf_text.pdf_missing))

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        txt_name = output_txt if output_txt else f"{base_name}.txt"
        txt_path = os.path.join(os.path.dirname(pdf_path), txt_name)

        # temp OCR pdf path
        with tempfile.TemporaryDirectory() as tmpdir:
            ocr_pdf_path = os.path.join(tmpdir, f"{base_name}_ocr.pdf")
            typer.echo(pdf_text.converting)
            cmd = [
                "ocrmypdf",
                "--force-ocr",
                "--tesseract-pagesegmode", str(psm),
                "--tesseract-oem", str(oem),
                "-l", lang,
                "--sidecar", txt_path,
                pdf_path,
                ocr_pdf_path,
            ]
            # run and capture errors
            subprocess.run(cmd, check=True)
        typer.echo(pdf_text.converted)
    except subprocess.CalledProcessError:
        raise SystemExit(typer.echo(pdf_text.conversion_error))


def _has_text_layer(pdf_path: str) -> bool:
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path, maxpages=1) or ""
        return bool(text.strip())
    except Exception:
        return False


def _extract_text_layer(pdf_path: str) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(pdf_path) or ""


def _arabic_ratio(s: str) -> float:
    if not s:
        return 0.0
    arabic_chars = re.findall(r"[\u0600-\u06FF]", s)
    return len(arabic_chars) / max(1, len(s))


def _is_arabic_text_disconnected(text: str) -> bool:
    """
    Check if Arabic text appears disconnected (common issue with PDF text layers).
    Returns True if Arabic characters are frequently isolated (not connected properly).
    """
    if not text:
        return False
    
    arabic_chars = re.findall(r"[\u0600-\u06FF]", text)
    if len(arabic_chars) < 10:  # Not enough Arabic to judge
        return False
    
    # Check for isolated Arabic characters (surrounded by spaces or line breaks)
    # This is a heuristic: if many Arabic chars are isolated, text layer is likely bad
    isolated_pattern = re.compile(r'[\s\n][\u0600-\u06FF][\s\n]')
    isolated_matches = len(isolated_pattern.findall(text))
    
    # If more than 20% of Arabic context shows isolation, consider it disconnected
    isolation_ratio = isolated_matches / max(1, len(arabic_chars))
    return isolation_ratio > 0.2


@app.command(name=pdf_verify.name, help=pdf_verify.help)
def pdf_verify_cmd(
    pdf_path: str = typer.Argument("", help=pdf_verify.input_pdf_help),
    out_dir: str = typer.Option("arabe ocr", "--out-dir", help=pdf_verify.out_dir_help),
    lang: str = typer.Option("ara", "--lang", "-l", help=pdf_verify.lang_help),
    threshold: float = typer.Option(0.99, "--threshold", help=pdf_verify.threshold_help),
) -> None:
    """
    Verify/extract with a target quality: if PDF has text layer, extract directly.
    Otherwise, OCR with sidecar. Writes text and a small JSON report.
    """
    if not pdf_path:
        raise SystemExit(typer.echo(pdf_verify.pdf_missing))

    if not os.path.isabs(pdf_path):
        pdf_path = os.path.join(current_dir, pdf_path)
    if not os.path.exists(pdf_path):
        raise SystemExit(typer.echo(pdf_verify.pdf_missing))

    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(out_dir, f"{base_name}.txt")
    report_path = os.path.join(out_dir, f"{base_name}.report.json")

    typer.echo(pdf_verify.processing)

    used_ocr = False
    try:
        if _has_text_layer(pdf_path):
            text = _extract_text_layer(pdf_path)
        else:
            used_ocr = True
            with tempfile.TemporaryDirectory() as tmpdir:
                ocr_pdf_path = os.path.join(tmpdir, f"{base_name}_ocr.pdf")
                cmd = [
                    "ocrmypdf",
                    "--force-ocr",
                    "--tesseract-pagesegmode", "6",
                    "--tesseract-oem", "1",
                    "-l", lang,
                    "--sidecar", txt_path,
                    pdf_path,
                    ocr_pdf_path,
                ]
                subprocess.run(cmd, check=True)
            # read sidecar
            text = open(txt_path, encoding="utf-8").read() if os.path.exists(txt_path) else ""

        # quality heuristics (no absolute truth for scans)
        length = len(text)
        ar_ratio = _arabic_ratio(text)
        # simple proxy: non-empty and arabic-heavy if lang is ara
        est_quality = 1.0 if not used_ocr else (0.98 + min(0.02, ar_ratio * 0.02))

        # persist text if from text layer
        if not used_ocr:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

        report = {
            "pdf": os.path.basename(pdf_path),
            "used_ocr": used_ocr,
            "lang": lang,
            "length": length,
            "arabic_ratio": round(ar_ratio, 4),
            "estimated_quality": round(est_quality, 4),
            "threshold": threshold,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        if est_quality < threshold:
            raise SystemExit(typer.echo(pdf_verify.failed))

        typer.echo(pdf_verify.done)
    except subprocess.CalledProcessError:
        raise SystemExit(typer.echo(pdf_text.conversion_error))


def _has_unpaper() -> bool:
    """Check if unpaper is available on the system."""
    try:
        subprocess.run(["unpaper", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _run_ocr_sidecar(pdf_path: str, out_txt: str, out_pdf: str, lang: str, psm: int = 6, oem: int = 1) -> None:
    # استخدام python -m ocrmypdf أولاً (الأفضل في Windows)، ثم ocrmypdf مباشرة
    ocrmypdf_base = None
    try:
        subprocess.run(
            [sys.executable, "-m", "ocrmypdf", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        ocrmypdf_base = [sys.executable, "-m", "ocrmypdf"]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # جرب ocrmypdf مباشرة
        try:
            subprocess.run(["ocrmypdf", "--version"], capture_output=True, check=True, timeout=5)
            ocrmypdf_base = ["ocrmypdf"]
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise FileNotFoundError("ocrmypdf غير متاح. يرجى تثبيته أولاً: pip install ocrmypdf")
    
    cmd = ocrmypdf_base + [
        "--force-ocr",
        "--deskew",
    ]
    # Only add --clean if unpaper is available
    # Note: --remove-background is temporarily not implemented in ocrmypdf
    if _has_unpaper():
        cmd.extend(["--clean"])
    cmd.extend([
        "--tesseract-pagesegmode", str(psm),
        "--tesseract-oem", str(oem),
        "-l", lang,
        "--sidecar", out_txt,
        pdf_path,
        out_pdf,
    ])
    subprocess.run(cmd, check=True)


def _pdftotext_layout(pdf_in: str, txt_out: str) -> None:
    try:
        subprocess.run(["pdftotext", "-layout", pdf_in, txt_out], check=True)
    except Exception:
        pass


@app.command(name=pdf_best.name, help=pdf_best.help)
def pdf_best_cmd(
    pdf_path: str = typer.Argument("", help=pdf_best.input_pdf_help),
    out_dir: str = typer.Option("arabe ocr", "--out-dir", help=pdf_best.out_dir_help),
    lang: str = typer.Option("ara", "--lang", "-l", help=pdf_best.lang_help),
) -> None:
    """
    OCR-only Arabic text extraction:
    - Always uses OCR (never uses text layer).
    - Two OCR passes (lang and lang+eng), also extract -layout variants; select best.
    Always outputs final text and a small report.
    """
    if not pdf_path:
        raise SystemExit(typer.echo(pdf_best.pdf_missing))
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.join(current_dir, pdf_path)
    if not os.path.exists(pdf_path):
        raise SystemExit(typer.echo(pdf_best.pdf_missing))

    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    final_txt = os.path.join(out_dir, f"{base}.txt")
    report_path = os.path.join(out_dir, f"{base}.best.report.json")

    typer.echo(pdf_best.processing)

    candidates = []  # (path, metrics)
    used_ocr = True  # Always use OCR, never use text layer
    
    try:
        # Always use OCR only, never use text layer
        ocr_success_a = False
        ocr_success_b = False
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # pass A: primary lang
                sidecar_a = os.path.join(tmpdir, f"{base}.a.txt")
                ocr_a_pdf = os.path.join(tmpdir, f"{base}.a.pdf")
                layout_a = None
                try:
                    _run_ocr_sidecar(pdf_path, sidecar_a, ocr_a_pdf, lang=lang)
                    ocr_success_a = True
                    # layout from pass A
                    if os.path.exists(ocr_a_pdf):
                        layout_a = os.path.join(tmpdir, f"{base}.a.layout.txt")
                        _pdftotext_layout(ocr_a_pdf, layout_a)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    typer.echo(f"OCR pass A failed: {e}")

                # pass B: lang + eng
                sidecar_b = os.path.join(tmpdir, f"{base}.b.txt")
                ocr_b_pdf = os.path.join(tmpdir, f"{base}.b.pdf")
                layout_b = None
                lang_b = f"{lang}+eng" if "eng" not in lang else lang
                try:
                    _run_ocr_sidecar(pdf_path, sidecar_b, ocr_b_pdf, lang=lang_b)
                    ocr_success_b = True
                    # layout from pass B
                    if os.path.exists(ocr_b_pdf):
                        layout_b = os.path.join(tmpdir, f"{base}.b.layout.txt")
                        _pdftotext_layout(ocr_b_pdf, layout_b)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    typer.echo(f"OCR pass B failed: {e}")

                # collect candidates if exist (store text content, not path)
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
                        txt = open(path, encoding="utf-8").read()
                        if txt.strip():  # Only add non-empty text
                            candidates.append((txt, {"source": source, "length": len(txt), "arabic_ratio": round(_arabic_ratio(txt), 4)}))
        except Exception as e:
            typer.echo(f"OCR process failed: {e}")

        # select best: highest arabic_ratio, then longer length
        if candidates:
            best_text, best_metrics = sorted(candidates, key=lambda x: (x[1]["arabic_ratio"], x[1]["length"]))[-1]
            with open(final_txt, "w", encoding="utf-8") as f:
                f.write(best_text)
            typer.echo(f"Selected best candidate: {best_metrics['source']} (Arabic ratio: {best_metrics['arabic_ratio']:.4f})")
        else:
            # OCR failed completely, raise error
            raise SystemExit(typer.echo("OCR failed completely. No text could be extracted. Please ensure Tesseract OCR with Arabic language data is installed."))

        # write report
        report = {
            "pdf": os.path.basename(pdf_path),
            "used_ocr": used_ocr,
            "lang_primary": lang,
            "final_text": os.path.basename(final_txt),
            "candidates": candidates,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        typer.echo(pdf_best.done)
    except subprocess.CalledProcessError:
        raise SystemExit(typer.echo(pdf_text.conversion_error))


if __name__ == "__main__":
    app()
