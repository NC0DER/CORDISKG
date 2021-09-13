import os
import time
import pandas
import requests
from io import StringIO
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
from CordisKG.utils import counter, clear_screen


@counter
def download_pdf(url, filename, max_retries = 5, backoff_factor = 0.5):
    """
    Function which connects to the EU Cordis site
    and downloads a deliverable pdf using the url.
    This function also returns True if the pdf 
    was succesfully retrieved and false otherwise.
    """

    # Open a new session, configure
    # the retry policy for all http connections,
    # and connect to the url.
    session = requests.Session()
    session.get(url)

    # Obtain cookies from the session and set the headers to a mozilla firefox user.
    cookies = session.cookies.get_dict()
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Download the html page text from the url.
    html_page = requests.get(url, cookies = cookies, headers = headers).text

    # Check if the html page contains the error code, and return early.
    if 'Error code' in html_page:
        return False

    # The download pdf url can be found in the bottom part of the page.
    l_idx = html_page.rfind('window.location=\'') + len('window.location=') + 1
    r_idx = html_page.rfind('\'')
    pdf_url = html_page[l_idx: r_idx]
    
    # Get a response from the pdf url.
    response = requests.get(pdf_url, cookies = cookies, headers = headers)

    # Save the file from the url, only if it's a pdf.
    if 'application/pdf' in response.headers.get('content-type'):
        with open(filename, 'wb') as file:
            file.write(response.content)
        return True
    else: 
        return False


@counter
def convert_pdf_to_txt(input_pdf, output_txt, max_pages = 5):
    """
    Function which converts a pdf to txt using pdfminer.
    Only the first max_pages are saved from the original pdf.
    """

    # Initialize necessary constructors
    resource_manager = PDFResourceManager()
    fake_file_handle = StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams = LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    # Open the pdf in binary mode.
    with open(input_pdf, 'rb') as pdf_file:

        # Iterate the pages of the pdf file.
        for page in PDFPage.get_pages(
            pdf_file, caching = True,
            maxpages = max_pages, 
            check_extractable = False):
            page_interpreter.process_page(page)
        
        # Obtain the selected text from the file handle.
        text = fake_file_handle.getvalue()

    # Cleanup opened file handles.
    converter.close()
    fake_file_handle.close()
    
    # Write the selected text from the pdf into a txt.
    with open(output_txt, 'w', encoding = 'utf-8-sig', errors = 'ignore') as txt_file:
        txt_file.write(text)
    return


def export_pdfs_to_txt(deliverables_csv, deliverables_dir, max_pages = 5):
    """
    Function which reads the deliverables csv, and makes a .txt file out of each row,
    where this .txt contains the first max_pages of the pdf, and the filename of the .txt
    is the rcn (Record Control Number). For storage reasons, only one .pdf is stored at a time, 
    while all .txts will be saved. Thus each download_url call overwrites the same pdf file.
    """

    # Read the input_csv
    rows = pandas.read_csv(deliverables_csv, sep = ';')
    start = 0
    total = len(rows)
    data = []
    
    # Iterate all rows of the deliverables
    for i in range(start, total):

        # Measure the duration of the iteration.
        # This is done to avoid flooding the server,
        # with download requests.
        start = time.perf_counter()
        print(f'Processing {i} out of {total} deliverables.')

        # Construct the file name and the path of the .pdf file.
        deliverable_pdf = os.path.join(
            deliverables_dir, 
            f'{total}.pdf'
        )
        # Read the url from each row, and save the pdf.
        download_status = download_pdf(rows['url'].iloc[i], deliverable_pdf)


        # The above function call returns the download status.
        # If the pdf failed to download, we continue to the next.
        if download_status == False:
            continue

        # Construct the file name and output path of the .txt file.
        output_path = os.path.join(
            deliverables_dir, 
            f'{rows["rcn"].iloc[i]}.txt'
        )
        
        # Convert the pdf to txt, if possible, and save it.
        try:
            convert_pdf_to_txt(deliverable_pdf, output_path, max_pages)
        except:
            pass
        end = time.perf_counter()

        # If the iteration had a duration less than a second then wait.
        if end - start < 1:
            time.sleep(1 - (end - start))
        clear_screen()
    return


if __name__ == '__main__': parse_pdf()
