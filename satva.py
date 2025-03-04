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

def extract_text_from_image_json(image_path, ocr_model):
    # Create document from image
    document = DocumentFile.from_images(image_path)
    result = ocr_model(document)

    # Export OCR result to JSON format (but store in a variable)
    ocr_data = result.export()

    # Extract text from JSON data
    text_content = []
    for page in ocr_data.get('pages', []):
        for block in page.get('blocks', []):
            for line in block.get('lines', []):
                line_text = ' '.join(word['value'] for word in line.get('words', []))
                if line_text.strip():  # Ensure only non-empty lines are added
                    text_content.append(line_text)

    # Return the extracted text or a fallback message
    return "\n".join(text_content) if text_content else "No text found in the image."
 

    # Create a PDF file from the extracted text (optional)
    # ... (implementation depends on the specific PDF creation library)
    
    

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

import json
from json2table import convert
def format_json_to_table(json_data):
    """
    Format nested JSON data into a table format.

    Args:
        json_data (str): The nested JSON data as a string.

    Returns:
        str: The formatted table as a string.
    """
    # Load the JSON data
    data = json.loads(json_data)

    # Convert the JSON data to a table format
    table = convert(data, build_direction='TOP_TO_BOTTOM')

    # Return the formatted table
    return table



# Load the JSON data


# Function to generate the invoice text
def generate_invoice_text(data):
    invoice_text = []

    # Vendor Details
    invoice_text.append("### Vendor Details")
    vendor_details = data.get("Vendor Details", {})
    invoice_text.append(f"- Name: {vendor_details.get('Name', '(not provided)')}")
    invoice_text.append(f"- GSTIN: {vendor_details.get('GSTIN', '(not provided)')}")
    invoice_text.append(f"- Email: {vendor_details.get('Email', '(not provided)')}\n")

    # Invoice Details
    invoice_text.append("### Invoice Details")
    invoice_details = data.get("Invoice Details", {})
    invoice_text.append(f"- Invoice Number: {invoice_details.get('Invoice Number', '(not provided)')}")
    invoice_text.append(f"- Invoice Date: {invoice_details.get('Invoice Date', '(not provided)')}\n")

    # Address Details
    invoice_text.append("### Address Details\n")
    
    # Vendor Address
    vendor_address = data.get("Address Details", {}).get("Vendor Address", {})
    invoice_text.append("**Vendor Address:**")
    invoice_text.append(f"- Name: {vendor_address.get('Name', '(not provided)')}")
    invoice_text.append(f"- Street: {vendor_address.get('Street', '(not provided)')}")
    invoice_text.append(f"- City: {vendor_address.get('City', '(not provided)')}")
    invoice_text.append(f"- State: {vendor_address.get('State', '(not provided)')}")
    invoice_text.append(f"- Pin Code: {vendor_address.get('Pin Code', '(not provided)')}")
    invoice_text.append(f"- GSTIN: {vendor_address.get('GSTIN', '(not provided)')}\n")

    # Bill-To Address
    bill_to_address = data.get("Address Details", {}).get("Bill-To Address", {})
    invoice_text.append("**Bill-To Address:**")
    invoice_text.append(f"- Name: {bill_to_address.get('Name', '(not provided)')}")
    invoice_text.append(f"- Street: {bill_to_address.get('Street', '(not provided)')}")
    invoice_text.append(f"- City: {bill_to_address.get('City', '(not provided)')}")
    invoice_text.append(f"- State: {bill_to_address.get('State', '(not provided)')}")
    invoice_text.append(f"- Pin Code: {bill_to_address.get('Pin Code', '(not provided)')}")
    invoice_text.append(f"- GSTIN: {bill_to_address.get('GSTIN', '(not provided)')}\n")

    # Ship-To Address
    ship_to_address = data.get("Address Details", {}).get("Ship-To Address", {})
    invoice_text.append("**Ship-To Address:**")
    invoice_text.append(f"- Name: {ship_to_address.get('Name', '(not provided)')}")
    invoice_text.append(f"- Street: {ship_to_address.get('Street', '(not provided)')}")
    invoice_text.append(f"- City: {ship_to_address.get('City', '(not provided)')}")
    invoice_text.append(f"- State: {ship_to_address.get('State', '(not provided)')}")
    invoice_text.append(f"- Pin Code: {ship_to_address.get('Pin Code', '(not provided)')}\n")

    # Tax Details
    invoice_text.append("### Tax Details")
    tax_details = data.get("Tax Details", {})
    invoice_text.append(f"- CGST: Rate: {tax_details.get('CGST', {}).get('Rate', '(not provided)')}, Amount: ₹{tax_details.get('CGST', {}).get('Amount', '(not provided)')}")
    invoice_text.append(f"- SGST: Rate: {tax_details.get('SGST', {}).get('Rate', '(not provided)')}, Amount: ₹{tax_details.get('SGST', {}).get('Amount', '(not provided)')}")
    invoice_text.append(f"- IGST: Rate: {tax_details.get('IGST', {}).get('Rate', '(not provided)')}, Amount: ₹{tax_details.get('IGST', {}).get('Amount', '(not provided)')}")
    invoice_text.append(f"- TCS: Rate: {tax_details.get('TCS', {}).get('Rate', '(not provided)')}, Amount: ₹{tax_details.get('TCS', {}).get('Amount', '(not provided)')}")
    invoice_text.append(f"- Total Tax Amount: ₹{tax_details.get('Total Tax Amount', '(not provided)')}\n")

    # Payment Details
    invoice_text.append("### Payment Details")
    payment_details = data.get("Payment Details", {})
    invoice_text.append(f"- Total Discount: {payment_details.get('Total Discount', '(not provided)')}")
    invoice_text.append(f"- Total Tax: ₹{payment_details.get('Total Tax', '(not provided)')}")
    invoice_text.append(f"- Grand Total Amount: ₹{payment_details.get('Grand Total Amount', '(not provided)')}")
    invoice_text.append(f"- Grand Total Amount in Words: {payment_details.get('Grand Total Amount in Words', '(not provided)')}\n")

    # Item Details
    invoice_text.append("### Item Details")
    invoice_text.append("| S.No | Description of Goods | HSN No | Quantity | Rate per Unit | Amount |")
    invoice_text.append("|------|---------------------|--------|----------|----------------|--------|")
    
    item_details = data.get("Item Details", [])
    for item in item_details:
        for detail in item.get("Item_Details", []):
            invoice_text.append(f"| {detail['S_No']} | {detail['Description_of_Goods']} | {detail['HSN_No']} | {detail['Quantity']} | ₹{detail['Rate_per_Unit']} | ₹{detail['Amount']} |")

    return "\n".join(invoice_text)


