import time
import streamlit as st
import json

# Load pre-generated scenarios
with open("scenarios.json") as f:
    data = json.load(f)
    scenarios = data["travelers"]

# Demo UI
st.title("DHS Border Security Training Simulator")

# Initialize session state
if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

# Traveler selection
scenario = st.selectbox("Select a traveler profile", [s["name"] for s in scenarios])
selected = next(s for s in scenarios if s["name"] == scenario)

# Display traveler info
st.subheader("Traveler Profile")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Nationality**: {selected['nationality']}")
    st.write(f"**Age**: {selected['age']}")
with col2:
    st.write(f"**Purpose**: {selected['purpose']}")
    st.write(f"**Emotional State**: {selected['emotional_state'].title()}")

# Question input
with st.form("question_form"):
    user_input = st.text_input("Ask a question...", key="question_input")
    submitted = st.form_submit_button("Submit")

# Process question
if submitted:
    with st.spinner("Traveler is thinking..."):
        time.sleep(1)  # Simulate processing time
        
        response_found = False
        for qa in selected["script"]:
            if user_input.lower().strip() == qa["question"].lower().strip():
                st.write(f"**{selected['name']}**: {qa['response']}")
                st.write(f"*Emotion detected: {qa['emotion'].title()}*")
                response_found = True
                break
        
        if not response_found:
            st.write(f"**{selected['name']}**: I'm not sure how to answer that.")

# Sidebar analysis
with st.sidebar:
    st.header("AI Analysis")
    
    if selected["red_flags"]:
        st.metric("Red Flags Detected", len(selected["red_flags"]))
        for flag in selected["red_flags"]:
            st.error(f"⚠️ {flag}")
    else:
        st.success("No red flags detected")
    
    st.subheader("Recommended Action")
    st.markdown(f"**{selected['decision']}**")
    st.caption(selected["decision_reason"])

# Predefined questions
st.subheader("Suggested Questions")
for qa in selected["script"][:2]:  # Show first 2 questions
    if st.button(qa["question"]):
        st.session_state.user_input = qa["question"]
        st.experimental_rerun()
