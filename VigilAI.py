import time
import pyttsx3
import streamlit as st
import json

# Load pre-generated scenarios
with open("scenarios.json") as f:
    scenarios = json.load(f)

# Demo UI
st.title("DHS Border Security Training Simulator")
scenario = st.selectbox("Select a traveler profile", [s["profile"]["name"] for s in scenarios])

selected = next(s for s in scenarios if s["profile"]["name"] == scenario)
st.write(f"**Nationality**: {selected['profile']['nationality']}")
st.write(f"**Visa Type**: {selected['profile']['visa_type']}")

user_input = st.text_input("Ask a question...")
if user_input:
    if user_input in selected["responses"]:
        st.write(f"**Traveler**: {selected['responses'][user_input]}")
        # Highlight red flags if a critical question is asked
        if user_input == "What is your purpose for visiting?":
            st.error("RED FLAG: Visa type (tourism) conflicts with mention of a business conference.")
    else:
        st.write("**Traveler**: I’m not sure what you mean.")

if user_input:
    with st.spinner("Traveler is thinking..."):
        time.sleep(1)  # Simulate processing time
    # Show response
engine = pyttsx3.init()
engine.say(selected["responses"][user_input])
engine.runAndWait()

with st.sidebar:
    st.header("AI Analysis")
    st.metric("Red Flags Detected", len(selected["profile"]["red_flags"]))
    for flag in selected["profile"]["red_flags"]:
        st.write(f"⚠️ {flag}")

if st.button("Ask about purpose of visit"):
    user_input = "What is your purpose for visiting?"
