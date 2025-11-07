# Standard
# None

# Pip
import typer

# Custom
# None


class MessageKeys:
    """
    This class contains the strings for the respective functions
    so that they can be accessed through dot notation.
    """

    class GenerateDir:
        """
        see function generate_directories
        """

        generate_dir = "gen-dir"
        generate_dir_help = "Generate directories where the files should reside."

        generating_dir = "Directories being generated."
        directory_generated = typer.style(
            "Directories have been generated.", fg=typer.colors.GREEN
        )
        folders_exists = typer.style(
            "The folders already exist in this directory.", fg=typer.colors.RED
        )

    class GeneratePdf:
        """
        see function generate_pdf
        """

        generate_pdf_name = "gen-pdf"
        generate_pdf_command = "Generate a .pdf from a collection of images."
        images_generate = typer.style(
            "The .pdf file is being generated. Please wait...",
            fg=typer.colors.BRIGHT_MAGENTA,
        )
        generate_pdf_help = "Enter the save name of the .pdf file"
        file_created = typer.style(
            ".pdf file was successfully created!", fg=typer.colors.GREEN
        )
        no_images = typer.style(
            "Error: Please make sure that there are images in the image directory ",
            fg=typer.colors.RED,
        )

        images_removed = typer.style(
            "The images have been removed from the directory",
            fg=typer.colors.RED,
        )

        retain_images = typer.style("Images will not be deleted",
                                    fg=typer.colors.GREEN)

        missing_directory = typer.style(
            "Error: The image directory is missing!", fg=typer.colors.RED
        )

        generate_custom_dir_long = "--dir"
        generate_custom_dir_short = "-d"
        generate_custom_dir_help = ""

        generated_file_name_long = "--save"
        generated_file_name_short = "-s"

    class AddMetadata:
        """
        see function add_metadata
        """

        add_metadata_name = "add-metadata"
        add_metadata_help = (
            "Add the data from the .yaml file " "to the .pdf as metadata."
        )

        meta_pdf = "The name of the .pdf that should have metadata added."
        save_name = "The name of the new .pdf file with metadata."
        yaml_error = typer.style(
            "The .yaml file could not be parsed. "
            "\nPlease make sure that you have "
            "correctly formatted the .yaml file",
            fg=typer.colors.RED,
        )

        yaml_not_exist = typer.style(
            "The .yaml file that you have selected does not exist.",
            fg=typer.colors.RED
        )

        pdf_not_exists = typer.style(
            "The .pdf either does not exist or the "
            "file name was not entered correctly. "
            "Please check the file name.",
            fg=typer.colors.RED,
        )

        pdf_corrupt = typer.style(
            "The file you entered is either corrput or "
            "is not a .pdf file. "
            "Please check the file again.",
            fg=typer.colors.RED,
        )

        yaml_config = "The name of the .yaml file which contains the config data."
        metadata_added = typer.style(
            "The metadata has been successfully added!", fg=typer.colors.GREEN
        )

        results = "results"

    class PdfToDocx:
        """
        see function pdf_to_docx
        """

        pdf_to_docx_name = "pdf-to-docx"
        pdf_to_docx_help = "Convert a PDF file to a DOCX (Word) document."
        input_pdf_help = "The name or path of the input PDF file."
        output_docx_help = "The output DOCX file name (defaults to input name)."
        converting = typer.style("Converting PDF to DOCX...", fg=typer.colors.BRIGHT_MAGENTA)
        converted = typer.style("DOCX file created successfully!", fg=typer.colors.GREEN)
        pdf_missing = typer.style("Error: The specified PDF could not be found.", fg=typer.colors.RED)
        conversion_error = typer.style("Error: Conversion failed. Please check the PDF file.", fg=typer.colors.RED)

    class PdfToText:
        """
        see function pdf_to_text
        """

        pdf_to_text_name = "pdf-to-text"
        pdf_to_text_help = "Extract plain text from a (scanned) PDF using Tesseract (sidecar)."
        input_pdf_help = "Input PDF path."
        output_txt_help = "Output TXT file name (defaults to input name + .txt)."
        lang_help = "OCR language code (e.g., ara, eng, fra+eng)."
        converting = typer.style("Extracting text via OCR...", fg=typer.colors.BRIGHT_MAGENTA)
        converted = typer.style("Text file created successfully!", fg=typer.colors.GREEN)
        pdf_missing = typer.style("Error: The specified PDF could not be found.", fg=typer.colors.RED)
        conversion_error = typer.style("Error: OCR failed. Please verify Tesseract/lang data.", fg=typer.colors.RED)

    class PdfVerify:
        """
        see function pdf_verify
        """

        name = "pdf-verify"
        help = "Extract text aiming for >= threshold quality; detects text layer else OCR."
        input_pdf_help = "Input PDF path."
        out_dir_help = "Directory to write outputs (text + report)."
        lang_help = "OCR language (e.g., ara, eng, fra+eng)."
        threshold_help = "Required minimal quality (0-1)."
        processing = typer.style("Verifying and extracting...", fg=typer.colors.BRIGHT_MAGENTA)
        done = typer.style("Extraction completed.", fg=typer.colors.GREEN)
        failed = typer.style("Quality below threshold.", fg=typer.colors.RED)
        pdf_missing = typer.style("Error: The specified PDF could not be found.", fg=typer.colors.RED)

    class PdfBest:
        """
        see function pdf_best
        """

        name = "pdf-best"
        help = "Best-effort Arabic text extraction: detect text layer or multi-pass OCR, select best."
        input_pdf_help = "Input PDF path."
        out_dir_help = "Directory to write the final text and report."
        lang_help = "Primary OCR language (default ara)."
        processing = typer.style("Running best-effort extraction...", fg=typer.colors.BRIGHT_MAGENTA)
        done = typer.style("Best-effort extraction completed.", fg=typer.colors.GREEN)
        pdf_missing = typer.style("Error: The specified PDF could not be found.", fg=typer.colors.RED)