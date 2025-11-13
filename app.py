import streamlit as st
import os
import re
from datetime import datetime
try:
    import openai
except Exception:
    openai = None

st.set_page_config(page_title="LegacyOnboard AI - Prototype", layout="wide")

st.title("LegacyOnboard AI — Prototype")
st.markdown("""
This is a lightweight prototype of the LegacyOnboard conversational onboarding assistant.
Two modes are supported:
- **MOCK** (default): runs without any external API and returns simulated AI responses for demo and testing.
- **OPENAI**: if you set the environment variable `OPENAI_API_KEY`, the app will attempt to call the OpenAI Chat API.
""")

mode = st.sidebar.selectbox("Mode", ["MOCK", "OPENAI"])

if mode == "OPENAI" and openai is None:
    st.sidebar.error("OpenAI SDK not installed in this environment. Use MOCK mode or install packages from requirements.txt.")

st.sidebar.markdown("## Quick actions")
st.sidebar.write("Upload a text file (or paste text) containing client documents to simulate data extraction.")

# --- Left column: Document upload & extraction ---
col1, col2 = st.columns([1,2])

with col1:
    st.header("Document Upload / Paste")
    uploaded = st.file_uploader("Upload a .txt file with client info (or skip and paste below)", type=["txt"])
    pasted = st.text_area("Or paste extracted document text here", height=200)
    raw_text = ""
    if uploaded is not None:
        try:
            raw_text = uploaded.getvalue().decode("utf-8")
        except Exception:
            raw_text = str(uploaded.getvalue())
    if pasted.strip():
        raw_text = pasted

    if raw_text.strip():
        st.subheader("Preview (first 800 chars)")
        st.code(raw_text[:800])

        # Simple extraction heuristics
        def extract_fields(text):
            fields = {}
            # name: look for "Name: ..." or capitalized first+last on a line
            m = re.search(r"Name:\s*(.+)", text, re.I)
            if m:
                fields["name"] = m.group(1).strip()
            else:
                m2 = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)", text)
                if m2:
                    fields["name"] = m2.group(1)
            # email
            m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
            if m:
                fields["email"] = m.group(1)
            # phone
            m = re.search(r"(\+?\d[\d\-\s]{7,}\d)", text)
            if m:
                fields["phone"] = re.sub(r"\s+","", m.group(1))
            # dob simple
            m = re.search(r"(?:DOB|Date of Birth)[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})", text, re.I)
            if m:
                fields["dob"] = m.group(1)
            # Mock ID number (SSN-like)
            m = re.search(r"(\d{3}-\d{2}-\d{4})", text)
            if m:
                fields["ssn"] = m.group(1)
            return fields

        extracted = extract_fields(raw_text)
        st.subheader("Extracted fields")
        if extracted:
            for k,v in extracted.items():
                st.write(f"**{k}**: {v}")
        else:
            st.write("No structured fields found. Try pasting a line like `Name: John Doe` or an email address.")

with col2:
    st.header("Interactive Onboarding Chat")
    st.write("Use the chat to guide the client, ask clarifying questions, and generate completed onboarding forms.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Client message or agent instruction", key="user_input")
    send = st.button("Send")

    def mock_agent_response(user_text, extracted):
        # Very simple rule-based simulated assistant
        if "start" in user_text.lower():
            return "Hello! I'm LegacyOnboard AI. I can guide you through onboarding, extract info from uploads, and pre-fill forms. Please upload your ID or paste the document text."
        if "status" in user_text.lower():
            return "Your onboarding status: Incomplete — documents pending. I can help you complete and submit them."
        if "form" in user_text.lower() or "complete" in user_text.lower():
            if extracted:
                lines = [f"{k}: {v}" for k,v in extracted.items()]
                return "I prepared a draft of your onboarding fields:\n" + "\n".join(lines) + "\nWould you like me to generate a completed PDF form?"
            else:
                return "I don't have enough info yet. Please upload or paste your documents so I can extract data."
        # fallback
        return "Thanks — I understand. For demo mode, try asking me to 'start onboarding', 'check status', or 'complete form'."

    if send and user_input.strip():
        st.session_state.chat_history.append(("Client", user_input.strip()))

        if mode == "MOCK":
            reply = mock_agent_response(user_input.strip(), extracted if 'extracted' in locals() else {})
        else:
            # OPENAI mode: call the API if available and API key exists in env
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key or openai is None:
                reply = "OpenAI mode requested but API key / SDK not available. Switch to MOCK or follow README to enable OpenAI."
            else:
                openai.api_key = api_key
                system_prompt = (
                    "You are LegacyOnboard AI — a professional onboarding assistant for a financial services company. "
                    "Be concise, ask only necessary questions, and avoid giving legal or tax advice. Always suggest secure document upload."
                )
                try:
                    resp = openai.ChatCompletion.create(
                        model="gpt-4o-mini", # user may change model per their account
                        messages=[{"role":"system","content":system_prompt},
                                  {"role":"user","content":user_input}],
                        max_tokens=500,
                        temperature=0.1
                    )
                    reply = resp["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    reply = f"OpenAI API error: {e}"

        st.session_state.chat_history.append(("Agent", reply))

    # display history
    for role, text in st.session_state.chat_history:
        if role == "Client":
            st.markdown(f"**You:** {text}")
        else:
            st.markdown(f"**LegacyOnboard AI:** {text}")

    # Quick action: generate a filled form (text-based) from extracted fields
    if st.button("Generate Draft Onboarding Form"):
        if 'extracted' in locals() and extracted:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            form_lines = [f"Onboarding Draft - Generated {now}", "--------------------------"]
            for k,v in extracted.items():
                form_lines.append(f"{k}: {v}")
            form_text = "\n".join(form_lines)
            st.text_area("Draft Onboarding Form (editable)", value=form_text, height=250)
            st.success("Draft prepared. In a full implementation this could be turned into a PDF and sent for e-signature.")
        else:
            st.warning("No extracted data available to generate a form.")

st.markdown("---")
st.caption("Prototype for course assignment. This demo intentionally keeps sensitive data handling minimal — do not use with real PII in MOCK mode.")