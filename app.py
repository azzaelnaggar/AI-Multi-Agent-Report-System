import streamlit as st
import os
from main import run_pipeline
import json

# ---- Ensure outputs folder exists ----
os.makedirs("outputs", exist_ok=True)

# ---- Page configuration ----
st.set_page_config(
    page_title="AI Multi-Agent Report System",
    layout="centered"
)

# ---- Custom CSS (kept here) ----
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #667eea;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.75rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---- Header ----
st.markdown("""
<div class="main-header">
    <h1>AI Multi-Agent Report System</h1>
</div>
""", unsafe_allow_html=True)

# ---- Main Form ----
with st.form(key="pipeline_form"):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_input(
            "Topic *",
            placeholder="e.g., Artificial Intelligence in Education",
            help="Enter the topic you want to research"
        )
    
    with col2:
        author = st.text_input(
            "Author Name",
            value="AutoAgent",
            help="This name will appear in the report header"
        )
    
    title = st.text_input(
        "Report Title (Optional)",
        placeholder="Leave empty for automatic generation",
        help="If left blank, the topic will be used as the title"
    )
    
    submit_button = st.form_submit_button("Generate Report", use_container_width=True)

# ---- Run Pipeline ----
if submit_button:
    if not topic.strip():
        st.error("Please enter a research topic!")
    else:
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("Processing your request..."):
            try:
                # Update progress
                status_text.text("Researching...")
                progress_bar.progress(20)
                
                # Run the pipeline
                meta = run_pipeline(
                    topic=topic,
                    title=title if title.strip() else None,
                    author=author
                )
                
                progress_bar.progress(100)
                
                if meta.get("success"):
                    status_text.empty()
                    st.markdown('<div class="success-box">Report generation completed successfully!</div>', unsafe_allow_html=True)
                    
                    # ---- Show Research Hits ----
                    with st.expander("Research Hits", expanded=True):
                        research_path = meta.get("research_path")
                        if research_path and os.path.exists(research_path):
                            with open(research_path, "r", encoding="utf-8") as f:
                                research = json.load(f)
                            hits = research.get("hits", [])
                            if hits:
                                for i, hit in enumerate(hits, 1):
                                    st.markdown(f"**{i}. [{hit['title']}]({hit['url']})**")
                                    st.caption(hit.get("snippet", ""))
                                    st.divider()
                            else:
                                st.info("No hits found.")
                        else:
                            st.warning("Research JSON not found.")
                    
                    # ---- Show Final Report Preview ----
                    with st.expander("Report Preview", expanded=False):
                        final_md_path = meta.get("final_md_path")
                        if final_md_path and os.path.exists(final_md_path):
                            with open(final_md_path, "r", encoding="utf-8") as f:
                                md_content = f.read()
                            st.markdown(md_content)
                        else:
                            st.warning("Final report file not found.")
                    
                    # ---- Download Buttons ----
                    st.subheader("Download")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download HTML
                        html_path = meta.get("pdf_path")
                        if html_path and os.path.exists(html_path):
                            with open(html_path, "rb") as f:
                                st.download_button(
                                    "Download HTML",
                                    f,
                                    file_name=f"{topic}_report.html",
                                    mime="text/html",
                                    use_container_width=True
                                )
                    
                    with col2:
                        # Download Markdown
                        final_md_path = meta.get("final_md_path")
                        if final_md_path and os.path.exists(final_md_path):
                            with open(final_md_path, "rb") as f:
                                st.download_button(
                                    "Download Markdown",
                                    f,
                                    file_name=f"{topic}_report.md",
                                    mime="text/markdown",
                                    use_container_width=True
                                )
                else:
                    status_text.empty()
                    error_msg = meta.get("error", "Unknown error")
                    st.markdown(f'<div class="error-box">Report generation failed: {error_msg}</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                status_text.empty()
                st.markdown(f'<div class="error-box">An error occurred: {str(e)}</div>', unsafe_allow_html=True)
                st.exception(e)
