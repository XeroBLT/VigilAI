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
        'selected_protocols': [],
        'protocol_submitted': False,
        'current_protocol_traveler': None,
        'protocol_feedback': {},
        'show_hints': False
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

# Get all possible protocols from all scenarios
def get_all_protocols():
    all_protocols = set()
    for traveler in scenarios:
        all_protocols.update(traveler.get("protocols", []))
    return sorted(all_protocols)

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
    all_protocols = get_all_protocols()
    correct_protocols = selected.get("protocols", [])
    
    # Reset states on new selection
    if 'current_traveler' not in st.session_state or st.session_state.current_traveler != selected['id']:
        st.session_state.start_time = time.time()
        st.session_state.current_traveler = selected['id']
        st.session_state.score = 0
        st.session_state.selected_protocols = []
        st.session_state.protocol_submitted = False
        st.session_state.protocol_feedback = {}
        st.session_state.show_hints = False

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
    for entry in st.session_state.conversation[-5:]:
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
        
        # Protocol Selection System
        st.subheader("🔒 Protocol Selection")
        st.write("Select ALL applicable protocols:")
        
        # Protocol checkboxes with hashed keys
        selected_protocols = []
        for protocol in all_protocols:
            protocol_hash = abs(hash(protocol))
            unique_key = f"proto_{selected['id']}_{protocol_hash}"
            
            if st.checkbox(
                protocol,
                value=protocol in st.session_state.selected_protocols,
                key=unique_key
            ):
                selected_protocols.append(protocol)
        
        # Protocol submission
        protocol_submitted = st.button("✅ Validate Protocol Selection")
        if protocol_submitted:
            st.session_state.selected_protocols = selected_protocols
            st.session_state.protocol_submitted = True
            
            # Calculate protocol score
            correct = set(selected_protocols) & set(correct_protocols)
            incorrect = set(selected_protocols) - set(correct_protocols)
            missed = set(correct_protocols) - set(selected_protocols)
            
            st.session_state.score += len(correct) * 2
            st.session_state.score -= (len(incorrect) + len(missed)) * 1
            st.session_state.score = max(st.session_state.score, 0)
            
            st.session_state.protocol_feedback = {
                "correct": list(correct),
                "incorrect": list(incorrect),
                "missed": list(missed)
            }
        
        # Protocol feedback
        if st.session_state.protocol_submitted:
            st.subheader("📝 Protocol Feedback")
            feedback = st.session_state.protocol_feedback
            
            if feedback["correct"]:
                st.success("**Correctly Selected:**")
                for p in feedback["correct"]:
                    st.markdown(f"✓ {p}")
            
            if feedback["incorrect"]:
                st.error("**Incorrectly Selected:**")
                for p in feedback["incorrect"]:
                    st.markdown(f"✗ {p}")
            
            if feedback["missed"]:
                st.warning("**Missed Protocols:**")
                for p in feedback["missed"]:
                    st.markdown(f"⚠️ {p}")

        # Hint System
        with st.expander("💡 Get Protocol Hints (Affects Score)", expanded=False):
            if st.button("Show Hint (-1 Point)"):
                if st.session_state.score > 0:
                    st.session_state.score = max(st.session_state.score - 1, 0)
                    st.session_state.show_hints = True
                else:
                    st.warning("You need at least 1 point to view hints!")

            if st.session_state.show_hints:
                st.write("**Protocol Indicators:**")
                hint_mapping = {
                    "USC": "U.S. Code",
                    "CFR": "Code of Federal Regulations",
                    "detain": "Temporary holding",
                    "deny": "Entry refusal",
                    "verify": "Document validation"
                }

                for protocol in correct_protocols:
                    masked = protocol
                    # Replace known terms
                    for term, replacement in hint_mapping.items():
                        masked = masked.replace(term, f"[{replacement}]")
                    # Mask numbers
                    masked = " ".join(["[Law]" if any(c.isdigit() for c in word) else word for word in masked.split()])
                    st.markdown(f"• {masked}")
        
        # Performance Metrics
        st.subheader("📈 Performance Metrics")
        st.metric("Current Score", st.session_state.score)
        st.metric("Response Consistency", f"{min(st.session_state.score * 10, 100)}%")
        
        # Download Report
        report = f"""
        # After-Action Report
        ## {selected['name']}
        **Decision**: {selected['decision']}  
        **Score**: {st.session_state.score}/10  
        **Time Spent**: {datetime.fromtimestamp(st.session_state.start_time).strftime('%H:%M:%S')}
        ### Protocol Analysis
        Correct: {len(st.session_state.protocol_feedback.get('correct', []))}
        Incorrect: {len(st.session_state.protocol_feedback.get('incorrect', []))}
        Missed: {len(st.session_state.protocol_feedback.get('missed', []))}
        ### Key Findings
        {chr(10).join(selected["red_flags"]) if selected["red_flags"] else "No red flags detected"}
        """
        st.download_button("📥 Download Report", report, file_name="dhs_report.md")

def process_question(selected, user_input):
    with st.spinner("🔍 Analyzing response..."):
        time.sleep(0.5)
        
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
                
                # Update score with bounds check (0-10)
                new_score = st.session_state.score + 2
                st.session_state.score = min(max(new_score, 0), 10)
                
                # Display response
                with st.chat_message("user"):
                    st.write(f"**You**: {user_input}")
                with st.chat_message("ai", avatar="🛃"):
                    st.write(f"**{selected['name']}**: {qa['response']}")
                    st.caption(f"*Emotion detected: {qa['emotion'].title()}*")
                
                response_found = True
                break
        
        if not response_found:
            st.session_state.score = max(st.session_state.score - 1, 0)
            st.warning(f"**{selected['name']}**: I don't understand that question.")

if __name__ == "__main__":
    main()
