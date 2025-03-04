import json
import time
import pdfplumber
import pandas as pd
import ollama
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def initialize_ocr_model():
    return ocr_predictor(pretrained=True)

def process_image_to_pdf(image_path, pdf_filename, ocr_model):
    document = DocumentFile.from_images(image_path)
    result = ocr_model(document)
    
    # Export OCR result to JSON
    with open('image.json', 'w') as json_file:
        json.dump(result.export(), json_file, indent=4)

    # Load JSON data
    with open('image.json', 'r') as f:
        data = json.load(f)
    
    # Create PDF with ReportLab
    pdf_canvas = canvas.Canvas(pdf_filename, pagesize=letter)
    pdf_canvas.setFont("Helvetica", 10)
    page_width, page_height = letter

    for page in data['pages']:
        dimensions = page['dimensions']
        width, height = dimensions

        for block in page['blocks']:
            for line in block['lines']:
                line_text = ' '.join(word['value'] for word in line['words'])
                first_word_geometry = line['words'][0]['geometry']
                x1, y1 = normalize_coordinates(first_word_geometry[0], page_width, page_height)
                pdf_canvas.drawString(x1, y1, line_text)

        pdf_canvas.showPage()
    
    pdf_canvas.save()

def normalize_coordinates(coord, width, height):
    return coord[0] * width, (1 - coord[1]) * height

def extract_text_from_pdf(pdf_filename):
    text_content = []
    with pdfplumber.open(pdf_filename) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text.strip())
    return "\n".join(text_content)

def create_prompts(extracted_text):
    prompt1 = (
        f'Text: {extracted_text} from this text \n'
        'Extract and format the following details from the provided text into a JSON file:\n\n'
        '1. Vendor Details:\n'
        '   - Name\n'
        '   - GSTIN\n'
        '   - Email\n\n'
        '2. Invoice Details:\n'
        '   - Invoice Number\n'
        '   - Invoice Date\n\n'
        '3. Address Details:\n'
        '   - Vendor Address (including name, street, city, state, pin code, GSTIN)\n'
        '   - Bill-To Address (including name, street, city, state, pin code, GSTIN)\n'
        '   - Ship-To Address (including name, street, city, state, pin code)\n\n'
        '4. Tax Details:\n'
        '   - CGST:\n'
        '     - Rate\n'
        '     - Amount\n'
        '   - SGST:\n'
        '     - Rate\n'
        '     - Amount\n'
        '   - IGST:\n'
        '     - Rate\n'
        '     - Amount\n'
        '   - TCS:\n'
        '     - Rate\n'
        '     - Amount\n'
        '   - Total Tax Amount\n\n'
        '5. Payment Details:\n'
        '   - Total Discount\n'
        '   - Total Tax\n'
        '   - Grand Total Amount\n'
        '   - Grand Total Amount in Words\n\n'
        '6. Terms and Conditions:\n'
        '   - Conditions \n'
        '   - Declaration \n'
        '   - Narrations \n\n'
        '7. Bank Details (if any):\n'
        '   - Bank Name\n'
        '   - IFSC\n'
        '   - Account Number\n'
        '   - Branch\n'
        '   - SWIFT Code\n\n'
        'Ensure that all numerical values are enclosed in double quotes. If any of the items are not present in the extracted text, leave the corresponding fields empty or set them to null. Output the data in JSON str format, ensuring that no fields are omitted.\n\n'
    )

    prompt2 = (
        f'Text: {extracted_text} from this text \n'
        'parse this text and return only the item details in json format  \n'
        'Extract  and format the following details from the provided text into a JSON file:\n\n'
        'Item Details :  \n'
        '      - S_No: Serial number of the item\n'
        '            - Description_of_Goods: Description of the item\n'
        '            - HSN_No: HSN/SAC code\n'
        '            - Quantity: Quantity of the item\n'
        '            - Rate_per_Unit: Rate per unit of the item\n'
        '            - Amount: Total amount for the item\n    '
        'Ensure that all numerical values are enclosed in double quotes. If any of the items are not present in the extracted text, leave the corresponding fields empty or set them to null. Output the data in JSON str format, ensuring that no fields are omitted.\n'
        'Once again ensure that all numerical(including serial  numbers) values are enclosed in double quotes.\n\n'
    )

    return prompt1, prompt2

