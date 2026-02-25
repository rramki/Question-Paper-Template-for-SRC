import streamlit as st
from streamlit_quill import st_quill
from weasyprint import HTML
from io import BytesIO
import base64

st.set_page_config(layout="wide")
st.title("Professional University Question Paper Generator (A5)")

TOTAL_MAX = 50

# -----------------------
# HEADER
# -----------------------
college_name = st.text_input("College Name")
department = st.text_input("Department Name")
exam_no = st.selectbox("Internal Exam No", ["1", "2", "3"])
course_code = st.text_input("Subject Code")
course_name = st.text_input("Subject Name")

st.markdown("---")

# -----------------------
# SECTION BUILDER
# -----------------------
def section_builder(section_name):
    st.header(section_name)

    answer_mode = st.radio(
        f"{section_name} Mode",
        ["Answer All Questions", "Answer Choice Based Questions"],
        key=section_name+"mode"
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

        question_html = st_quill(
            placeholder="Paste text, images, or equations here...",
            key=section_name+str(i)
        )

        marks = st.number_input(
            "Marks for this question",
            min_value=1,
            step=1,
            key=section_name+"m"+str(i)
        )

        section_total += marks
        section_data.append((question_html, marks))

    return answer_mode, section_data, section_total

partA = section_builder("PART-A")
partB = section_builder("PART-B")
partC = section_builder("PART-C")

grand_total = partA[2] + partB[2] + partC[2]

st.subheader(f"Total Marks: {grand_total} / 50")

if grand_total != TOTAL_MAX:
    st.error("Total must equal 50")
else:
    st.success("Total Valid")

# -----------------------
# PDF GENERATOR
# -----------------------
def generate_pdf():

    html_content = f"""
    <html>
    <head>
    <style>
    @page {{ size: A5; margin: 20mm; }}
    body {{ font-family: 'Times New Roman'; font-size: 12pt; }}
    h1 {{ font-size: 16pt; font-weight: bold; }}
    h2 {{ font-size: 14pt; font-weight: bold; }}
    .header {{ display: flex; justify-content: space-between; }}
    .footer {{ text-align: center; margin-top: 30px; font-weight: bold; }}
    </style>

    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    <body>

    <h1>{college_name}</h1>
    <h2>{department}</h2>

    <div class="header">
        <div>
            <b>Internal Exam:</b> {exam_no}<br>
            <b>Subject Code:</b> {course_code}<br>
            <b>Subject Name:</b> {course_name}
        </div>
        <div>
            <b>Duration:</b> 90 Minutes<br>
            <b>Maximum Marks:</b> 50
        </div>
    </div>
    <hr>
    """

    q_number = 1

    def build_section(title, data):
        nonlocal html_content, q_number
        mode, questions, _ = data

        html_content += f"<h3>{title}</h3>"

        if "All" in mode:
            html_content += "<p><b>Answer all questions.</b></p>"
        else:
            html_content += "<p><b>Answer choice based questions.</b></p>"

        for q_html, marks in questions:
            html_content += f"""
            <p><b>{q_number}.</b> {q_html}
            <span style="float:right;"><b>({marks} Marks)</b></span></p>
            """
            q_number += 1

    build_section("PART-A", partA)
    build_section("PART-B", partB)
    build_section("PART-C", partC)

    html_content += """
    <div class="footer">All the Best</div>
    </body></html>
    """

    pdf = HTML(string=html_content).write_pdf()
    return BytesIO(pdf)

# -----------------------
# DOWNLOAD
# -----------------------
if st.button("Generate Professional PDF"):
    if grand_total == 50:
        pdf = generate_pdf()
        filename = f"{course_code}_{course_name}.pdf".replace(" ", "_")
        st.download_button("Download PDF", pdf, filename, "application/pdf")
    else:
        st.error("Total must equal 50")
