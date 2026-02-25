import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

st.set_page_config(layout="wide")
st.title("University Internal Examination Paper Generator (A5)")

# -----------------------------
# Header Inputs
# -----------------------------
department = st.text_input("Department Name")
exam_no = st.selectbox("Internal Exam Number", ["1", "2", "3"])
course_code = st.text_input("Course Code")
course_name = st.text_input("Course Name")

st.markdown("---")

# -----------------------------
# Section Builder with Subsections
# -----------------------------
def section_builder(section_name):
    st.header(section_name)

    num_questions = st.number_input(
        f"Number of Questions in {section_name}",
        min_value=0,
        step=1,
        key=section_name
    )

    section_data = []

    for i in range(int(num_questions)):
        st.subheader(f"Question {i+1}")
        has_choice = st.checkbox("This question has choice?", key=section_name+"choice"+str(i))
        num_sub = st.number_input("Number of Subsections", min_value=1, step=1,
                                  key=section_name+"sub"+str(i))

        subs = []
        for j in range(int(num_sub)):
            col1, col2 = st.columns([4,1])
            text = col1.text_area(f"Subsection ({chr(97+j)})", key=section_name+str(i)+str(j))
            mark = col2.number_input("Marks", min_value=0, step=1,
                                     key=section_name+"m"+str(i)+str(j))
            subs.append((text, mark))

        section_data.append((has_choice, subs))

    return section_data

partA = section_builder("PART-A")
partB = section_builder("PART-B")
partC = section_builder("PART-C")

# -----------------------------
# PDF Generator
# -----------------------------
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5)
    elements = []

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        'normal',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12
    )

    bold = ParagraphStyle(
        'bold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12
    )

    # -------------------------
    # Header Table
    # -------------------------
    logo = Image("logo.png", width=1*inch, height=1*inch)

    header_right = f"""
    <b>Department:</b> {department}<br/>
    <b>Internal Exam:</b> {exam_no}<br/>
    <b>Course Code:</b> {course_code}<br/>
    <b>Course Name:</b> {course_name}<br/>
    <b>Duration:</b> 90 Minutes<br/>
    <b>Maximum Marks:</b> 50
    """

    header_table = Table([
        [logo, Paragraph(header_right, normal)]
    ], colWidths=[1.2*inch, 4.5*inch])

    header_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # -------------------------
    # Section Writer
    # -------------------------
    def write_section(title, data):
        elements.append(Paragraph(f"<b>{title}</b>", bold))
        elements.append(Spacer(1, 0.2*inch))

        for i, (choice, subs) in enumerate(data):
            q_text = f"{i+1}."
            if choice:
                q_text += " (OR Choice Available)"
            elements.append(Paragraph(q_text, normal))
            elements.append(Spacer(1, 0.1*inch))

            for j, (text, mark) in enumerate(subs):
                elements.append(
                    Paragraph(f"({chr(97+j)}) {text} ({mark} Marks)", normal)
                )
                elements.append(Spacer(1, 0.1*inch))

            elements.append(Spacer(1, 0.2*inch))

    write_section("PART-A", partA)
    write_section("PART-B", partB)
    write_section("PART-C", partC)

    # -------------------------
    # Page Number
    # -------------------------
    def add_page_number(canvas, doc):
        canvas.setFont("Times-Roman", 12)
        canvas.drawRightString(A5[0]-20, 20, f"Page {doc.page}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer

# -----------------------------
# Download Button
# -----------------------------
if st.button("Generate Question Paper"):
    pdf = generate_pdf()
    filename = f"{course_code}_{course_name}.pdf".replace(" ", "_")

    st.download_button(
        "Download PDF",
        pdf,
        file_name=filename,
        mime="application/pdf"
    )
