import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
import os

st.set_page_config(layout="wide")
st.title("Professional University Question Paper Generator (A5)")

# ---------------------------
# HEADER INPUTS
# ---------------------------
college_name = st.text_input("College Name")
department = st.text_input("Department Name")
exam_no = st.selectbox("Internal Exam No", ["1", "2", "3"])
course_code = st.text_input("Subject Code")
course_name = st.text_input("Subject Name")

st.markdown("---")

TOTAL_MAX = 50

# ---------------------------
# SECTION BUILDER
# ---------------------------
def section_builder(section_name):
    st.header(section_name)

    choice_mode = st.radio(
        f"{section_name} Answer Mode",
        ["Answer All Questions", "Answer Any (Choice Based)"],
        key=section_name+"choice"
    )

    num_questions = st.number_input(
        f"Number of Questions in {section_name}",
        min_value=0,
        step=1,
        key=section_name
    )

    section_data = []
    section_total = 0

    for i in range(int(num_questions)):
        st.subheader(f"Question {i+1}")

        num_sub = st.number_input(
            "Number of Subsections",
            min_value=1,
            step=1,
            key=section_name+"sub"+str(i)
        )

        subs = []
        for j in range(int(num_sub)):
            col1, col2 = st.columns([4,1])
            text = col1.text_area(f"({chr(97+j)}) Question Text",
                                 key=section_name+str(i)+str(j))
            mark = col2.number_input("Marks",
                                     min_value=1,
                                     step=1,
                                     key=section_name+"m"+str(i)+str(j))
            section_total += mark
            subs.append((text, mark))

        section_data.append(subs)

    return choice_mode, section_data, section_total

# ---------------------------
# BUILD SECTIONS
# ---------------------------
partA = section_builder("PART-A")
partB = section_builder("PART-B")
partC = section_builder("PART-C")

grand_total = partA[2] + partB[2] + partC[2]

st.markdown("---")
st.subheader(f"Total Marks Entered: {grand_total} / 50")

if grand_total != TOTAL_MAX:
    st.error("Total Marks must be exactly 50")
else:
    st.success("Total Marks Valid (50)")

# ---------------------------
# PDF GENERATOR
# ---------------------------
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

    college_style = ParagraphStyle(
        'college',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=16
    )

    dept_style = ParagraphStyle(
        'dept',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=14
    )

    # -----------------------
    # HEADER TABLE
    # -----------------------
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
    else:
        logo = Paragraph("LOGO", bold)

    right_header = f"""
    <b>Internal Exam:</b> {exam_no}<br/>
    <b>Subject Code:</b> {course_code}<br/>
    <b>Subject Name:</b> {course_name}<br/>
    <b>Duration:</b> 90 Minutes<br/>
    <b>Maximum Marks:</b> 50
    """

    header_table = Table(
        [[logo, Paragraph(right_header, normal)]],
        colWidths=[2.5*inch, 2.5*inch]
    )

    header_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    elements.append(Paragraph(college_name, college_style))
    elements.append(Paragraph(department, dept_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # -----------------------
    # WRITE SECTIONS
    # -----------------------
    q_number = 1

    def write_section(title, data):
        nonlocal q_number
        mode, questions, _ = data

        elements.append(Paragraph(f"<b>{title}</b>", bold))
        elements.append(Spacer(1, 0.2*inch))

        if mode == "Answer All Questions":
            elements.append(Paragraph("Answer all the questions.", normal))
        else:
            elements.append(Paragraph("Answer the questions based on choice.", normal))

        elements.append(Spacer(1, 0.2*inch))

        for subs in questions:
            elements.append(Paragraph(f"{q_number}.", normal))
            elements.append(Spacer(1, 0.1*inch))

            for sub in subs:
                text, mark = sub
                elements.append(
                    Paragraph(f"({chr(97+subs.index(sub))}) {text} ({mark} Marks)", normal)
                )
                elements.append(Spacer(1, 0.1*inch))

            elements.append(Spacer(1, 0.2*inch))
            q_number += 1

    write_section("PART-A", partA)
    write_section("PART-B", partB)
    write_section("PART-C", partC)

    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("<b>All the Best</b>", bold))

    # Page Number
    def add_page_number(canvas, doc):
        canvas.setFont("Times-Roman", 12)
        canvas.drawRightString(A5[0]-20, 20, f"Page {doc.page}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer

# ---------------------------
# DOWNLOAD BUTTON
# ---------------------------
if st.button("Generate Professional Question Paper"):
    if grand_total == 50:
        pdf = generate_pdf()
        filename = f"{course_code}_{course_name}.pdf".replace(" ", "_")
        st.download_button(
            "Download PDF",
            pdf,
            file_name=filename,
            mime="application/pdf"
        )
    else:
        st.error("Cannot generate PDF. Total marks must be 50.")
