import time
import streamlit as st
import json
from datetime import datetime

# Load profiles
with open("profiles.json") as f:
    data = json.load(f)
    profiles = data["profiles"]

# Initialize session state
def init_session():
    session_defaults = {
        'user_input': '',
        'conversation': [],
        'score': 0,
        'start_time': time.time(),
        'common_interests': 0,
        'matched_interests': {},
        'current_profile': None
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Compatibility indicator component
def compatibility_indicator(interests):
    compatibility_level = len(interests)
    if compatibility_level == 0:
        return "🔴 LOW COMPATIBILITY", "#F44336"
    elif 1 <= compatibility_level <= 2:
        return "🟡 MEDIUM COMPATIBILITY", "#FFC107"
    else:
        return "🟢 HIGH COMPATIBILITY", "#4CAF50"

# Main application
def main():
    st.set_page_config(page_title="Dating App", layout="wide")
    init_session()
    
    st.title("💖 Modern Dating Simulator")
    
    # --- Profile Selection ---
    selected_name = st.selectbox(
        "Select a Profile",
        options=[p["name"] for p in profiles],
        index=0
    )
    selected = next(p for p in profiles if p["name"] == selected_name)
    
    # Reset timer and interests on new selection
    if 'current_profile' not in st.session_state or st.session_state.current_profile != selected['id']:
        st.session_state.start_time = time.time()
        st.session_state.current_profile = selected['id']
        st.session_state.matched_interests = {}
        st.session_state.current_profile = selected['id']

    # --- Profile Header ---
    compatibility_text, compatibility_color = compatibility_indicator(selected["interests"])
    with st.container():
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            st.subheader(f"Profile: {selected['name']}")
        with col2:
            st.markdown(f"<h3 style='color:{compatibility_color};'>{compatibility_text}</h3>", unsafe_allow_html=True)
        with col3:
            elapsed = int(time.time() - st.session_state.start_time)
            st.metric("⏱️ Time Elapsed", f"{elapsed // 60:02d}:{elapsed % 60:02d}")
    
    # --- Profile Details ---
    with st.expander("📄 Profile Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Age**: {selected['age']}")
            st.markdown(f"**Location**: {selected['location']}")
        with col2:
            st.markdown(f"**Occupation**: {selected['occupation']}")
            st.markdown(f"**Hobbies**: {', '.join(selected['hobbies'])}")
        with col3:
            st.metric("💖 Compatibility Score", st.session_state.score)
    
    # --- Conversation Interface ---
    with st.form("question_form"):
        user_input = st.text_input("Start a conversation:", key="question_input")
        submitted = st.form_submit_button("➤ Send Message")
    
    if submitted:
        process_message(selected, user_input)
    
    # --- Conversation History ---
    st.subheader("📜 Conversation Transcript")
    for entry in st.session_state.conversation[-5:]:  # Show last 5 exchanges
        st.markdown(f"`{entry['time']}` **{entry['role']}**: {entry['content']}")
    
    # --- Suggested Conversation Starters ---
    st.subheader("💡 Suggested Conversation Starters")
    for qa in selected["conversation_starters"][:3]:
        if st.button(qa["question"], key=f"suggest_{qa['question'][:10]}"):
            st.session_state.user_input = qa["question"]
            st.experimental_rerun()
    
    # --- Analysis Sidebar ---
    with st.sidebar:
        st.header("📊 Compatibility Analysis Panel")
        
        # Common Interests
        if selected["interests"]:
            st.success(f"✅ Common Interests: {len(selected['interests'])}")
            for interest in selected["interests"]:
                st.markdown(f"- 💡 {interest}")
        else:
            st.error("🔴 No common interests detected")
        
        # Interest Tracking
        st.subheader("📝 Matched Interests")
        current_interests = selected.get("interests", [])
        new_matched = {}
        interest_change = 0

        for interest in current_interests:
            interest_key = f"{selected['id']}-{interest}"
            was_checked = st.session_state.matched_interests.get(interest_key, False)
            is_checked = st.checkbox(interest, value=was_checked, key=f"interest_{interest_key}")
            new_matched[interest_key] = is_checked
            
            if is_checked != was_checked:
                interest_change += 1 if is_checked else -1

        # Update interest count
        st.session_state.common_interests += interest_change
        st.session_state.matched_interests = new_matched
        
        # Performance Metrics
        st.subheader("📈 Performance Metrics")
        st.metric("Common Interests", st.session_state.common_interests)
        st.metric("Conversation Quality", f"{min(st.session_state.score * 10, 100)}%")
        
        # Download Report
        report = f"""
        # Compatibility Report
        ## {selected['name']}
        **Decision**: {selected['decision']}  
        **Score**: {st.session_state.score}/10  
        **Common Interests**: {st.session_state.common_interests}/{len(current_interests)}
        **Time Spent**: {datetime.fromtimestamp(st.session_state.start_time).strftime('%H:%M:%S')}
        ### Key Findings
        {chr(10).join(selected["interests"]) if selected["interests"] else "No common interests detected"}
        """
        st.download_button("📥 Download Report", report, file_name="dating_report.md")

def process_message(selected, user_input):
    with st.spinner("💬 Analyzing response..."):
        time.sleep(0.5)  # Simulate processing
        
        response_found = False
        for qa in selected["conversation_starters"]:
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
                if any(interest in qa["response"] for interest in selected["interests"]):
                    st.session_state.score += 2
                
                # Display response
                with st.chat_message("user"):
                    st.write(f"**You**: {user_input}")
                with st.chat_message("ai", avatar="💖"):
                    st.write(f"**{selected['name']}**: {qa['response']}")
                    st.caption(f"*Mood detected: {qa['mood'].title()}*")
                
                response_found = True
                break
        
        if not response_found:
            st.warning(f"**{selected['name']}**: I don't understand that question.")
            st.session_state.score -= 1

if __name__ == "__main__":
    main()