import streamlit as st
import os
import tempfile
import time
import json
import csv
import pandas as pd
from PIL import Image



def main():
    st.title('     S-A-T-V-A     ')

    # Add an image selection button
    image_file = st.file_uploader('Select an invoice image:', type=['jpg', 'png', 'jpeg'])
    start_time=time.time()
    if image_file is not None:
        # Read the image contents into a bytes buffer
        image_buffer = image_file.getbuffer()

        # Create a temporary file
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp_file.write(image_buffer)
        tmp_file.close()  # Close the file to ensure it's written to disk

        # Initialize OCR model
        ocr_model = initialize_ocr_model()

        # Extract text from image
        extracted_text = extract_text_from_image_json(tmp_file.name, ocr_model)

        # Load the image
        img = Image.open(image_file)
        img = img.resize((int(img.size[0] * 0.5), int(img.size[1] * 0.5)))

        # Create two columns
        col1, col2 = st.columns(2)

        # Display uploaded image in column 1
        with col1:
            st.image(img, caption="Uploaded Image", use_column_width=True)

        # Process the image and display the results in column 2
        with col2:
            with st.spinner('Processing...'):
                # Create prompts
                prompt1, prompt2 = create_prompts(extracted_text)
                print("text :-",extracted_text)
                response1 = get_model_response(prompt1)
                response2 = get_model_response(prompt2)

                # Extract JSON data from responses
                summary1 = response1.get('message', {}).get('content', 'No summary available.')
                summary2 = response2.get('message', {}).get('content', 'No summary available.')
                json_data_str_1, json_data_str_2 = extract_json_from_summary(summary1, summary2)
                print(json_data_str_1,json_data_str_2)
                print("#-="*50)
                merged_json_str = merge_json_data(json_data_str_1, json_data_str_2)
                print(merged_json_str)
                
                print("Close...............")


                

                # Convert JSON string to CSV data
                json_data = json.loads(merged_json_str)
                csv_data = []
                for key, value in json_data.items():
                    csv_data.append([key, value])

                # Create a CSV file
                with open('output.csv', 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Key", "Value"])  # header row
                    writer.writerows(csv_data)

                # Create tabs to display information
                tab1, tab2, tab3 = st.tabs(["Merged JSON", "Text", "CSV File"])
                with tab1:
                    json_obj = json.loads(merged_json_str)
                    # Create an HTML string to display the JSON data
                    st.markdown(f"<style>p {{ color: white }}</style>", unsafe_allow_html=True)
                    st.json(merged_json_str)
                    
                with tab2:
                    with st.container():
                       #st.markdown("<div style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
                       
                       data = json.loads(merged_json_str)
                       st.title("Invoice Display")
                       invoice_text = generate_invoice_text(data)
                       st.markdown(invoice_text)


                    #formatted_table = format_json_to_table(merged_json_str)
                    #st.markdown(formatted_table, unsafe_allow_html=True)
                    
                    
                    # Assuming you have a function to generate an Excel file
                    # excel_file = generate_excel_file(json_data)
                    # st.download_button('Download Excel File', excel_file, 'output.xlsx')
                with tab3:
                    st.write("CSV File:")
                    df = pd.DataFrame(csv_data, columns=["Key", "Value"])
                    st.dataframe(df)

        # Display messages or errors

        st.write("Messages:")
        st.write("1. Text extracted")
        st.write("2. Parsing is completed")
        st.write("3. Processing time: {:.2f} seconds".format(time.time() - start_time))
        
        # Delete the temporary file
        os.remove(tmp_file.name)

if __name__ == '__main__':
    st.set_page_config(
        page_title="Satva-1.0",
        page_icon=":camera:",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.write("<style>.main { background-color: #FFFFFF !important; }</style>", unsafe_allow_html=True)
    st.markdown("<style>body, td, p, span, div, h1, h2, h3, h4, h5, h6, pre, code { color: #000000 !important; }</style>", unsafe_allow_html=True)
    st.markdown("<style>.custom-text { color: #000000 !important; }</style>", unsafe_allow_html=True)
    
    
    main()