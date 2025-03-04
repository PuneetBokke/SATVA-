import streamlit as st
from streamlit_option_menu import option_menu
from tr1 import *
import streamlit as st
from PIL import Image
import io
import pandas as pd
import matplotlib.pyplot as plt


import numpy as np
import matplotlib.pyplot as plt

def clean_numerical_values_in_excel(file_path, output_file_path):
    """
    Clean numerical values in specific columns of an Excel file with multiple sheets.

    Parameters:
    file_path (str): Path to the input Excel file.
    output_file_path (str): Path to the output Excel file.

    Returns:
    None
    """
    xl = pd.ExcelFile(file_path)

    with pd.ExcelWriter(output_file_path) as writer:
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            if sheet_name == 'Payment Details':
                df['Total Tax'] = df['Total Tax'].apply(lambda x: pd.to_numeric(x.replace(',', '').replace('$', ''), errors='coerce') if isinstance(x, str) else x)
                df['Grand Total Amount'] = df['Grand Total Amount'].apply(lambda x: pd.to_numeric(x.replace(',', '').replace('$', ''), errors='coerce') if isinstance(x, str) else x)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Cleaned Excel file saved to {output_file_path}")

def display_images_in_grid(images, cols=3):
    """
    Display a list of images in a grid layout.
    
    Args:
    - images (list): A list of image objects.
    - cols (int): Number of columns for the grid.
    """
    # Create the grid layout
    for idx, img in enumerate(images):
        if idx % cols == 0:
            row = st.columns(cols)
        row[idx % cols].image(img, use_column_width=True)


def plot_numerical_values(file_path):
    """
    Plot numerical values in specific columns of an Excel file.

    Parameters:
    file_path (str): Path to the input Excel file.

    Returns:
    None
    """
    # Load the cleaned Excel file
    df = pd.read_excel(file_path, sheet_name='Payment Details')

    # Calculate metrics
    total_tax = df['Total Tax'].sum()
    total_amount = df['Grand Total Amount'].sum()

    # Display metrics in a box
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric(label="Total Tax", value=f"{total_tax:,.2f}")
    with col2:
        st.metric(label="Total Amount", value=f"{total_amount:,.2f}")

    # Create a figure and axis object
    fig, ax = plt.subplots(figsize=(6, 3))

    # Set the x-coordinates for the bars
    x = np.arange(len(df['Invoice Number']))

    # Set the width of the bars
    width = 0.25

    # Plot the Grand Total Amount bars
    ax.bar(x - width/2, df['Grand Total Amount'], width, label='Grand Total Amount', color='b')

    # Plot the Total Tax bars
    ax.bar(x + width/2, df['Total Tax'], width, label='Total Tax', color='r')

    # Set the x-axis ticks
    ax.set_xticks(x)
    ax.set_xticklabels(df['Invoice Number'], rotation=45, ha='right')

    # Set the y-axis label
    ax.set_ylabel('Amount')

    # Set the title
    ax.set_title('Grand Total Amount and Total Tax by Invoice Number')

    # Legend
    ax.legend()

    # Display the plot in Streamlit
    st.pyplot(fig)


st.set_page_config(
    page_title="SATVA",
    page_icon="👽",
    layout="wide",
    initial_sidebar_state="auto",
)

# 1. as sidebar menu
with st.sidebar:
    selected = option_menu("Main Menu", ["Home", "Upload", "Tasks", 'Settings'], 
        icons=['house', 'cloud-upload', "list-task", 'gear'], menu_icon="cast", default_index=1)



if selected == "Home":
    # Home content
    st.title("Home Page")
    st.write("Welcome to the home page.")

# Set the layout to wide
#st.set_page_config(layout="wide")


if selected == "Upload":
   
    

# Title of the app
   st.title("S-A-T-V-A Invoice extraction ")

