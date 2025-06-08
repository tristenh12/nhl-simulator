# main.py
import streamlit as st
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Only one set_page_config() call in the entire app:
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")

mode = st.sidebar.radio(
    "Pick Simulation Mode:",
    ("Free", "Full")
)

if mode == "Free":
    run_free_sim()
else:
    run_full_sim()
