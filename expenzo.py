import streamlit as st
import pandas as pd
import plotly.express as px
import pyttsx3, os, tempfile, re, playsound
from gtts import gTTS
import speech_recognition as sr
from api import get_gemini_reply
from datetime import datetime

# -------------------------------------------------
# STREAMLIT CONFIG
# -------------------------------------------------
st.set_page_config(page_title="💰 Expenzo - Smart AI Expense Tracker",
                   layout="wide",
                   page_icon="💰")


# -------------------------------------------------
# LOGIN SYSTEM
# -------------------------------------------------
def login_page():
    st.title("🔐 Login to Expenzo")

    USERNAMES = ["pratham joshi", "stuti shrivas"]   # allowed usernames
    PASSWORD = "1234"                                # common password

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username.lower() in [u.lower() for u in USERNAMES] and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("Login successful! Redirecting...")
            st.rerun()     # UPDATED
        else:
            st.error("Invalid username or password.")


# Initialize login key
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# If not logged in → show login page
if not st.session_state.logged_in:
    login_page()
    st.stop()


# -------------------------------------------------
# SIDEBAR LOGOUT
# -------------------------------------------------
st.sidebar.title("Account")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()   # UPDATED


# -------------------------------------------------
# SESSION STATES
# -------------------------------------------------
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Description'])
if 'threshold' not in st.session_state:
    st.session_state.threshold = 1000.0
if 'threshold_alerted' not in st.session_state:
    st.session_state.threshold_alerted = False


# -------------------------------------------------
# TEXT TO SPEECH
# -------------------------------------------------
def speak_fast(text):
    clean_text = re.sub(r'[*₹•]', '', str(text)).replace("...", " ").strip()

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 185)
        engine.setProperty('volume', 1.0)
        engine.say(clean_text)
        engine.runAndWait()

    except Exception:
        try:
            temp_file = os.path.join(tempfile.gettempdir(), "voice_output.mp3")
            gTTS(text=clean_text, lang='en', slow=False).save(temp_file)
            playsound.playsound(temp_file)
            os.remove(temp_file)
        except Exception as e:
            st.warning(f"Speech error: {e}")


# -------------------------------------------------
# VOICE INPUT
# -------------------------------------------------
def voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Speak now...")
        audio = r.listen(source, timeout=6, phrase_time_limit=8)

    try:
        text = r.recognize_google(audio)
        st.success(f"🗣️ You said: {text}")
        return text.lower()

    except sr.UnknownValueError:
        st.warning("Could not understand. Try again.")
        return ""

    except sr.RequestError:
        st.warning("Speech service unavailable.")
        return ""


# -------------------------------------------------
# CATEGORY DETECTION
# -------------------------------------------------
def detect_category(command):
    mapping = {
        "Food": ["food", "lunch", "dinner", "snack", "restaurant", "breakfast"],
        "Travel": ["travel", "bus", "train", "taxi", "cab", "auto", "petrol", "fuel"],
        "Shopping": ["shopping", "clothes", "gift", "mall"],
        "Bills": ["electricity", "water", "gas", "wifi", "bill", "recharge"],
        "Entertainment": ["movie", "netflix", "game", "music"],
        "Misc": []
    }
    for cat, keywords in mapping.items():
        if any(word in command for word in keywords):
            return cat
    return "Misc"


def parse_voice_input(command):
    amount_match = re.search(r'(\d+)', command)
    amount = float(amount_match.group(1)) if amount_match else None

    category = detect_category(command)

    desc_match = re.search(r'(?:for|on)\s+(.+)', command)
    desc = desc_match.group(1).capitalize() if desc_match else "Voice entry"

    return amount, category, desc


# -------------------------------------------------
# AI INSIGHT
# -------------------------------------------------
def ai_insight(prompt):
    try:
        return get_gemini_reply(prompt)
    except Exception as e:
        return f"AI error: {e}"


