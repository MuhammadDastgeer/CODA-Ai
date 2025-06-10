import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Page config for wide layout
st.set_page_config(layout="wide")

# Custom styling for padding and code wrapping
st.markdown("""
    <style>
        .block-container {
            padding: 2rem 4rem;
        }
        pre, code {
            white-space: pre-wrap !important;
            word-break: break-word !important;
        }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("🤖 AI Code Agent")
st.write("Give me any coding prompt and specify the language, I'll generate the code for you!")

# Sidebar - API Key Input
groq_api_key = st.sidebar.text_input("🔑 Enter your Groq API key:", type="password")
if not groq_api_key:
    st.warning("Please enter your Groq API key to continue.")
    st.stop()

# Optional explanation toggle
include_explanation = st.sidebar.checkbox("📘 Include explanation with the code")

# Initialize the model
try:
    chat = ChatGroq(
        temperature=0.7,
        groq_api_key=groq_api_key,
        model_name="deepseek-r1-distill-llama-70b"
    )
except Exception as e:
    st.error(f"Failed to initialize ChatGroq: {e}")
    st.stop()

# Prompt template
prompt_template = ChatPromptTemplate.from_template(
    """You are an expert coding assistant that generates clean, efficient code 
    in any programming language requested. When given a prompt, respond with 
    only the code (unless explanation is explicitly asked for) in markdown format 
    with correct syntax highlighting.

    User request: {user_input}

    {explanation_flag}
    """
)

# Chain setup
chain = prompt_template | chat | StrOutputParser()

# Input area
user_input = st.text_area("📝 Describe what you want the code to do:")

# Language selection
language = st.selectbox("💻 Select programming language:", [
    "Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Rust", "TypeScript", "Other"
])

# Handle 'Other' language input
if language == "Other":
    language = st.text_input("Type your custom language:")

# Generate button
if st.button("🚀 Generate Code"):
    if not user_input:
        st.warning("Please enter a coding prompt.")
    elif not language:
        st.warning("Please specify a programming language.")
    else:
        with st.spinner("Generating code..."):
            try:
                explanation_flag = "Also provide a brief explanation." if include_explanation else "Only return code."
                formatted_input = f"Language: {language}\nRequest: {user_input}"

                response = chain.invoke({
                    "user_input": formatted_input,
                    "language": language.lower(),
                    "explanation_flag": explanation_flag
                })

                st.markdown("### ✅ Generated Code")
                st.code(response, language=language.lower())

                # Download button
                st.download_button(
                    label="📥 Download Code",
                    data=response,
                    file_name=f"generated_code.{language.lower()}",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Sidebar instructions
st.sidebar.markdown("""
### 🧠 How to use:
1. Enter your Groq API key
2. Describe what you want the code to do
3. Select or type the programming language
4. (Optional) Toggle explanation
5. Click "Generate Code"

---
Be specific for best results!
""")