def get_model_response(prompt, model_name="llama3.2:3b"):
    return ollama.chat(
        model=model_name,
        messages=[{'role': 'user', 'content': prompt}]
    )

def extract_json_from_summary(summary1, summary2):
    def find_brace_indices(text):
        start_index = text.find('{')
        end_index = text.rfind('}')
        return start_index, end_index

    def extract_json(text, label):
        start_index, end_index = find_brace_indices(text)
        if start_index != -1 and end_index != -1:
            return text[start_index:end_index + 1].strip()
        return None

    return extract_json(summary1, "summary1"), extract_json(summary2, "summary2")

import json

def validate_json(json_str):
    try:
        json.loads(json_str)
        print("Valid JSON!")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")

def merge_json_data(json_str1, json_str2):
    """
    Merge JSON data from two strings, converting the second string into a JSON array
    and adding it under the 'Item Details' key in the first JSON object.

    Args:
    json_str1 (str): The JSON string for the main data.
    json_str2 (str): The JSON string for the items data.

    Returns:
    str: A JSON string with the merged data.
    """
    def convert_to_json_array(original_data_str):
        """
        Convert a string of JSON objects (without array brackets) into a properly formatted JSON array.
        
        Args:
        original_data_str (str): A string containing JSON objects separated by commas.
        
        Returns:
        str: A JSON array formatted as a string.
        """
        # Remove any extra newlines or spaces
        cleaned_str = original_data_str.strip()
        
        if not cleaned_str:
            raise ValueError("The input string is empty or contains only whitespace.")
        
        # Check if the string starts with '{' and ends with '}' indicating single object
        if cleaned_str.startswith('{') and cleaned_str.endswith('}'):
            # Wrap the single object in an array
            json_array_str = '[' + cleaned_str + ']'
        else:
            # Add brackets if not present
            if not cleaned_str.startswith('['):
                cleaned_str = '[' + cleaned_str
            if not cleaned_str.endswith(']'):
                cleaned_str = cleaned_str + ']'
            
            # Fix potential missing commas between objects
            json_array_str = cleaned_str
        
        return json_array_str

    # Convert str2 into a proper JSON array string
    json_str2_corrected = convert_to_json_array(json_str2)

    # Parse the JSON strings into Python dictionaries and lists
    try:
        json_data_str_1 = json.loads(json_str1)
        json_data_str_2 = json.loads(json_str2_corrected)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None

    # Add str2 data under the key "Item Details" in json_data_str_1
    json_data_str_1["Item Details"] = json_data_str_2

    # Convert the updated dictionary back to a JSON string
    combined_json_str = json.dumps(json_data_str_1, indent=4)

    return combined_json_str


import pandas as pd
import json
import os

