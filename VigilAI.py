import time
import streamlit as st
import json
from datetime import datetime

# Load scenarios
with open("scenarios.json") as f:
    data = json.load(f)
    scenarios = data["travelers"]

# Initialize session state
def init_session():
    session_defaults = {
        'user_input': '',
        'conversation': [],
        'score': 0,
        'start_time': time.time(),
        'protocols_followed': 0,
        'followed_protocols': {},
        'current_protocol_traveler': None
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Risk indicator component
def risk_indicator(flags):
    risk_level = len(flags)
    if risk_level == 0:
        return "🟢 LOW RISK", "#4CAF50"
    elif 1 <= risk_level <= 2:
        return "🟡 MEDIUM RISK", "#FFC107"
    else:
        return "🔴 HIGH RISK", "#F44336"

# Main application
def main():
    st.set_page_config(page_title="DHS Training Simulator", layout="wide")
    init_session()
    
    st.title("🚨 DHS Border Security Training Simulator")
    
    # --- Traveler Selection ---
    selected_name = st.selectbox(
        "Select Traveler Profile",
        options=[t["name"] for t in scenarios],
        index=0
    )
    selected = next(t for t in scenarios if t["name"] == selected_name)
    
    # Reset timer and protocols on new selection
    if 'current_traveler' not in st.session_state or st.session_state.current_traveler != selected['id']:
        st.session_state.start_time = time.time()
        st.session_state.current_traveler = selected['id']
        st.session_state.followed_protocols = {}
        st.session_state.current_protocol_traveler = selected['id']

    # --- Profile Header ---
    risk_text, risk_color = risk_indicator(selected["red_flags"])
    with st.container():
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            st.subheader(f"Traveler Profile: {selected['name']}")
        with col2:
            st.markdown(f"<h3 style='color:{risk_color};'>{risk_text}</h3>", unsafe_allow_html=True)
        with col3:
            elapsed = int(time.time() - st.session_state.start_time)
            st.metric("⏱️ Time Elapsed", f"{elapsed // 60:02d}:{elapsed % 60:02d}")
    
    # --- Profile Details ---
    with st.expander("📄 Traveler Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Nationality**: {selected['nationality']}")
            st.markdown(f"**Age**: {selected['age']}")
        with col2:
            st.markdown(f"**Purpose**: {selected['purpose']}")
            st.markdown(f"**Emotional State**: {selected['emotional_state'].title()}")
        with col3:
            st.metric("🏆 Training Score", st.session_state.score)
    
    # --- Conversation Interface ---
    with st.form("question_form"):
        user_input = st.text_input("Ask a question:", key="question_input")
        submitted = st.form_submit_button("➤ Submit Question")
    
    if submitted:
        process_question(selected, user_input)
    
    # --- Conversation History ---
    st.subheader("📜 Conversation Transcript")
    for entry in st.session_state.conversation[-5:]:  # Show last 5 exchanges
        st.markdown(f"`{entry['time']}` **{entry['role']}**: {entry['content']}")
    
    # --- Suggested Questions ---
    st.subheader("💡 Suggested Interview Questions")
    for qa in selected["script"][:3]:
        if st.button(qa["question"], key=f"suggest_{qa['question'][:10]}"):
            st.session_state.user_input = qa["question"]
            st.experimental_rerun()
    
    # --- Analysis Sidebar ---
    with st.sidebar:
        st.header("📊 AI Analysis Panel")
        
        # Red Flags
        if selected["red_flags"]:
            st.error(f"⛔ Red Flags Detected: {len(selected['red_flags'])}")
            for flag in selected["red_flags"]:
                st.markdown(f"- 🔍 {flag}")
        else:
            st.success("✅ No red flags detected")
        
        # Protocol Tracking
        st.subheader("📝 Required Protocols")
        current_protocols = selected.get("protocols", [])
        new_followed = {}
        protocol_change = 0

        for protocol in current_protocols:
            protocol_key = f"{selected['id']}-{protocol}"
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
        ## {selected['name']}
        **Decision**: {selected['decision']}  
        **Score**: {st.session_state.score}/10  
        **Protocols Followed**: {st.session_state.protocols_followed}/{len(current_protocols)}
        **Time Spent**: {datetime.fromtimestamp(st.session_state.start_time).strftime('%H:%M:%S')}
        ### Key Findings
        {chr(10).join(selected["red_flags"]) if selected["red_flags"] else "No red flags detected"}
        """
        st.download_button("📥 Download Report", report, file_name="dhs_report.md")

def process_question(selected, user_input):
    with st.spinner("🔍 Analyzing response..."):
        time.sleep(0.5)  # Simulate processing
        
        response_found = False
        for qa in selected["script"]:
            if user_input.strip().lower() == qa["question"].strip().lower():
                # Update conversation history
                st.session_state.conversation.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "role": "You",
                    "content": user_input
                })
                st.session_state.conversation.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "role": selected["name"],
                    "content": qa["response"]
                })
                
                # Update score
                if any(flag in qa["response"] for flag in selected["red_flags"]):
                    st.session_state.score += 2
                
                # Display response
                with st.chat_message("user"):
                    st.write(f"**You**: {user_input}")
                with st.chat_message("ai", avatar="🛃"):
                    st.write(f"**{selected['name']}**: {qa['response']}")
                    st.caption(f"*Emotion detected: {qa['emotion'].title()}*")
                
                response_found = True
                break
        
        if not response_found:
            st.warning(f"**{selected['name']}**: I don't understand that question.")
            # Do not decrease the score here

if __name__ == "__main__":
    main()