def json_to_text(json_data):
    """
    Dynamically converts nested JSON data into a visually structured text format.
    
    Parameters:
    - json_data: The JSON data to be converted (nested and may change dynamically).
    
    Returns:
    - A string representing the formatted text version of the JSON data.
    """
    try:
        # Helper function to safely extract nested data
        def get_nested_value(dct, keys, default='N/A'):
            for key in keys:
                dct = dct.get(key, {})
                if not isinstance(dct, dict):
                    return dct
            return default

        # Initialize formatted text
        formatted_text = "\n"
        formatted_text += "        INVOICE\n"
        formatted_text += "\n\n"

        # Vendor Information
        formatted_text += "VENDOR INFORMATION:\n"
        formatted_text += "-------------------\n"
        vendor_name = get_nested_value(json_data, ['vendor_details', 'name'])
        vendor_gst = get_nested_value(json_data, ['vendor_details', 'gst'])
        formatted_text += f"Vendor Name     : {vendor_name}\n"
        formatted_text += f"Vendor GST No.  : {vendor_gst}\n\n"

        # Invoice Details
        formatted_text += "INVOICE DETAILS:\n"
        formatted_text += "----------------\n"
        invoice_no = get_nested_value(json_data, ['invoice_details', 'invoice_no'])
        invoice_date = get_nested_value(json_data, ['invoice_details', 'date'])
        formatted_text += f"Invoice Number  : {invoice_no}\n"
        formatted_text += f"Invoice Date    : {invoice_date}\n\n"

        # Address Details (Bill To and Ship To)
        formatted_text += "ADDRESS DETAILS:\n"
        formatted_text += "----------------\n"
        bill_to_name = get_nested_value(json_data, ['address_details', 'bill_to', 'name'])
        bill_to_street = get_nested_value(json_data, ['address_details', 'bill_to', 'street'])
        bill_to_state = get_nested_value(json_data, ['address_details', 'bill_to', 'state'])

        ship_to_name = get_nested_value(json_data, ['address_details', 'ship_to', 'name'])
        ship_to_street = get_nested_value(json_data, ['address_details', 'ship_to', 'street'])
        ship_to_state = get_nested_value(json_data, ['address_details', 'ship_to', 'state'])

        formatted_text += f"Bill To:\n"
        formatted_text += f"  Name          : {bill_to_name}\n"
        formatted_text += f"  Address       : {bill_to_street}\n"
        formatted_text += f"  State         : {bill_to_state}\n\n"

        formatted_text += f"Ship To:\n"
        formatted_text += f"  Name          : {ship_to_name}\n"
        formatted_text += f"  Address       : {ship_to_street}\n"
        formatted_text += f"  State         : {ship_to_state}\n\n"

        # Item Details
        formatted_text += "ITEM DETAILS:\n"
        formatted_text += "--------------\n"
        formatted_text += "| Item Description   | HSN Code | Quantity | Unit  | Amount     |\n"
        formatted_text += "|--------------------|----------|----------|-------|------------|\n"

        for item in json_data.get('item_details', []):
            description = item.get('description', 'N/A')
            hsn = item.get('hsn', 'N/A')
            qty = item.get('qty', 'N/A')
            unit = item.get('unit', 'N/A')
            amount = item.get('amount', 'N/A')
            formatted_text += f"| {description[:18]:<18} | {hsn:<8} | {qty:<8} | {unit:<5} | {amount:<10} |\n"
        formatted_text += "\n"

        # Tax Details
        formatted_text += "TAX INFORMATION:\n"
        formatted_text += "----------------\n"
        igst_rate = get_nested_value(json_data, ['tax_details', 'igst', 'rate'])
        igst_amount = get_nested_value(json_data, ['tax_details', 'igst', 'amount'])
        tcs_amount = get_nested_value(json_data, ['tax_details', 'tcs_on_sales', 'amount'])

        formatted_text += f"IGST Rate       : {igst_rate}\n"
        formatted_text += f"IGST Amount     : {igst_amount}\n"
        formatted_text += f"TCS Amount      : {tcs_amount}\n\n"

        # Grand Total
        grand_total = get_nested_value(json_data, ['bank_details', 'grand_total'])
        formatted_text += "BANKING INFORMATION:\n"
        formatted_text += "-------------------\n"
        formatted_text += f"Grand Total     : {grand_total}\n\n"

        # Terms and Conditions
        formatted_text += "TERMS AND CONDITIONS:\n"
        formatted_text += "---------------------\n"
        for term in json_data.get('terms_and_conditions', []):
            formatted_text += f"- {term}\n"

        return formatted_text

    except Exception as e:
        raise ValueError(f"Error converting JSON to text: {e}")



import io

import csv
import io
import pandas as pd
from pandas import json_normalize

