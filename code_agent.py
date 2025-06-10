import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fpdf import FPDF
import textwrap
import io
import contextlib

# --------- Streamlit Page Config ---------
st.set_page_config(layout="wide")

# --------- Custom CSS ---------
st.markdown("""
    <style>
        .block-container { padding: 2rem 4rem; }
        pre, code { white-space: pre-wrap !important; word-break: break-word !important; }
        .stButton>button { margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --------- Session State ---------
if "history" not in st.session_state:
    st.session_state.history = []

# --------- App Title ---------
st.title("🤖 AI Code Agent")
st.write("Give me any coding prompt and specify the language, I'll generate the code for you!")

# --------- Sidebar Options ---------
groq_api_key = st.sidebar.text_input("🔑 Enter your Groq API key:", type="password")
include_explanation = st.sidebar.checkbox("📘 Include explanation with the code", value=False)
show_code_only = st.sidebar.checkbox("🧾 Show code only in output", value=True)
enhance_prompt = st.sidebar.checkbox("✨ Auto-enhance vague prompts", value=False)
clear_inputs = st.sidebar.button("🧹 Clear all inputs")

uploaded_file = st.sidebar.file_uploader("📂 Upload code file for context", type=["py", "js", "cpp", "java", "txt"])

# --------- Groq API Check ---------
if not groq_api_key:
    st.warning("Please enter your Groq API key to continue.")
    st.stop()

# --------- LangChain Setup ---------
try:
    chat = ChatGroq(temperature=0.7, groq_api_key=groq_api_key, model_name="deepseek-r1-distill-llama-70b")
except Exception as e:
    st.error(f"Failed to initialize ChatGroq: {e}")
    st.stop()

# --------- Prompt Templates ---------
main_prompt = ChatPromptTemplate.from_template("""
You are an expert coding assistant that generates clean, efficient code 
in any programming language requested. When given a prompt, respond with 
only the code (unless explanation is explicitly asked for) in markdown format 
with correct syntax highlighting.

User request: {user_input}

{explanation_flag}
""")

rewriter_prompt = ChatPromptTemplate.from_template(
    "Rewrite this prompt to be as clear and specific as possible for coding:\n{input}"
)

review_prompt = ChatPromptTemplate.from_template(
    "Review the following code and provide improvements:\n```{language}\n{code}\n```"
)

# --------- Chains ---------
main_chain = main_prompt | chat | StrOutputParser()
rewriter_chain = rewriter_prompt | chat | StrOutputParser()
review_chain = review_prompt | chat | StrOutputParser()

# --------- Inputs ---------
# Inside your sidebar or main layout
clear_inputs = st.sidebar.button("🗑️ Clear All Inputs")

if clear_inputs:
    st.session_state.history.clear()  # or any other session state vars
    st.experimental_rerun()

    

user_input = st.text_area("📝 Describe what you want the code to do:")

language = st.selectbox("💻 Select programming language:", [
    "Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Rust", "TypeScript", "Other"
])

if language == "Other":
    language = st.text_input("Type your custom language:")

# --------- Optional Context from Upload ---------
context_code = ""
if uploaded_file:
    context_code = uploaded_file.read().decode("utf-8")
    user_input = f"{context_code}\n\nNow do this:\n{user_input}"

# --------- Generate Code ---------
if st.button("🚀 Generate Code"):
    if not user_input:
        st.warning("Please enter a coding prompt.")
    elif not language:
        st.warning("Please specify a programming language.")
    else:
        with st.spinner("Generating code..."):
            try:
                # Enhance prompt if selected
                if enhance_prompt:
                    user_input = rewriter_chain.invoke({"input": user_input})

                explanation_flag = "Also provide a brief explanation." if include_explanation else "Only return code."
                formatted_input = f"Language: {language}\nRequest: {user_input}"

                response = main_chain.invoke({
                    "user_input": formatted_input,
                    "language": language.lower(),
                    "explanation_flag": explanation_flag
                })

                estimated_tokens = len(formatted_input.split()) + len(response.split())

                # Save in history
                st.session_state.history.append({
                    "prompt": user_input,
                    "language": language,
                    "response": response
                })

                # Display result
                st.markdown("### ✅ Generated Code")
                if show_code_only:
                    st.code(response, language=language.lower())
                else:
                    st.markdown(response, unsafe_allow_html=True)

                st.text_area("📋 Copyable Code", value=response, height=200)

                st.download_button(
                    label="📥 Download Code",
                    data=response,
                    file_name=f"generated_code.{language.lower()}",
                    mime="text/plain"
                )

               

                # Python Code Runner
                if language.lower() == "python":
                    st.markdown("### ▶️ Run Code Output")
                    output_buffer = io.StringIO()
                    try:
                        with contextlib.redirect_stdout(output_buffer):
                            exec(response)
                        st.text(output_buffer.getvalue())
                    except Exception as e:
                        st.error(f"Runtime Error: {e}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

# --------- Review Code ---------
if st.button("🔍 Review My Code"):
    if not st.session_state.history:
        st.warning("Generate code first.")
    else:
        last = st.session_state.history[-1]
        with st.spinner("Reviewing code..."):
            try:
                review = review_chain.invoke({
                    "language": last["language"],
                    "code": last["response"]
                })
                st.markdown("### 🧠 AI Review & Suggestions")
                st.write(review)
            except Exception as e:
                st.error(f"Review failed: {e}")



# --------- PDF Export ---------
def generate_pdf(history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for item in history:
        pdf.multi_cell(0, 10, f"Prompt: {item['prompt']}")
        pdf.multi_cell(0, 10, f"Language: {item['language']}")
        pdf.multi_cell(0, 10, f"Code:\n{item['response']}")
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

if st.sidebar.button("📄 Export Session as PDF"):
    if st.session_state.history:
        pdf_data = generate_pdf(st.session_state.history)
        st.download_button("Download PDF", pdf_data, "session_history.pdf", "application/pdf")
    else:
        st.warning("No history to export.")

# --------- Sidebar Help ---------
st.sidebar.markdown("""
---
### 📌 How to use:
1. Enter your Groq API key
2. Describe what you want the code to do
3. Choose the language
4. (Optional) Upload context file or enhance prompt
5. Click "Generate Code"

Try giving clear instructions for the best results.
""")


