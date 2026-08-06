import streamlit as st
import pandas as pd
from google import genai
import time
import json
import re

# --- Page Configuration ---
st.set_page_config(page_title="AI Budget Planner", page_icon="💸", layout="wide")

st.title("💸 AI Personal Budget Planner")
st.write("Track expenses, auto-allocate with AI, monitor your savings goals, and get expert financial advice.")

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your API key from Google AI Studio")

# Currency Selector
currency_choice = st.sidebar.selectbox(
    "Select Currency",
    ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "Custom"]
)

if currency_choice == "Custom":
    currency_sym = st.sidebar.text_input("Enter Custom Symbol", value="¤")
else:
    # Extract the symbol from the string (e.g., extracts "$" from "USD ($)")
    currency_sym = currency_choice.split("(")[1].replace(")", "")

# --- 1. Income & Goals ---
st.subheader("1. Income & Goals")
col1, col2 = st.columns(2)
with col1:
    income = st.number_input(f"Monthly Income ({currency_sym})", min_value=0.0, value=5000.0, step=100.0)
with col2:
    savings_goal = st.number_input(f"Monthly Savings Goal ({currency_sym})", min_value=0.0, value=1000.0, step=100.0)

# Initialize default dataframe in session state
if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame([
        {"Category": "Housing", "Amount": 1500.0},
        {"Category": "Groceries", "Amount": 400.0},
        {"Category": "Utilities", "Amount": 200.0},
        {"Category": "Transportation", "Amount": 150.0},
        {"Category": "Fun Money", "Amount": 200.0},
        {"Category": "Investments", "Amount": 300.0},
        {"Category": "Emergency Fund", "Amount": 100.0},
    ])

# --- 2. AI Auto-Allocator ---
st.subheader("2. ✨ AI Budget Allocator")
st.write("Not sure where to start? Let AI distribute your income into a balanced, zero-based budget.")
if st.button("Auto-Allocate My Budget"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to use the AI Allocator.")
    else:
        with st.spinner("AI is calculating the optimal allocation..."):
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are a master financial planner. Based on a monthly income of {income}, create a realistic and mathematically balanced monthly budget. 
            Include standard categories (Housing, Groceries, Utilities) but you MUST also include:
            - "Fun Money" or "Entertainment"
            - "Investments" 
            - "Emergency Fund"
            
            Ensure the total of all Amounts equals exactly {income}.
            
            Respond STRICTLY with a raw JSON array of objects. Do not include markdown code blocks or any other text.
            Example format:
            [
              {{"Category": "Housing", "Amount": 1500.0}},
              {{"Category": "Fun Money", "Amount": 300.0}}
            ]
            """
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=prompt
                    )
                    
                    # Clean up response to safely extract JSON
                    raw_text = response.text.strip()
                    raw_text = re.sub(r'^```json', '', raw_text)
                    raw_text = re.sub(r'^```', '', raw_text)
                    raw_text = re.sub(r'```$', '', raw_text).strip()
                    
                    start = raw_text.find('[')
                    end = raw_text.rfind(']') + 1
                    json_str = raw_text[start:end]
                    
                    # Parse and update table
                    new_expenses = json.loads(json_str)
                    st.session_state.expenses_df = pd.DataFrame(new_expenses)
                    st.rerun()  # Instantly refreshes the page to show new data
                    
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2 ** (attempt + 1))
                    else:
                        st.error(f"Failed to auto-allocate. Error: {e}")
                        break

# --- 3. Monthly Expenses (Interactive Table) ---
st.subheader("3. Monthly Expenses")
edited_df = st.data_editor(st.session_state.expenses_df, num_rows="dynamic", use_container_width=True)

# Save manual edits back to session state
st.session_state.expenses_df = edited_df

# --- 4. Budget Summary ---
st.subheader("4. Budget Summary")
total_allocated = edited_df["Amount"].sum()
unallocated_balance = income - total_allocated

# Calculate savings progress (summing up any row with "invest", "sav", or "emergency" in the name)
savings_mask = edited_df["Category"].str.contains("invest|sav|emergency", case=False, na=False)
actual_savings = edited_df.loc[savings_mask, "Amount"].sum() + (unallocated_balance if unallocated_balance > 0 else 0)
savings_progress = (actual_savings / savings_goal) * 100 if savings_goal > 0 else 0

col3, col4, col5 = st.columns(3)
col3.metric("Total Allocated/Spent", f"{currency_sym}{total_allocated:,.2f}", f"{(total_allocated/income)*100:.1f}% of income" if income > 0 else "")
col4.metric("Unallocated Balance", f"{currency_sym}{unallocated_balance:,.2f}", "Aim for $0 (Zero-Based Budgeting)")
col5.metric("Goal Progress", f"{savings_progress:.1f}%", f"{currency_sym}{actual_savings:,.2f} tracking to savings")

# --- 5. AI Financial Advisor ---
st.subheader("5. 🤖 AI Financial Advisor")
if st.button("Generate Actionable Advice"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to unlock the AI advisor.")
    else:
        with st.spinner("Analyzing your financial distribution..."):
            client = genai.Client(api_key=api_key)
            expense_str = edited_df.to_string(index=False)
            
            prompt = f"""
            You are an expert financial advisor. Analyze this monthly budget:
            
            - Currency: {currency_sym}
            - Monthly Income: {currency_sym}{income}
            - Savings Goal: {currency_sym}{savings_goal}
            - Total Allocated: {currency_sym}{total_allocated}
            - Unallocated Balance: {currency_sym}{unallocated_balance}
            
            Expense Breakdown:
            {expense_str}
            
            Please provide:
            1. A brief evaluation of the budget allocation (compare it to frameworks like 50/30/20).
            2. Identify any specific categories where spending is risky or praise solid emergency/investment allocations.
            3. Provide 3 specific, actionable steps to help the user optimize this budget and hit their {currency_sym}{savings_goal} goal.
            
            Format with bolding and bullet points for readability. Keep it concise.
            """
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=prompt
                    )
                    
                    st.info("💡 AI Recommendations")
                    st.write(response.text)
                    break
                    
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        st.toast(f"Server busy. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        st.error(f"An error occurred while calling the Gemini API: {e}")
                        break
