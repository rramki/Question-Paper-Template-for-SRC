import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(layout="wide")

st.title("Internal Examination Question Paper Generator")

# ----------------------------
# Basic Details
# ----------------------------
college_name = st.text_input("College Name")
department = st.text_input("Department Name")
exam_no = st.selectbox("Internal Exam Number", ["1", "2", "3"])
course_code = st.text_input("Course Code")
course_name = st.text_input("Course Name")

st.markdown("---")

# ----------------------------
# Section Builder Function
# ----------------------------
def section_builder(section_name):
    st.subheader(f"{section_name}")
    total_marks = st.number_input(f"{section_name} Total Marks", min_value=0, step=1)
    choice_type = st.selectbox(
        f"{section_name} Choice Type",
        ["Answer All", "Answer Any"],
        key=section_name
    )

    num_questions = st.number_input(
        f"Number of Questions in {section_name}",
        min_value=0,
        step=1,
        key=section_name+"num"
    )

    questions = []
    for i in range(int(num_questions)):
        col1, col2 = st.columns([4,1])
        q = col1.text_area(f"{section_name} Question {i+1}", key=section_name+str(i))
        m = col2.number_input("Marks", min_value=0, step=1, key=section_name+"m"+str(i))
        questions.append((q, m))

    return total_marks, choice_type, questions

# ----------------------------
# Sections
# ----------------------------
st.header("Sections")

partA = section_builder("PART-A")
st.markdown("---")
partB = section_builder("PART-B")
st.markdown("---")
partC = section_builder("PART-C")

# ----------------------------
# PDF Generator
# ----------------------------
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A3)
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

    # Header
    elements.append(Paragraph(f"<b>{college_name}</b>", bold))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>Department of {department}</b>", bold))
    elements.append(Spacer(1, 0.3*inch))

    exam_data = [
        ["Internal Exam No:", exam_no, "Course Code:", course_code],
        ["Course Name:", course_name, "Duration:", "90 Minutes"],
        ["Maximum Marks:", "50", "", ""]
    ]

    table = Table(exam_data, colWidths=[2*inch, 3*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('FONTNAME',(0,0),(-1,-1),'Times-Roman'),
        ('FONTSIZE',(0,0),(-1,-1),12),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))

    def add_section(title, data):
        total, choice, questions = data
        elements.append(Paragraph(f"<b>{title} (Total Marks: {total})</b>", bold))
        elements.append(Spacer(1, 0.2*inch))

        if choice == "Answer All":
            elements.append(Paragraph("Answer all questions.", normal))
        else:
            elements.append(Paragraph("Answer any specified number of questions.", normal))

        elements.append(Spacer(1, 0.2*inch))

        for i, (q, m) in enumerate(questions):
            elements.append(Paragraph(f"{i+1}. {q} ({m} Marks)", normal))
            elements.append(Spacer(1, 0.2*inch))

        elements.append(Spacer(1, 0.4*inch))

    add_section("PART-A", partA)
    add_section("PART-B", partB)
    add_section("PART-C", partC)

    def add_page_number(canvas, doc):
        canvas.setFont("Times-Roman", 12)
        canvas.drawRightString(A3[0]-40, 20, f"Page {doc.page}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    return buffer

# ----------------------------
# Download Button
# ----------------------------
if st.button("Generate Question Paper"):
    pdf_file = generate_pdf()
    filename = f"{course_code}_{course_name}.pdf".replace(" ", "_")

    st.download_button(
        label="Download PDF",
        data=pdf_file,
        file_name=filename,
        mime="application/pdf"
    )
