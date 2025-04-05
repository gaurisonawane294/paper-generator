import streamlit as st
import json
import PyPDF2
import io
from model import get_output
import base64
from datetime import datetime
import time
import re
from history_manager import HistoryManager

# Set wide layout and custom theme
st.set_page_config(
    page_title="Advanced Question Paper Generator",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Advanced Question Paper Generator\nCreate professional question papers with ease."
    }
)

# Custom CSS
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #34495e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        height: 3.5em;
        margin-top: 1em;
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Card styling */
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 1rem 0;
        border: 1px solid #e1e8ed;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
        padding: 0.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        background-color: transparent;
        border: none;
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Form styling */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #e1e8ed;
    }
    
    .stSelectbox>div>div>div {
        border-radius: 5px;
        border: 1px solid #e1e8ed;
    }
    
    /* Message styling */
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 5px;
        margin: 1rem 0;
        border-left: 4px solid #dc3545;
    }
    
    /* History section styling */
    .history-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e1e8ed;
    }
    
    /* PDF styling improvements */
    .pdf-content {
        font-family: "Times New Roman", Times, serif;
        line-height: 1.6;
    }
    
    .pdf-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .pdf-section {
        margin-top: 2rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def load_templates():
    try:
        with open("templates.json", "r") as f:
            templates = json.load(f)
    except FileNotFoundError:
        templates = {}
    return templates


def save_templates(templates):
    with open("templates.json", "w") as f:
        json.dump(templates, f, indent=4)


def extract_text_from_pdf(pdf_file):
    try:
        from PyPDF2 import PdfFileReader
        pdf_reader = PdfFileReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extractText()
        
        # Clean up the extracted text
        text = text.strip()
        text = ' '.join(text.split())  # Remove extra whitespace
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""


def generate_prompt(num_mcq, num_3_marks, num_5_marks, difficulty_level, syllabus, subject="", topic="", with_answers=True):
    requirements = {
        "syllabus": syllabus,
        "subject": subject,
        "topic": topic,
        "num_mcq": num_mcq,
        "num_3_marks": num_3_marks,
        "num_5_marks": num_5_marks,
        "difficulty": difficulty_level,
        "with_answers": with_answers
    }
    return requirements


def convert_to_pdf(content):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from io import BytesIO
    import re
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles with better formatting
    styles = getSampleStyleSheet()
    
    custom_styles = {
        'Title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ),
        'Header': ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1,
            textColor=HexColor('#34495e'),
            fontName='Helvetica'
        ),
        'Section': ParagraphStyle(
            'CustomSection',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=20,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ),
        'Question': ParagraphStyle(
            'CustomQuestion',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            spaceBefore=12,
            spaceAfter=12,
            leftIndent=20,
            fontName='Times-Roman'
        ),
        'Option': ParagraphStyle(
            'CustomOption',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            leftIndent=40,
            spaceBefore=2,
            spaceAfter=2,
            fontName='Times-Roman'
        ),
        'Answer': ParagraphStyle(
            'CustomAnswer',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            leftIndent=40,
            spaceBefore=6,
            spaceAfter=12,
            fontName='Times-Roman'
        )
    }
    
    def clean_html(text):
        # Convert <b> tags to reportlab bold
        text = text.replace('<b>', '<b>')
        text = text.replace('</b>', '</b>')
        # Handle other HTML-like formatting
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('**', '')
        return text
    
    def format_mcq(text):
        # Format MCQ options to look better
        text = re.sub(r'\b([a-d])\)', r'\1) ', text)  # Add space after option letters
        text = re.sub(r'\s{2,}', ' ', text)  # Remove extra spaces
        return text
    
    story = []
    
    # Split content into lines and process
    lines = content.split('\n')
    in_mcq_section = False
    
    for line in lines:
        if not line.strip():
            continue
        
        line = clean_html(line)
        
        if 'Question Paper' in line or 'Answer Key' in line:
            story.append(Paragraph(line, custom_styles['Title']))
            story.append(Spacer(1, 20))
        elif 'Section' in line:
            in_mcq_section = 'Multiple Choice' in line
            story.append(Paragraph(line, custom_styles['Section']))
            story.append(Spacer(1, 10))
        elif line.startswith('Time:') or line.startswith('Max. Marks:') or line.startswith('Instructions:'):
            story.append(Paragraph(line, custom_styles['Header']))
        elif line.strip().startswith(('Q', '1.', '2.', '3.', '4.', '5.')):
            if in_mcq_section:
                line = format_mcq(line)
            story.append(Paragraph(line, custom_styles['Question']))
        else:
            story.append(Paragraph(line, custom_styles['Answer']))
            story.append(Spacer(1, 6))
    
    try:
        doc.build(story)
    except Exception as e:
        st.error(f"Error building PDF: {str(e)}")
        # Fallback to simpler formatting
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = [Paragraph(line, styles['Normal']) for line in content.split('\n') if line.strip()]
        doc.build(story)
    
    buffer.seek(0)
    return buffer


