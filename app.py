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
        ["Answer All Questions", "Choice Based"],
        key=section_name+"mode"
    )

    num_questions = st.number_input(
        f"Total Questions in {section_name}",
        min_value=0,
        step=1,
        key=section_name+"num"
    )

    required_answers = num_questions

    if answer_mode == "Choice Based" and num_questions > 0:
        required_answers = st.number_input(
            f"How many questions must be answered?",
            min_value=1,
            max_value=num_questions,
            step=1,
            key=section_name+"required"
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

            text = col1.text_area(
                f"({chr(97+j)}) Question Text",
                key=section_name+str(i)+str(j)
            )

            mark = col2.number_input(
                "Marks",
                min_value=1,
                step=1,
                key=section_name+"mark"+str(i)+str(j)
            )

            section_total += mark   # ✅ CORRECT
            subs.append((text, mark))

        section_data.append(subs)

    return answer_mode, num_questions, required_answers, section_data, section_total    
partA = section_builder("PART-A")
partB = section_builder("PART-B")
partC = section_builder("PART-C")

grand_total = partA[4] + partB[4] + partC[4]

st.subheader(f"Total Marks Entered: {grand_total} / 50")

if grand_total != 50:
    st.error("Total Marks must be exactly 50")
else:
    st.success("Total Marks Valid (50)")

# -----------------------
# PDF GENERATOR
# -----------------------
def generate_pdf():

    from weasyprint import HTML
    from io import BytesIO

    q_number = 1
    html_parts = []

    # ---------- HEADER ----------
    html_parts.append(f"""
    <html>
    <head>
    <style>
    @page {{ size: A5; margin: 20mm; }}
    body {{ font-family: 'Times New Roman'; font-size: 12pt; }}
    h1 {{ font-size: 16pt; font-weight: bold; text-align:center; }}
    h2 {{ font-size: 14pt; font-weight: bold; text-align:center; }}
    h3 {{ font-weight: bold; margin-top:20px; }}
    .marks {{ float:right; font-weight:bold; }}
    .footer {{ text-align:center; margin-top:30px; font-weight:bold; }}
    </style>
    </head>
    <body>
    """)

    html_parts.append(f"<h1>{college_name}</h1>")
    html_parts.append(f"<h2>{department}</h2>")

    html_parts.append(f"""
    <p>
    <b>Internal Exam:</b> {exam_no}<br>
    <b>Subject Code:</b> {course_code}<br>
    <b>Subject Name:</b> {course_name}<br>
    <b>Duration:</b> 90 Minutes<br>
    <b>Maximum Marks:</b> 50
    </p>
    <hr>
    """)

    # ---------- SECTION BUILDER ----------
    def build_section(title, data):
        nonlocal q_number

        mode, total_q, required_q, questions, _ = data

        html_parts.append(f"<h3>{title}</h3>")

        if mode == "Answer All Questions":
            html_parts.append("<p><b>Answer ALL the questions:</b></p>")
        else:
            html_parts.append(f"<p><b>Answer any {required_q} questions:</b></p>")

        for q_html, marks in questions:
            html_parts.append(f"""
            <p>
            <b>{q_number}.</b> {q_html}
            <span class="marks">({marks} Marks)</span>
            </p>
            """)
            q_number += 1

    build_section("PART-A", partA)
    build_section("PART-B", partB)
    build_section("PART-C", partC)

    html_parts.append("<div class='footer'>All the Best</div>")
    html_parts.append("</body></html>")

    final_html = "".join(html_parts)

    pdf = HTML(string=final_html).write_pdf()
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
