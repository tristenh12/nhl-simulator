# main.py
import streamlit as st
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Set page config once
st.set_page_config(
    page_title="NHL What-If Simulator",
    layout="wide"
)

# Inject custom CSS for mobile responsiveness
mobile_css = """
<style>
  /* MOBILE-SPECIFIC TWEAKS */
  @media (max-width: 600px) {
    /* tighten up margins/containers */
    .block-container { padding: 1rem 0.5rem !important; }

    /* scale down headings */
    h1, h2, h3 { font-size: 1.3rem !important; }

    /* make buttons a bit smaller */
    .stButton>button { padding: 0.5rem 1rem !important; font-size: 0.9rem !important; }
  }
  /* ensure images/charts never overflow */
  .stImage img, .stChart>div { max-width: 100% !important; height: auto !important; }
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)

# Sidebar to choose mode
mode = st.sidebar.radio(
    "Pick Simulation Mode:",
    ("Free", "Full")
)

# Run the selected simulation
if mode == "Free":
    run_free_sim()
else:
    run_full_sim()
