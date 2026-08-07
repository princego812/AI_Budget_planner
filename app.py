import streamlit as st
import pandas as pd
from google import genai
import json
import re

# --- Page Configuration ---
st.set_page_config(page_title="FinAI | Smart Wealth", page_icon="🟢", layout="wide")

# --- Custom High UI/UX CSS ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #FFFFFF; font-family: -apple-system, sans-serif; }
    [data-testid="stSidebar"] { background-color: #000000; }
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.04em; }
    .stMarkdown p, .stCaption { color: #B3B3B3 !important; }
    .stButton>button {
        background-color: #1DB954 !important; color: #000000 !important;
        border: none !important; border-radius: 500px !important; font-weight: 700 !important;
        padding: 0.5rem 2rem !important; transition: all 0.2s ease !important;
    }
    .stButton>button:hover { background-color: #1ed760 !important; transform: scale(1.04); }
    [data-testid="stDataFrame"] { background-color: #181818; border-radius: 8px; padding: 10px; border: none; }
    .globe-container { display: flex; justify-content: center; align-items: center; flex-direction: column; margin: 3rem 0; }
    .globe {
        width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #1ed760, #1DB954, #121212);
        box-shadow: 0 0 40px rgba(29, 185, 84, 0.3), inset -15px -15px 30px rgba(0,0,0,0.7);
        animation: pulse 4s infinite alternate; display: flex; justify-content: center;
        align-items: center; text-align: center; position: relative;
    }
    .globe-text { position: absolute; color: #FFFFFF; font-size: 1.8rem; font-weight: 900; text-shadow: 0px 2px 10px rgba(0,0,0,0.8); z-index: 2; }
    .globe-label { margin-top: 20px; font-size: 1rem; color: #B3B3B3; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; }
    @keyframes pulse { 0% { box-shadow: 0 0 30px rgba(29, 185, 84, 0.2); transform: scale(1); } 100% { box-shadow: 0 0 50px rgba(29, 185, 84, 0.5); transform: scale(1.02); } }
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border-radius: 12px; }
    [data-testid="stChatInput"] textarea { color: #000000 !important; font-weight: 500; }
    [data-testid="stChatInput"] button { color: #000000 !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: #666666 !important; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.title("FinAI System")
st.sidebar.info("Allocate funds intelligently, track expenses, and chat with an AI advisor.")
st.sidebar.divider()
api_key = st.sidebar.text_input("Gemini API Key", type="password")

currency_choice = st.sidebar.selectbox("Select Currency", ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "Custom"])
currency_sym = st.sidebar.text_input("Custom Symbol", value="¤") if currency_choice == "Custom" else currency_choice.split("(")[1].replace(")", "")

# --- State Initialization ---
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False

if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame([{"Category": "Pending Setup...", "Amount": 0.0}])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "👋 Hello! To get started, please tell me your monthly income, and list out your typical daily and monthly expenses (e.g., rent, groceries, daily coffee, travel). I will build your budget from there!"}
    ]

# --- 1. Core Inputs ---
st.title("AI Budget Terminal")

col1, col2 = st.columns(2)
with col1:
    income = st.number_input(f"Monthly Income ({currency_sym})", min_value=0.0, value=5000.0, step=100.0)
with col2:
    savings_goal = st.number_input(f"Savings Target ({currency_sym})", min_value=0.0, value=1000.0, step=100.0)

# --- 2. Interactive Data Grid ---
st.subheader("Expense Breakdown")
if not st.session_state.setup_complete:
    st.caption("Awaiting your expense details in the chat below to auto-generate this table...")

edited_df = st.data_editor(st.session_state.expenses_df, num_rows="dynamic", use_container_width=True)
st.session_state.expenses_df = edited_df

# --- Calculations ---
total_allocated = edited_df["Amount"].sum()
unallocated_balance = income - total_allocated
savings_mask = edited_df["Category"].str.contains("invest|sav|emergency", case=False, na=False)
actual_savings = edited_df.loc[savings_mask, "Amount"].sum() + (unallocated_balance if unallocated_balance > 0 else 0)

# --- Human-Readable Context Alerts & Sweep Button ---
if st.session_state.setup_complete:
    if unallocated_balance < 0:
        st.error(f"⚠️ You are over budget by {currency_sym}{abs(unallocated_balance):,.2f}! Reduce expenses in the table above.")
    elif unallocated_balance > 0:
        st.info(f"💡 You have {currency_sym}{unallocated_balance:,.2f} unallocated.")
        if st.button(f"Sweep {currency_sym}{unallocated_balance:,.2f} to Investments"):
            # Add unallocated money to Investments row, or create one if it doesn't exist
            if "Investments" in edited_df["Category"].values:
                st.session_state.expenses_df.loc[st.session_state.expenses_df["Category"] == "Investments", "Amount"] += unallocated_balance
            else:
                new_row = pd.DataFrame([{"Category": "Investments", "Amount": unallocated_balance}])
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_row], ignore_index=True)
            st.rerun()
    else:
        st.success("🎯 Perfect Zero-Based Budget Achieved!")

# --- 3. The Green Globe Dashboard ---
st.markdown("---")
st.markdown(f"""
<div class="globe-container">
    <div class="globe">
        <div class="globe-text">{currency_sym}{actual_savings:,.0f}</div>
    </div>
    <div class="globe-label">Total Wealth Secured</div>
</div>
""", unsafe_allow_html=True)

col3, col4 = st.columns(2)
col3.metric("Total Allocated", f"{currency_sym}{total_allocated:,.2f}")
col4.metric("Unallocated (Zero-Based)", f"{currency_sym}{unallocated_balance:,.2f}")

# --- 4. Interactive Chat (Onboarding + Free Chat) ---
st.markdown("---")
st.subheader("FinAI Advisor")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message FinAI..."):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = genai.Client(api_key=api_key)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
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
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=sys_prompt)
                        
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
                            model="gemini-2.5-flash", 
                            contents=f"{sys_prompt}\n\nUser Question: {prompt}"
                        )
                        st.markdown(response.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})

                except Exception as e:
                    st.error(f"API Error: {e}")