def dynamic_json_to_csv(json_data, csv_file='output.csv'):
    """
    Converts a nested JSON to CSV file dynamically.
    
    Parameters:
    - json_data: The JSON data to be converted (nested).
    - csv_file: The file path for the output CSV file (default 'output.csv').
    
    Returns:
    - A Pandas DataFrame that represents the flattened JSON.
    """
    # Normalize and flatten the data based on nested structures
    try:
        # Flatten top-level structures
        vendor_details = json_data.get("vendor_details", {})
        invoice_details = json_data.get("invoice_details", {})
        address_details = json_data.get("address_details", {})
        tax_details = json_data.get("tax_details", {})
        bank_details = json_data.get("bank_details", {})
        terms_and_conditions = json_data.get("terms_and_conditions", [])
        
        # Flatten item details into a DataFrame
        item_details = json_data.get("item_details", [])
        df_items = json_normalize(item_details)
        
        # Add the static fields (vendor, invoice, address, etc.) to each row in df_items
        for key, value in vendor_details.items():
            df_items[f'vendor_{key}'] = value
            
        for key, value in invoice_details.items():
            df_items[f'invoice_{key}'] = value
            
        for addr_type, addr_info in address_details.items():
            for key, value in addr_info.items():
                df_items[f'{addr_type}_{key}'] = value
                
        for key, value in tax_details.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    df_items[f'tax_{key}_{sub_key}'] = sub_value
            else:
                df_items[f'tax_{key}'] = value
                
        for key, value in bank_details.items():
            df_items[f'bank_{key}'] = value
            
        df_items['terms_and_conditions'] = '; '.join(terms_and_conditions)
        
        # Save the DataFrame to CSV
        df_items.to_csv(csv_file, index=False)
        print(f"CSV file '{csv_file}' created successfully.")
        
        return df_items
    
    except Exception as e:
        raise ValueError(f"Error processing JSON to CSV: {e}")
    



# Display the DataFrame
#print(df)    


def convert_data_to_text(data):
    # Text Format Conversion
    output_text = io.StringIO()
    
    # Writing Vendor Details to Text
    output_text.write("Vendor Details:\n")
    for key, value in data['vendor_details'].items():
        output_text.write(f"{key}: {value}\n")
    
    # Writing Invoice Details to Text
    output_text.write("\nInvoice Details:\n")
    for key, value in data['invoice_details'].items():
        output_text.write(f"{key}: {value}\n")

    # Writing Address Details to Text
    output_text.write("\nAddress Details:\n")
    for section, details in data['address_details'].items():
        output_text.write(f"{section.title()} Address:\n")
        for key, value in details.items():
            output_text.write(f"  {key}: {value}\n")

    # Writing Tax Details to Text
    output_text.write("\nTax Details:\n")
    for tax_type, details in data['tax_details'].items():
        output_text.write(f"{tax_type.title()}:\n")
        for key, value in details.items():
            output_text.write(f"  {key}: {value}\n")

    # Writing Bank Details to Text
    output_text.write("\nBank Details:\n")
    for key, value in data['bank_details'].items():
        output_text.write(f"{key}: {value}\n")

    # Writing Item Details to Text
    output_text.write("\nItem Details:\n")
    output_text.write("Description | HSN | Quantity | Unit | Amount\n")
    output_text.write("-" * 40 + "\n")
    for item in data['item_details']:
        output_text.write(f"{item['description']} | {item['hsn']} | {item['qty']} | {item['unit']} | {item['amount']}\n")

    # Writing Terms and Conditions to Text
    output_text.write("\nTerms and Conditions:\n")
    for term in data['terms_and_conditions']:
        output_text.write(f"{term}\n")

    text_data = output_text.getvalue()
    output_text.close()

    return text_data

# Example usage for Text
########for excel sheets
import streamlit as st
import pandas as pd
from io import BytesIO

from openpyxl import Workbook

def write_json_to_excel(data):
    """Write JSON data to an Excel file in memory, with each main key in a separate sheet."""
    
    def write_dict_to_sheet(sheet, data_dict):
        """Helper function to write a dictionary to an Excel sheet."""
        for key, value in data_dict.items():
            if isinstance(value, dict):  # If value is another dictionary, write its content
                sheet.append([key])
                for sub_key, sub_value in value.items():
                    sheet.append([sub_key, sub_value])
            else:
                sheet.append([key, value])

    # Create a new Excel workbook
    wb = Workbook()
    # Remove the default sheet
    wb.remove(wb.active)

    # Write each main key as a separate sheet
    for main_key, main_value in data.items():
        ws = wb.create_sheet(title=main_key.upper())
        
        if isinstance(main_value, dict):
            write_dict_to_sheet(ws, main_value)
        elif isinstance(main_value, list):
            # Handle list of dictionaries
            if all(isinstance(item, dict) for item in main_value):
                ws.append(list(main_value[0].keys()))  # Write list of dictionary headers
                for item in main_value:
                    ws.append(list(item.values()))  # Write each dictionary's values
            else:
                for item in main_value:
                    ws.append([item])  # Write list values as rows

    # Save the workbook into a BytesIO object (in-memory)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)  # Set the buffer position to the beginning
    return buffer





