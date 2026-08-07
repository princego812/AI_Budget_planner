import streamlit as st
import pandas as pd
from google import genai
import json
import re
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="FinAI | Smart Wealth", 
    page_icon="🟢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom High UI/UX CSS ---
st.markdown("""
<style>
    /* Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { 
        background-color: #0E1117; 
        color: #FAFAFA; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Headings */
    h1, h2, h3 { 
        color: #FFFFFF !important; 
        font-weight: 700 !important; 
        letter-spacing: -0.02em; 
    }
    
    /* Streamlit Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #161A25; 
        border-right: 1px solid #2A2F3D;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #1DB954 0%, #179343 100%) !important;
        color: #FFFFFF !important;
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important; 
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(29, 185, 84, 0.2);
    }
    .stButton>button:hover { 
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(29, 185, 84, 0.4);
    }
    
    /* Metric Cards (Glassmorphism) */
    [data-testid="metric-container"] {
        background: rgba(30, 34, 45, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #1DB954 !important;
    }
    
    /* Data Editor */
    [data-testid="stDataFrame"] { 
        border-radius: 12px; 
        overflow: hidden;
        border: 1px solid #2A2F3D;
    }
    
    /* Wealth Globe Animation */
    .globe-container { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        flex-direction: column; 
        margin: 2rem 0; 
    }
    .globe {
        width: 180px; 
        height: 180px; 
        border-radius: 50%;
        background: radial-gradient(circle at 35% 35%, #24E269, #1DB954, #0A421D);
        box-shadow: 0 0 30px rgba(29, 185, 84, 0.2), inset -10px -10px 20px rgba(0,0,0,0.5);
        animation: pulse-glow 4s ease-in-out infinite alternate; 
        display: flex; 
        justify-content: center;
        align-items: center; 
        text-align: center; 
        position: relative;
    }
    .globe-text { 
        position: absolute; 
        color: #FFFFFF; 
        font-size: 1.8rem; 
        font-weight: 800; 
        text-shadow: 0px 4px 15px rgba(0,0,0,0.5); 
        z-index: 2; 
    }
    .globe-label { 
        margin-top: 15px; 
        font-size: 0.9rem; 
        color: #A0AEC0; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
    }
    @keyframes pulse-glow { 
        0% { box-shadow: 0 0 20px rgba(29, 185, 84, 0.2); transform: scale(1); } 
        100% { box-shadow: 0 0 50px rgba(29, 185, 84, 0.4); transform: scale(1.03); } 
    }
    
    /* Chat Input Stylization */
    [data-testid="stChatInput"] { 
        background-color: #161A25 !important; 
        border: 1px solid #2A2F3D !important;
        border-radius: 12px; 
    }
    [data-testid="stChatInput"] textarea { 
        color: #FFFFFF !important; 
        font-weight: 400; 
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2529/2529396.png", width=60) # Placeholder logo
    st.title("FinAI Setup")
    st.caption("Allocate funds intelligently and chat with your AI advisor.")
    st.divider()
    
    api_key = st.text_input("Gemini API Key", type="password", help="Get this from Google AI Studio")
    currency_choice = st.selectbox("Currency", ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "Custom"])
    currency_sym = st.text_input("Custom Symbol", value="¤") if currency_choice == "Custom" else currency_choice.split("(")[1].replace(")", "")
    
    st.divider()
    st.markdown("### 🟢 System Status")
    if api_key:
        st.success("API Key Provided")
    else:
        st.warning("Awaiting API Key")

# --- State Initialization ---
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False

if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame([{"Category": "Pending Setup...", "Amount": 0.0}])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "👋 **Hello!** To get started, please tell me your monthly income, and list out your typical daily and monthly expenses (e.g., rent, groceries, daily coffee, travel). I will build your budget from there!"}
    ]

# --- App Header ---
st.title("AI Budget Terminal")
st.markdown("Automate your wealth building with Zero-Based Budgeting.")
st.markdown("<br>", unsafe_allow_html=True)

# --- Top Dashboard Layout ---
top_col1, top_col2, top_col3 = st.columns([1, 1, 1])

with top_col1:
    income = st.number_input(f"Monthly Income ({currency_sym})", min_value=0.0, value=5000.0, step=100.0)
with top_col2:
    savings_goal = st.number_input(f"Savings Target ({currency_sym})", min_value=0.0, value=1000.0, step=100.0)

# --- Calculations (Happens before rendering metrics) ---
edited_df = st.session_state.expenses_df
total_allocated = edited_df["Amount"].sum()
unallocated_balance = income - total_allocated
savings_mask = edited_df["Category"].str.contains("invest|sav|emergency", case=False, na=False)
actual_savings = edited_df.loc[savings_mask, "Amount"].sum() + (unallocated_balance if unallocated_balance > 0 else 0)

with top_col3:
    st.metric("Unallocated Funds", f"{currency_sym}{unallocated_balance:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# --- Main Interface ---
main_col1, main_col2 = st.columns([1.5, 1], gap="large")

with main_col1:
    st.subheader("📊 Expense Breakdown")
    if not st.session_state.setup_complete:
        st.caption("Awaiting your expense details in the chat below to auto-generate this table...")

    # Data Editor
    edited_df = st.data_editor(
        st.session_state.expenses_df, 
        num_rows="dynamic", 
        use_container_width=True,
        hide_index=True
    )
    st.session_state.expenses_df = edited_df

    # Sweeper & Alerts
    if st.session_state.setup_complete:
        st.markdown("<br>", unsafe_allow_html=True)
        if unallocated_balance < 0:
            st.error(f"⚠️ **Over Budget:** You need to reduce expenses by {currency_sym}{abs(unallocated_balance):,.2f}.")
        elif unallocated_balance > 0:
            st.info(f"💡 **Action Required:** You have {currency_sym}{unallocated_balance:,.2f} unallocated.")
            if st.button(f"Sweep {currency_sym}{unallocated_balance:,.2f} to Investments 🚀"):
                if "Investments" in edited_df["Category"].values:
                    st.session_state.expenses_df.loc[st.session_state.expenses_df["Category"] == "Investments", "Amount"] += unallocated_balance
                else:
                    new_row = pd.DataFrame([{"Category": "Investments", "Amount": unallocated_balance}])
                    st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_row], ignore_index=True)
                st.rerun()
        else:
            st.success("🎯 **Perfect Zero-Based Budget Achieved!** Every dollar has a job.")

with main_col2:
    st.subheader("📈 Wealth Snapshot")
    
    # Render Globe
    st.markdown(f"""
    <div class="globe-container">
        <div class="globe">
            <div class="globe-text">{currency_sym}{actual_savings:,.0f}</div>
        </div>
        <div class="globe-label">Total Wealth Secured</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.metric("Total Allocated", f"{currency_sym}{total_allocated:,.2f}")
    
    # Visual Progress bar for savings target
    if savings_goal > 0:
        progress = min(actual_savings / savings_goal, 1.0)
        st.caption(f"Savings Goal Progress: {progress*100:.1f}%")
        st.progress(progress)


# --- Interactive Chat ---
st.divider()
st.subheader("💬 FinAI Advisor")

# Create a container for chat history so it doesn't take up the whole screen immediately
chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Message FinAI (e.g., 'I spend 1200 on rent, 400 on food...')"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar to activate the AI.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = genai.Client(api_key=api_key)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your finances..."):
                try:
                    if not st.session_state.setup_complete:
                        # PHASE 1: Parse expenses, generate budget JSON, and give advice
                        sys_prompt = f"""
                        The user earns {currency_sym}{income}. They are describing their expenses: "{prompt}"
                        
                        Task 1: Extract their expenses and create a realistic budget JSON array. Add an "Investments" or "Emergency Fund" category if unallocated money remains. 
                        Format EXACTLY as: [{{"Category": "Rent", "Amount": 1000}}]
                        
                        Task 2: Type exactly '===ADVICE===' after the JSON.
                        
                        Task 3: After '===ADVICE===', write a brief message containing:
                        - A summary of what you allocated.
                        - 2-3 Bullet points about Risks in their current spending.
                        - 1 piece of Advice to optimize.
                        """
                        response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=sys_prompt)
                        
                        if "===ADVICE===" in response.text:
                            json_part, advice_part = response.text.split("===ADVICE===")
                            
                            # Parse JSON strictly
                            match = re.search(r'\[.*\]', json_part, re.DOTALL)
                            if match:
                                st.session_state.expenses_df = pd.DataFrame(json.loads(match.group(0)))
                                st.session_state.setup_complete = True
                                
                                st.markdown(advice_part.strip())
                                st.session_state.chat_history.append({"role": "assistant", "content": advice_part.strip()})
                                
                                time.sleep(2) # Give user a second to read before refresh populates the table
                                st.rerun()
                            else:
                                msg = "I couldn't quite extract the numbers. Could you list them clearly (e.g., Rent 1000, Food 500)?"
                                st.markdown(msg)
                                st.session_state.chat_history.append({"role": "assistant", "content": msg})
                        else:
                            st.error("AI response format failed. Please try again.")

                    else:
                        # PHASE 2: Free Chat with existing budget context
                        expense_str = edited_df.to_string(index=False)
                        sys_prompt = f"""
                        You are FinAI, a financial advisor. 
                        Context: Income {currency_sym}{income} | Unallocated: {currency_sym}{unallocated_balance}
                        Budget Breakdown: \n{expense_str}
                        
                        Answer the user's question directly, briefly, and accurately based on their current budget. Keep it under 4 sentences.
                        """
                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite", 
                            contents=f"{sys_prompt}\n\nUser Question: {prompt}"
                        )
                        st.markdown(response.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})

                except Exception as e:
                    st.error(f"API Error: {e}")
