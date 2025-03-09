import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf_by_size(input_pdf_path, output_folder, max_size_mb=100):
    """
    Splits a PDF into smaller chunks, each approximately max_size_mb in size.

    Parameters:
        input_pdf_path (str): Path to the input PDF file.
        output_folder (str): Folder where the split PDFs will be saved.
        max_size_mb (int): Maximum size of each split PDF in megabytes.
    """
    # Convert size to bytes
    max_size_bytes = max_size_mb * 1024 * 1024

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Read the input PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)

    writer = PdfWriter()
    current_size = 0
    file_index = 1

    for i, page in enumerate(reader.pages):
        # Add page to the writer
        writer.add_page(page)

        # Estimate the size of the current PDF chunk
        temp_output_path = os.path.join(output_folder, f"temp_output.pdf")
        with open(temp_output_path, "wb") as temp_output_file:
            writer.write(temp_output_file)

        current_size = os.path.getsize(temp_output_path)

        if current_size >= max_size_bytes or i == total_pages - 1:
            # Save the current chunk
            output_path = os.path.join(output_folder, f"output_chunk_{file_index}.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            print(f"Chunk {file_index} saved: {output_path} ({current_size / (1024 * 1024):.2f} MB)")

            # Reset the writer and size tracker
            writer = PdfWriter()
            current_size = 0
            file_index += 1

        # Remove temporary file
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

if __name__ == "__main__":
    input_pdf = input("Please enter the path to your PDF file: ").strip()
    output_dir = os.path.join(os.getcwd(), "split_pdf")
    
    if not os.path.exists(input_pdf):
        print(f"Error: File '{input_pdf}' does not exist!")
        exit(1)
        
    split_pdf_by_size(input_pdf, output_dir)
    print(f"\nAll chunks have been saved to: {output_dir}")
