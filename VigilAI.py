import time
import streamlit as st
import json
from datetime import datetime

# Load scenarios from JSON file
with open("scenarios.json") as f:
    data = json.load(f)
    scenarios = data["travelers"]

# Initialize session state for the application
def initialize_session_state():
    session_defaults = {
        'user_input': '',
        'conversation': [],
        'score': 0,
        'start_time': time.time(),
        'protocols_followed': 0,
        'followed_protocols': {},
        'current_traveler_id': None
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Risk assessment component
def assess_risk_level(red_flags):
    risk_level = len(red_flags)
    if risk_level == 0:
        return "🟢 LOW RISK", "#4CAF50"  # Green for low risk
    elif 1 <= risk_level <= 2:
        return "🟡 MEDIUM RISK", "#FFC107"  # Yellow for medium risk
    else:
        return "🔴 HIGH RISK", "#F44336"  # Red for high risk

# Main application function
def main():
    st.set_page_config(page_title="DHS Border Security Training", layout="wide")
    initialize_session_state()
    
    st.title("DHS Border Security Training Simulator")
    
    # --- Traveler Profile Selection ---
    selected_name = st.selectbox(
        "Select Traveler Profile",
        options=[traveler["name"] for traveler in scenarios],
        index=0
    )
    selected_traveler = next(traveler for traveler in scenarios if traveler["name"] == selected_name)
    
    # Reset session state if a new traveler is selected
    if 'current_traveler_id' not in st.session_state or st.session_state.current_traveler_id != selected_traveler['id']:
        st.session_state.start_time = time.time()
        st.session_state.current_traveler_id = selected_traveler['id']
        st.session_state.followed_protocols = {}
        st.session_state.protocols_followed = 0

    # --- Traveler Profile Header ---
    risk_text, risk_color = assess_risk_level(selected_traveler["red_flags"])
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"Traveler Profile: {selected_traveler['name']}")
        with col2:
            st.markdown(f"<h3 style='color:{risk_color};'>{risk_text}</h3>", unsafe_allow_html=True)
        with col3:
            elapsed_time = int(time.time() - st.session_state.start_time)
            st.metric("⏱️ Time Elapsed", f"{elapsed_time // 60:02d}:{elapsed_time % 60:02d}")
    
    # --- Traveler Details ---
    with st.expander("📄 Traveler Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Nationality**: {selected_traveler['nationality']}")
            st.markdown(f"**Age**: {selected_traveler['age']}")
        with col2:
            st.markdown(f"**Purpose of Visit**: {selected_traveler['purpose']}")
            st.markdown(f"**Emotional State**: {selected_traveler['emotional_state'].title()}")
        with col3:
            st.metric("🏆 Training Score", st.session_state.score)
    
    # --- Interview Interface ---
    with st.form("interview_form"):
        user_input = st.text_input("Enter your question:", key="question_input")
        submitted = st.form_submit_button("Submit Question")
    
    if submitted:
        process_interaction(selected_traveler, user_input)
    
    # --- Conversation History ---
    st.subheader("📜 Conversation Transcript")
    for entry in st.session_state.conversation[-5:]:  # Display the last 5 exchanges
        st.markdown(f"`{entry['time']}` **{entry['role']}**: {entry['content']}")
    
    # --- Suggested Questions ---
    st.subheader("💡 Suggested Interview Questions")
    for qa in selected_traveler["script"][:3]:
        if st.button(qa["question"], key=f"suggest_{qa['question'][:10]}"):
            st.session_state.user_input = qa["question"]
            st.experimental_rerun()
    
    # --- Analysis Sidebar ---
    with st.sidebar:
        st.header("📊 Analysis Panel")
        
        # Red Flags
        if selected_traveler["red_flags"]:
            st.error(f"⛔ Red Flags Detected: {len(selected_traveler['red_flags'])}")
            for flag in selected_traveler["red_flags"]:
                st.markdown(f"- 🔍 {flag}")
        else:
            st.success("✅ No red flags detected")
        
        # Protocol Tracking
        st.subheader("📝 Required Protocols")
        current_protocols = selected_traveler.get("protocols", [])
        new_followed = {}
        protocol_change = 0

        for protocol in current_protocols:
            protocol_key = f"{selected_traveler['id']}-{protocol}"
            was_checked = st.session_state.followed_protocols.get(protocol_key, False)
            is_checked = st.checkbox(protocol, value=was_checked, key=f"proto_{protocol_key}")
            new_followed[protocol_key] = is_checked
            
            if is_checked != was_checked:
                protocol_change += 1 if is_checked else -1

        # Update protocol count
        st.session_state.protocols_followed += protocol_change
        st.session_state.followed_protocols = new_followed
        
        # Performance Metrics
        st.subheader("📈 Performance Metrics")
        st.metric("Protocols Followed", st.session_state.protocols_followed)
        st.metric("Response Consistency", f"{min(st.session_state.score * 10, 100)}%")
        
        # Download Report
        report = f"""
        # After-Action Report
        ## {selected_traveler['name']}
        **Decision**: {selected_traveler['decision']}  
        **Score**: {st.session_state.score}/10  
        **Protocols Followed**: {st.session_state.protocols_followed}/{len(current_protocols)}
        **Time Spent**: {datetime.fromtimestamp(st.session_state.start_time).strftime('%H:%M:%S')}
        ### Key Findings
        {chr(10).join(selected_traveler["red_flags"]) if selected_traveler["red_flags"] else "No red flags detected"}
        """
        st.download_button("📥 Download Report", report, file_name="dhs_report.md")

# Process user questions and traveler responses
def process_interaction(traveler, user_input):
    with st.spinner("🔍 Analyzing response..."):
        time.sleep(0.5)  # Simulate processing time
        
        response_found = False
        for qa in traveler["script"]:
            if user_input.strip().lower() == qa["question"].strip().lower():
                # Update conversation history
                st.session_state.conversation.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "role": "Officer",
                    "content": user_input
                })
                st.session_state.conversation.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "role": traveler["name"],
                    "content": qa["response"]
                })
                
                # Update score based on red flags
                if any(flag in qa["response"] for flag in traveler["red_flags"]):
                    st.session_state.score += 2
                
                # Display response
                with st.chat_message("user"):
                    st.write(f"**Officer**: {user_input}")
                with st.chat_message("ai", avatar="🛃"):
                    st.write(f"**{traveler['name']}**: {qa['response']}")
                    st.caption(f"*Emotion detected: {qa['emotion'].title()}*")
                
                response_found = True
                break
        
        if not response_found:
            st.warning(f"**{traveler['name']}**: I don't understand that question.")
            st.session_state.score -= 1

if __name__ == "__main__":
    main()