def generate_download_buttons(questions, answers, key_prefix=""):
    col1, col2, col3 = st.columns(3)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with col1:
        # Add unique key for each download button
        st.download_button(
            "📄 Download Question Paper",
            convert_to_pdf(questions).getvalue(),  # Convert to PDF
            f"question_paper_{timestamp}.pdf",
            mime="application/pdf",
            key=f"{key_prefix}_question_paper"
        )

    with col2:
        if answers:
            st.download_button(
                "✅ Download Answer Key",
                convert_to_pdf(answers).getvalue(),  # Convert to PDF
                f"answer_key_{timestamp}.pdf",
                mime="application/pdf",
                key=f"{key_prefix}_answer_key"
            )
    
    with col3:
        if st.button("🔄 Reset", key=f"{key_prefix}_reset"):
            # Only clear form inputs, not generated content
            for key in list(st.session_state.keys()):
                if key not in ['generated_content']:
                    st.session_state.pop(key)
            st.experimental_rerun()


def store_in_history(questions, answers, metadata):
    history_manager = HistoryManager()
    history_manager.add_paper(questions, answers, metadata)


def show_history():
    if 'paper_history' in st.session_state and st.session_state.paper_history:
        st.markdown("---")
        st.markdown("### Generation History")
        
        for i, paper in enumerate(reversed(st.session_state.paper_history)):
            with st.expander(f"Paper {i+1} - Generated on {paper['timestamp']}"):
                tab1, tab2 = st.tabs(["📝 Question Paper", "✅ Answer Key"])
                
                with tab1:
                    st.markdown(paper['questions'])
                    st.download_button(
                        "📄 Download Question Paper",
                        convert_to_pdf(paper['questions']).getvalue(),
                        f"question_paper_{paper['timestamp']}.pdf",
                        mime="application/pdf",
                        key=f"history_{i}_question"
                    )
                
                if paper['answers']:
                    with tab2:
                        st.markdown(paper['answers'])
                        st.download_button(
                            "✅ Download Answer Key",
                            convert_to_pdf(paper['answers']).getvalue(),
                            f"answer_key_{paper['timestamp']}.pdf",
                            mime="application/pdf",
                            key=f"history_{i}_answer"
                        )