def json_to_excel(json_str, output_file):
    """
    Append JSON data to an existing Excel file's sheets.
    
    Args:
    json_str (str): JSON data as a string.
    output_file (str): Path to the existing Excel file.
    """
    # Load JSON data
    merged_json = json.loads(json_str)
    
    # Extract Invoice Number from JSON data
    invoice_number = merged_json.get('Invoice Details', {}).get('Invoice Number', '')

    # Helper function to safely get nested data
    def safe_get(d, keys, default=''):
        """
        Safely get a value from a nested dictionary.
        
        Args:
        d (dict): The dictionary to search.
        keys (list): A list of keys representing the path to the desired value.
        default: The value to return if any key is not found (default is an empty string).

        Returns:
        The value if found, otherwise the default value.
        """
        value = d
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    # Define a helper function to append data to an existing sheet
    def append_to_sheet(sheet_name, df, writer):
        try:
            # Read existing sheet
            existing_df = pd.read_excel(output_file, sheet_name=sheet_name)
            # Append the new data to the existing DataFrame
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except FileNotFoundError:
            # If the file does not exist yet, create a new sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        except ValueError:
            # Handle case where the sheet does not exist yet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Load existing Excel file and prepare to update it
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        try:
            # Update Vendor Details
            vendor_df = pd.DataFrame([merged_json.get('Vendor Details', {})])
            vendor_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Vendor Details', vendor_df, writer)
        except Exception as e:
            print(f"Error updating Vendor Details sheet: {e}")

        try:
            # Update Invoice Details
            invoice_df = pd.DataFrame([merged_json.get('Invoice Details', {})])
            append_to_sheet('Invoice Details', invoice_df, writer)
        except Exception as e:
            print(f"Error updating Invoice Details sheet: {e}")

        try:
            # Update Address Details
            address_data = merged_json.get('Address Details', {})
            address_df = pd.DataFrame({
                'Vendor Address - Name': [safe_get(address_data, ['Vendor Address', 'Name'])],
                'Vendor Address - Street': [safe_get(address_data, ['Vendor Address', 'Street'])],
                'Vendor Address - City': [safe_get(address_data, ['Vendor Address', 'City'])],
                'Vendor Address - State': [safe_get(address_data, ['Vendor Address', 'State'])],
                'Vendor Address - Pin Code': [safe_get(address_data, ['Vendor Address', 'Pin Code'])],
                'Vendor Address - GSTIN': [safe_get(address_data, ['Vendor Address', 'GSTIN'])],
                'Bill-To Address - Name': [safe_get(address_data, ['Bill-To Address', 'Name'])],
                'Bill-To Address - Street': [safe_get(address_data, ['Bill-To Address', 'Street'])],
                'Bill-To Address - City': [safe_get(address_data, ['Bill-To Address', 'City'])],
                'Bill-To Address - State': [safe_get(address_data, ['Bill-To Address', 'State'])],
                'Bill-To Address - Pin Code': [safe_get(address_data, ['Bill-To Address', 'Pin Code'])],
                'Ship-To Address - Name': [safe_get(address_data, ['Ship-To Address', 'Name'])],
                'Ship-To Address - Street': [safe_get(address_data, ['Ship-To Address', 'Street'])],
                'Ship-To Address - City': [safe_get(address_data, ['Ship-To Address', 'City'])],
                'Ship-To Address - State': [safe_get(address_data, ['Ship-To Address', 'State'])],
                'Ship-To Address - Pin Code': [safe_get(address_data, ['Ship-To Address', 'Pin Code'])]
            })
            address_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Address Details', address_df, writer)
        except Exception as e:
            print(f"Error updating Address Details sheet: {e}")

        try:
            # Update Tax Details
            tax_details = merged_json.get('Tax Details', {})
            tax_details_df = pd.DataFrame({
                'CGST Rate': [safe_get(tax_details, ['CGST', 'Rate'], '')],
                'CGST Amount': [safe_get(tax_details, ['CGST', 'Amount'], '')],
                'SGST Rate': [safe_get(tax_details, ['SGST', 'Rate'], '')],
                'SGST Amount': [safe_get(tax_details, ['SGST', 'Amount'], '')],
                'IGST Rate': [safe_get(tax_details, ['IGST', 'Rate'], '')],
                'IGST Amount': [safe_get(tax_details, ['IGST', 'Amount'], '')],
                'TCS Rate': [safe_get(tax_details, ['TCS', 'Rate'], '')],
                'TCS Amount': [safe_get(tax_details, ['TCS', 'Amount'], '')],
                'Total Tax Amount': [safe_get(tax_details, ['Total Tax Amount'], '')]
            })
            tax_details_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Tax Details', tax_details_df, writer)
        except Exception as e:
            print(f"Error updating Tax Details sheet: {e}")

        try:
            # Update Payment Details
            payment_details = merged_json.get('Payment Details', {})
            payment_details_df = pd.DataFrame({
                'Total Discount': [safe_get(payment_details, ['Total Discount'], '')],
                'Total Tax': [safe_get(payment_details, ['Total Tax'], '')],
                'Grand Total Amount': [safe_get(payment_details, ['Grand Total Amount'], '')],
                'Grand Total Amount in Words': [safe_get(payment_details, ['Grand Total Amount in Words'], '')]
            })
            payment_details_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Payment Details', payment_details_df, writer)
        except Exception as e:
            print(f"Error updating Payment Details sheet: {e}")

        try:
            # Update Terms and Conditions
            terms_conditions = merged_json.get('Terms and Conditions', {})
            conditions_list = safe_get(terms_conditions, ['Conditions'], [])
            declaration_list = [safe_get(terms_conditions, ['Declaration'], '')]
            narrations_list = safe_get(terms_conditions, ['Narrations'], [])
            
            # Ensure lists are in proper format
            if not isinstance(conditions_list, list):
                conditions_list = [conditions_list]
            if not isinstance(declaration_list, list):
                declaration_list = [declaration_list]
            if not isinstance(narrations_list, list):
                narrations_list = [narrations_list]
            
            # Create DataFrames for each part
            conditions_df = pd.DataFrame({'Conditions': conditions_list})
            declaration_df = pd.DataFrame({'Declaration': declaration_list})
            narrations_df = pd.DataFrame({'Narrations': narrations_list})
            
            # Combine DataFrames
            terms_conditions_combined_df = pd.concat([conditions_df, declaration_df, narrations_df], axis=1)
            terms_conditions_combined_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            
            # Append to the Terms and Conditions sheet
            append_to_sheet('Terms and Conditions', terms_conditions_combined_df, writer)
        except Exception as e:
            print(f"Error updating Terms and Conditions sheet: {e}")

        try:
            # Update Bank Details
            bank_df = pd.DataFrame([merged_json.get('Bank Details', {})])
            bank_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Bank Details', bank_df, writer)
        except Exception as e:
            print(f"Error updating Bank Details sheet: {e}")

        try:
            # Update Item Details
            item_df = pd.DataFrame(merged_json.get('Item Details', []))
            item_df.insert(0, 'Invoice Number', invoice_number)  # Insert invoice number at the start
            append_to_sheet('Item Details', item_df, writer)
        except Exception as e:
            print(f"Error updating Item Details sheet: {e}")



