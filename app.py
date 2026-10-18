import streamlit as st
import pandas as pd
from fpdf import FPDF
from pypdf import PdfWriter, PdfReader
from PIL import Image
import io
import tempfile
import os

# Page Setup
st.set_page_config(page_title="Employee Dossier Generator", page_icon="📄", layout="wide")

st.title("📄 Employee Profile & Document PDF Generator")
st.write("Excel se employee data select karein, unke identity documents upload karein aur ek single PDF download karein.")

# Step 1: Upload Excel File
st.subheader("1. Employee Data Excel Upload Karein")
excel_file = st.file_uploader("Upload Excel File (.xlsx or .xls)", type=["xlsx", "xls"])

if excel_file is not None:
    try:
        df = pd.read_excel(excel_file)
        st.success("Excel file successfully load ho gayi!")
        
        with st.expander("Poora Excel Data Dekhein"):
            st.dataframe(df)

        # Step 2: Select Employee
        st.subheader("2. Employee Select Karein")
        columns = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            search_col = st.selectbox("Kis column se Employee select karna hai? (Jaise Name ya Emp ID)", columns)
        with col2:
            selected_val = st.selectbox(f"Select {search_col}", df[search_col].astype(str).unique())

        # Filter selected employee row
        emp_row = df[df[search_col].astype(str) == selected_val].iloc[0]

        st.markdown("#### Selected Employee Details:")
        emp_df = pd.DataFrame(emp_row).reset_index()
        emp_df.columns = ["Field", "Value"]
        st.table(emp_df)

        # Step 3: Upload Identity Documents
        st.subheader("3. Identity Documents Upload Karein")
        st.info("Aap multiple files select kar sakte hain (JPG, PNG, ya PDF format mein - Jaise Aadhar, PAN, Voter ID).")
        uploaded_docs = st.file_uploader(
            "Upload ID Proofs (Images or PDFs)", 
            type=["png", "jpg", "jpeg", "pdf"], 
            accept_multiple_files=True
        )

        # Function to create the final merged PDF
        def generate_employee_pdf(emp_series, docs):
            # 1. Create First Page with Employee Details using FPDF
            pdf = FPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", style="B", size=18)
            pdf.cell(0, 12, "EMPLOYEE INFORMATION DOSSIER", ln=True, align="C")
            pdf.ln(8)

            # Employee Details Table
            pdf.set_font("Arial", size=11)
            for field, val in emp_series.items():
                # Clean text to avoid encoding issues in standard FPDF
                field_str = str(field).encode('latin-1', 'replace').decode('latin-1')
                val_str = str(val).encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font("Arial", style="B", size=11)
                pdf.cell(65, 10, f" {field_str}", border=1)
                
                pdf.set_font("Arial", style="", size=11)
                pdf.cell(125, 10, f" {val_str}", border=1, ln=True)

            # If image documents are uploaded, add them to FPDF pages
            pdf_docs_to_merge = []

            if docs:
                for doc in docs:
                    file_ext = doc.name.split(".")[-1].lower()
                    
                    if file_ext in ["jpg", "jpeg", "png"]:
                        pdf.add_page()
                        pdf.set_font("Arial", style="B", size=13)
                        clean_name = doc.name.encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(0, 10, f"Attached Document: {clean_name}", ln=True)
                        pdf.ln(4)

                        # Save image to a temporary file for FPDF
                        img = Image.open(doc)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                            
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                            img.save(tmp_img.name, format="JPEG")
                            tmp_img_path = tmp_img.name

                        # Fit image nicely on A4 page (max width ~180mm)
                        pdf.image(tmp_img_path, x=15, y=30, w=180)
                        os.remove(tmp_img_path)

                    elif file_ext == "pdf":
                        # Save PDF files to merge later using pypdf
                        pdf_docs_to_merge.append(doc)

            # Save the FPDF output into memory
            base_pdf_bytes = pdf.output(dest="S").encode("latin-1")

            # 2. Merge any uploaded PDF documents using pypdf
            writer = PdfWriter()
            base_reader = PdfReader(io.BytesIO(base_pdf_bytes))
            for page in base_reader.pages:
                writer.add_page(page)

            for pdf_doc in pdf_docs_to_merge:
                pdf_doc.seek(0)
                doc_reader = PdfReader(pdf_doc)
                for page in doc_reader.pages:
                    writer.add_page(page)

            final_output = io.BytesIO()
            writer.write(final_output)
            final_output.seek(0)
            return final_output

        # Step 4: Generate & Download Button
        st.subheader("4. PDF Generate Aur Download Karein")
        if st.button("🚀 Generate Combined PDF", type="primary"):
            with st.spinner("PDF taiyaar ho rahi hai..."):
                final_pdf = generate_employee_pdf(emp_row, uploaded_docs)
                
                # Safe file name
                safe_name = "".join(x for x in str(selected_val) if x.isalnum() or x in (" ", "_", "-")).strip()
                file_name = f"Employee_{safe_name}_Document.pdf"
                
                st.success("✅ PDF successfully ban gayi hai! Niche button se download karein:")
                st.download_button(
                    label="📥 Download Employee PDF",
                    data=final_pdf,
                    file_name=file_name,
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"File read karne mein error aaya: {e}")
