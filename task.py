import streamlit as st
import pandas as pd
from tr import *
import time

st.set_page_config(
    page_title="SATVA",
    page_icon="👽",
    layout="wide",
    initial_sidebar_state="auto",
)

def home_page():
    st.title("Satva Document Extraction")
    st.write("Welcome to the Satva page.")

    # Read the contents of the text file
    with open("blog_post.txt", "r") as file:
        blog_content = file.read()

    # Display the blog content
    st.write("### INTODUCTION.......")
    st.write(blog_content)

    # Display the image
    st.write("### Image")
    st.image("satva_home.png")

    
def upload_page ():
    st.title("Upload Page")
    uploaded_files = st.file_uploader("Choose multiple images", type=["jpg", "png"], accept_multiple_files=True)

    if uploaded_files:
        # Create a container to hold the images
        with st.container(height=100):
            # Create columns to display the images horizontally
            cols = st.columns(len(uploaded_files))
            for i, file in enumerate(uploaded_files):
                with cols[i]:
                    st.image(file, caption=uploaded_files[i].name)

        # Invoice details with tabs
        st.write('*Invoice Details*')

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["TEXT", "EXCEL", "JSON ","logs"])

        # Content for Tab 3 with a fixed-height scrollable container
        with tab3:
            with st.container(height=550):
                st.json(data)
                
        # Content for Tab 2
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
        
        # Content for Tab 1
        with tab1:
            formatted_text = json_to_text(data)
            with st.container(height=550):
                st.text(formatted_text)

        with tab4:
            st.spinner()
            st.write("text extraction ")            
import streamlit as st
clean_numerical_values_in_excel('working_data.xlsx', 'output_file.xlsx')


import warnings
warnings.filterwarnings("ignore")

def task_page():
    if st.button('Show Dashboard'):
        #clean_numerical_values_in_excel('working_data.xlsx', 'output_file.xlsx')
        
        plot_numerical_values('output_file.xlsx')
        
    # Return the invoice details
    

def settings_page():
    st.title("Settings Page")
    st.write("Settings page content.")

options = {
    "Home": home_page,
    "Import-Export": upload_page,
    "Dashboard": task_page,
    "Settings": settings_page
}

with st.sidebar:
    selected = option_menu("Satva the Extractor", list(options.keys()), 
        icons=['house', 'cloud-upload', "list-task", 'gear'], menu_icon="cast", default_index=1)

options[selected]()