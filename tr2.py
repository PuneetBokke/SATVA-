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

import streamlit as st
from PIL import Image

# Set the layout to wide
st.set_page_config(layout="wide")

# Title of the app
st.title("S-A-T-V-A__1.0")

# Image upload feature at the top of both columns
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Create two columns with equal width
col1, col2 = st.columns(2, gap="large")

# Column 1: Display the uploaded image
with col1:
    st.write('**uploaded image**')
    if uploaded_file is not None:
        st.image(uploaded_file, width=450)
    else:
        st.write("No image uploaded.")



# Column 2: Invoice details with tabs
with col2:
    st.write('**Invoice Details**')

    # Create tabs
    tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

    # Set a fixed height for the tabs
    tab_height = 500  # Adjust as needed

    # Content for Tab 1 with a fixed-height scrollable container
    with tab1:
        with st.container(height=550):
            #st.markdown(f'<div style="height: {tab_height}px; overflow-y: auto; padding: 10px;">', unsafe_allow_html=True)
            st.json(data)
            #for i in range(1, 21):
             #   st.write(f"Line {i}: This is some sample content to demonstrate scrolling.")
            #st.markdown('</div>', unsafe_allow_html=True)

    # Content for Tab 2
    with tab2:
        # Create 2 rows of 3 columns each
        row1 = st.columns(3)
        row2 = st.columns(3)

        # Add containers to each column with unique content
        with row1[0].container(height=250):
            st.markdown("## Vendor Details")
            st.write(f"**Name:** {data['vendor_details']['name']}")
            st.write(f"**GST:** {data['vendor_details']['gst']}")          
            st.write("Unique content for Container 1")

        with row1[1].container(height=200):
            st.write("Unique content for Container 2")

        with row1[2].container(height=200):
            st.write("Unique content for Container 3")

        with row2[0].container(height=200):
            st.write("Unique content for Container 4")

        with row2[1].container(height=200):
            st.write("Unique content for Container 5")

        with row2[2].container(height=200):
            st.write("Unique content for Container 6")

# To run the app, save this code in a file called app.py and run the following command:
# streamlit run app.py
st.write("**Messages:**")
messages = ["1. Text extracted", "2. Parsing","3.Data format"]
for message in messages:
    st.write(message)