import os
import time

def process_image_folder(folder_path, output_file):
    
    
    # Initialize OCR model
    ocr_model = initialize_ocr_model()
    
    # Iterate over all image files in the folder
    for image_filename in os.listdir(folder_path):
        if image_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(folder_path, image_filename)
            pdf_filename = f"temp_{image_filename}.pdf"
            start_time = time.time()

            # Process image and create PDF
            process_image_to_pdf(image_path, pdf_filename, ocr_model)
            
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(pdf_filename)
            
            # Create prompts
            prompt1, prompt2 = create_prompts(extracted_text)
            
            # Get model responses
            response1 = get_model_response(prompt1)
            response2 = get_model_response(prompt2)
            
            # Extract JSON data from responses
            summary1 = response1.get('message', {}).get('content', 'No summary available.')
            summary2 = response2.get('message', {}).get('content', 'No summary available.')
            json_data_str_1, json_data_str_2 = extract_json_from_summary(summary1, summary2)
            print(json_data_str_1)
            print(json_data_str_2)
            print('+3-'*29,'\n')
            
            # Merge JSON data
            merged_json_str = merge_json_data(json_data_str_1, json_data_str_2)
            
            # Save to Excel
            json_to_excel(merged_json_str, output_file)
            
            # Clean up temporary PDF file
            os.remove(pdf_filename)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f'Execution time: {execution_time} seconds')



    
if __name__ == "__main__":
    folder_path = r'image'  # Path to the folder containing images
    output_file = 'output_1.xlsx'
    process_image_folder(folder_path, output_file)