# Sample data
data = {
    "vendor_details": {
        "name": "ALPHA COOL PRODUCTS",
        "gst": "24AAICS7449H1ZQ"
    },
    "invoice_details": {
        "invoice_no": "SCP/41590/20-21",
        "date": "19-Feb-21"
    },
    "address_details": {
        "vendor": {
            "name": "ALPHA COOL PRODUCTS",
            "street": "104, The GmmiApamaNHofatam:t Palace, Nr. Digjam Circle, Aerodromel Road",
            "state": "Gujarat"
        },
        "bill_to": {
            "name": "K.K.Brown Papers LLP",
            "street": "127/A,127/B, Devraj Industrial Park, 7/107, w/o. Mohandas Pamnani",
            "state": "Rajasthan"
        },
        "ship_to": {
            "name": "K.K.Brown Papers LLP",
            "street": "PiplajPiranal RoadNr, Kamod Oholadi(Gay@rele) Kishanganj In Front Of Prem Prakash Ashram",
            "state": "Gujarat"
        }
    },
    "tax_details": {
        "igst": {
            "rate": "12%",
            "amount": "20,410.097"
        },
        "tcs_on_sales": {
            "amount": "143.000"
        }
    },
    "bank_details": {
        "grand_total": "1,90,637.000"
    },
    "item_details": [
        {
            "description": "Moon Chips",
            "hsn": "19055",
            "qty": "1",
            "unit": "BOX",
            "amount": "1,374.109"
        },
        {
            "description": "Tomato Moon Chips",
            "hsn": "190550",
            "qty": "1",
            "unit": "BOX",
            "amount": "13,741.090"
        },
        {
            "description": "Ring",
            "hsn": "19055",
            "qty": "1",
            "unit": "BOX",
            "amount": "1,374.109"
        },
        {
            "description": "Pasta",
            "hsn": "190520",
            "qty": "1",
            "unit": "BOX",
            "amount": "5,496.436"
        },
        {
            "description": "Mixi Fryums",
            "hsn": "190250",
            "qty": "1",
            "unit": "BOX",
            "amount": "5,496.436"
        },
        {
            "description": "Pop Corn",
            "hsn": "1905",
            "qty": "1",
            "unit": "BOX",
            "amount": "21,985.744"
        },
        {
            "description": "Sabudana",
            "hsn": "1905",
            "qty": "1",
            "unit": "BOX",
            "amount": "1,832.141"
        },
        {
            "description": "FFI Papad",
            "hsn": "190150",
            "qty": "1",
            "unit": "BOX",
            "amount": "2,748.218"
        },
        {
            "description": "Aeroplane",
            "hsn": "1905",
            "qty": "1",
            "unit": "BOX",
            "amount": "1,374.109"
        },
        {
            "description": "Khichul Papad",
            "hsn": "190155",
            "qty": "1",
            "unit": "BOX",
            "amount": "4,122.327"
        },
        {
            "description": "Noodles",
            "hsn": "1940050",
            "qty": "1",
            "unit": "BOX",
            "amount": "1,09928.718"
        },
        {
            "description": "Soya! Stick",
            "hsn": "210690919",
            "qty": "1",
            "unit": "BOX",
            "amount": "610.715"
        }
    ],
    "terms_and_conditions": [
        "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."
    ]
}

# Image upload feature at the top of both columns
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Create two columns with equal width
col1, col2 = st.columns(2, gap="medium")

# Column 1: Display the uploaded image
with col1:
    st.write('*Uploaded Image*')
    if uploaded_file is not None:
        st.image(uploaded_file, width=450)
    else:
        st.write("No image uploaded.")

# Column 2: Invoice details with tabs
with col2:
    st.write('*Invoice Details*')

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["TEXT", "EXCEL", "JSON "])

    # Content for Tab 1 with a fixed-height scrollable container
    with tab3:
        with st.container(height=550):
            #st.markdown(f'<div style="height: 450px; overflow-y: auto; padding: 10px; border: 1px solid black;">', unsafe_allow_html=True)
            st.json(data)
            st.markdown('</div>', unsafe_allow_html=True)
#############################################################            
    with tab2:
        excel_buffer = write_json_to_excel(data)
        df_dict = pd.read_excel(excel_buffer, sheet_name=None)
        with st.container(height=550):
            for sheet_name, df in df_dict.items():
                st.subheader(f"Sheet: {sheet_name}")
            
                with st.container():              
                   st.dataframe(df)          
        st.download_button(
            label="Download Excel File",
            data=excel_buffer,
            file_name="data.xlsx",  # Name for the downloaded file
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # Excel MIME type
        )    
    # Content for Tab 2
    #text_output = convert_data_to_text(data)
###################################################################    
    with tab1:
        formatted_text = json_to_text(data)
        with st.container(height=550):

            st.text(formatted_text)
            ###################################################################
    

st.write("*Messages:*")
messages = ["1. Text extracted", "2. Parsing", "3. Data format"]
for message in messages:
    st.write(message)