def main():
    # Initialize session state for storing generated content
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = None
    
    # Initialize variables
    subject = ""
    selected_topic = ""
    output = None

    # Header with custom styling
    st.markdown("""
        <h1 style='text-align: center; color: #1f77b4;'>
            Advanced Question Paper Generator
        </h1>
        <p style='text-align: center; font-size: 1.2em; color: #666;'>
            Generate professional question papers with automated answer keys
        </p>
        <hr>
    """, unsafe_allow_html=True)

    # Load templates
    templates = load_templates()
    
    # Sidebar for template selection
    with st.sidebar:
        st.header("Templates")
        selected_template = st.selectbox("Select Template", ["Custom"] + list(templates.keys()), index=0)
        
        if st.button("Save Current as Template"):
            template_name = st.text_input("Template Name")
            if template_name:
                # Code to save current settings as template
                pass

    # Main content area
    st.header("Syllabus Input")
    
    input_method = st.radio("Select syllabus input method:", ["Use predefined subjects", "Paste syllabus text", "Upload syllabus PDF"])
    
    syllabus_content = ""
    
    if input_method == "Use predefined subjects":
        subjects = {
            'Data Structures and Algorithms': ['Data Structure', 'Searching & Sorting', 'Tree Traversal'],
            'Operating Systems': ['Scheduling', 'Memory Management', 'Process & Threads'],
            'Database Management System': ['Transaction & Concurrency Control', 'Normalization', 'File Organization']
        }
        
        subject = st.selectbox('Subjects', list(subjects.keys()))
        option = st.selectbox('Option', ['Full-syllabus', 'Topic-wise'])
        
        if option == 'Topic-wise':
            topics = st.multiselect(f'Select Topics for {subject}', subjects[subject])
            syllabus_content = f"Subject: {subject}\nTopics: {', '.join(topics)}"
            selected_topic = topics[0] if topics else ""
        else:
            syllabus_content = f"Subject: {subject}\nAll topics covered"
            selected_topic = ""
            
    elif input_method == "Paste syllabus text":
        syllabus_content = st.text_area("Paste your syllabus here:", height=200)
        subject = "Custom"  # Set default subject for custom input
        selected_topic = ""
        
    elif input_method == "Upload syllabus PDF":
        uploaded_file = st.file_uploader("Upload syllabus PDF", type=["pdf"])
        if uploaded_file is not None:
            syllabus_content = extract_text_from_pdf(uploaded_file)
            subject = "Custom"  # Set default subject for PDF input
            selected_topic = ""
            st.success("PDF uploaded and processed successfully!")
            with st.expander("View extracted syllabus content"):
                st.text(syllabus_content)
    
    # Question configuration
    st.header("Question Configuration")
    
    if selected_template == "Custom":
        col1, col2 = st.columns(2)
        
        with col1:
            question_types = {
                "MCQ": st.checkbox("MCQ"),
                "Descriptive": st.checkbox("Descriptive")
            }
            
            if question_types["MCQ"]:
                num_mcq = st.slider("Number of MCQ", min_value=0, max_value=20, value=5)
            else:   
                num_mcq = 0
                
            num_3_marks = st.slider("Number of 3-marks Questions", min_value=0, max_value=20, value=5)
            num_5_marks = st.slider("Number of 5-marks Questions", min_value=0, max_value=20, value=3)
            
        with col2:
            total_marks = num_mcq + (num_3_marks * 3) + (num_5_marks * 5)
            st.metric("Total Marks", total_marks)
            
            difficulty_level = st.select_slider(
                'Difficulty level',
                options=['Easy', 'Medium', 'Hard'],
                value='Medium'
            )
            
            include_answers = st.checkbox("Generate Answer Key", value=True)

        # Validate if at least one checkbox is checked for question type
        if not any(question_types.values()):
            st.error("Please select at least one question type.")
            return
            
    else:
        template = templates[selected_template]
        question_types = template["question_types"]
        num_mcq = template["num_mcq"]
        num_3_marks = template["num_3_marks"]
        num_5_marks = template["num_5_marks"]
        total_marks = template["total_marks"]
        difficulty_level = template["selected_option"]
        include_answers = template.get("include_answers", True)
    
    # Paper generation 
    if st.button("🎯 Generate Question Paper", type="primary"):
        if not syllabus_content:
            st.error("Please provide syllabus content before generating the paper.")
            return

        with st.spinner("🔄 Generating your question paper..."):
            try:
                progress_bar = st.progress(0)
                progress_bar.progress(25)
                
                requirements = generate_prompt(
                    num_mcq, num_3_marks, num_5_marks,
                    difficulty_level, syllabus_content,
                    subject=subject,
                    topic=selected_topic,
                    with_answers=include_answers
                )
                
                progress_bar.progress(50)
                output = get_output(requirements)
                progress_bar.progress(100)

                if output and "Answer Key" in output:
                    questions, answers = output.split("Answer Key", 1)
                    questions = questions.strip()
                    answers = "Answer Key" + answers.strip()
                    
                    # Store in history
                    metadata = {
                        'subject': subject,
                        'topic': selected_topic,
                        'difficulty': difficulty_level,
                        'total_marks': total_marks,
                        'num_mcq': num_mcq,
                        'num_3_marks': num_3_marks,
                        'num_5_marks': num_5_marks
                    }
                    store_in_history(questions, answers, metadata)
                    
                    # Display current generation
                    tab1, tab2 = st.tabs(["📝 Question Paper", "✅ Answer Key"])
                    
                    with tab1:
                        st.markdown("### Question Paper")
                        st.markdown(questions)
                    
                    with tab2:
                        st.markdown("### Answer Key")
                        st.markdown(answers)
                    
                    generate_download_buttons(questions, answers, "current")
                elif output:
                    store_in_history(output, None, None)
                    st.markdown(output)
                    generate_download_buttons(output, None, "current")

            except Exception as e:
                st.error(f"Error generating paper: {str(e)}")
                if 'output' in locals() and output:
                    st.markdown(output)

    # Show history
    show_history()


if __name__ == "__main__":
    main()