# -------------------------------------------------
# CUSTOM THEME
# -------------------------------------------------
st.markdown("""
<style>
body, .stApp { background-color:#0E1117; color:#FAFAFA !important; }
h1, h2, h3, h4, h5, label, div, p { color:#FAFAFA !important; }
.card { background-color:#1E293B; padding:15px; border-radius:10px;
        text-align:center; color:#FAFAFA; box-shadow:0 0 10px rgba(56,189,248,0.3); }
.main-title { text-align:center; font-size:45px; color:#38BDF8; font-weight:700; margin-bottom:15px; }
button[kind="primary"] { background-color:#2563EB !important; color:white !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>💰 Expenzo - AI Expense Tracker</h1>", unsafe_allow_html=True)


# -------------------------------------------------
# TABS
# -------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📥 Add Expense",
    "📊 Dashboard",
    "📈 Charts",
    "🤖 AI Chat"
])


# -------------------------------------------------
# TAB 1 — ADD EXPENSE
# -------------------------------------------------
with tab1:
    st.subheader("➕ Add a New Expense")

    with st.form("expense_form"):
        date = st.date_input("Date", datetime.now())
        category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Misc"])
        amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0)
        desc = st.text_input("Description", placeholder="e.g. Lunch at cafe")

        if st.form_submit_button("Add Expense"):
            new = pd.DataFrame([[date, category, amount, desc]],
                               columns=['Date', 'Category', 'Amount', 'Description'])

            st.session_state.expenses = pd.concat([st.session_state.expenses, new], ignore_index=True)

            st.success(f"Added ₹{amount} to {category} for {desc}")
            speak_fast(f"Added {amount} rupees to {category} for {desc}")

    st.divider()

    if st.button("🎙️ Add via Voice"):
        cmd = voice_input()
        amt, cat, desc = parse_voice_input(cmd)

        if amt:
            new = pd.DataFrame([[datetime.now().date(), cat, amt, desc]],
                               columns=['Date', 'Category', 'Amount', 'Description'])

            st.session_state.expenses = pd.concat([st.session_state.expenses, new], ignore_index=True)

            st.success(f"Added ₹{amt} to {cat} for {desc}")
            speak_fast(f"Added {amt} rupees to {cat} for {desc}")

        else:
            st.warning("Try saying: 'Add 200 to food for lunch'")


# -------------------------------------------------
# TAB 2 — DASHBOARD
# -------------------------------------------------
with tab2:
    st.subheader("📊 Overview")

    total = st.session_state.expenses["Amount"].sum()
    remaining = max(st.session_state.threshold - total, 0)

    c1, c2, c3 = st.columns(3)

    c1.markdown(f"<div class='card'><h4>Total Spent</h4><h2>₹{total:.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><h4>Threshold</h4><h2>₹{st.session_state.threshold:.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><h4>Remaining</h4><h2>₹{remaining:.2f}</h2></div>", unsafe_allow_html=True)

    st.slider("⚙️ Set Spending Limit (₹)", 500.0, 20000.0, key="threshold", step=100.0)

    if total >= st.session_state.threshold and not st.session_state.threshold_alerted:
        st.warning("⚠️ Spending limit reached!")
        speak_fast(f"You reached your spending limit of {st.session_state.threshold} rupees.")
        st.session_state.threshold_alerted = True

    elif total < st.session_state.threshold:
        st.session_state.threshold_alerted = False

    st.divider()

    st.subheader("🧾 Summary of Your Spending")

    if st.session_state.expenses.empty:
        st.info("No expenses yet!")

    else:
        summary = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()

        for _, row in summary.iterrows():
            st.write(f"💸 **{row['Category']}** → ₹{row['Amount']:.2f}")


# -------------------------------------------------
# TAB 3 — CHARTS
# -------------------------------------------------
with tab3:
    if st.session_state.expenses.empty:
        st.info("No data yet.")
    else:
        cat_sum = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()

        st.plotly_chart(px.pie(cat_sum,
                               names="Category",
                               values="Amount",
                               title="Expense Breakdown",
                               color_discrete_sequence=px.colors.sequential.Agsunset),
                        use_container_width=True)

        st.plotly_chart(px.bar(st.session_state.expenses,
                               x="Date",
                               y="Amount",
                               color="Category",
                               title="Daily Expenses",
                               color_discrete_sequence=px.colors.qualitative.Safe),
                        use_container_width=True)

        st.dataframe(st.session_state.expenses, use_container_width=True)


# -------------------------------------------------
# TAB 4 — AI CHAT
# -------------------------------------------------
with tab4:
    st.subheader("💬 Talk to Expenzo AI")

    q = st.text_input("Ask your spending question:")

    if st.button("Ask"):
        if st.session_state.expenses.empty:
            st.warning("Add expenses first.")
        else:
            summary = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()
            context = (
                f"Expense summary:\n"
                f"{summary.to_string(index=False)}\n"
                f"User question: {q}"
            )

            reply = ai_insight(context)
            st.success(reply)
            speak_fast(reply)

    if st.button("🎤 Voice Chat"):
        user_voice = voice_input()

        if st.session_state.expenses.empty:
            st.warning("Add expenses first.")
            speak_fast("Please add expenses first.")
        else:
            summary = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()
            context = (
                f"Expense summary:\n"
                f"{summary.to_string(index=False)}\n"
                f"User question: {user_voice}"
            )

            reply = ai_insight(context)
            st.success(reply)
            speak_fast(reply)
q