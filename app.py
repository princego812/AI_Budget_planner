import streamlit as st
import pandas as pd
from google import genai

# --- Page Configuration ---
st.set_page_config(page_title="AI Budget Planner", page_icon="💸", layout="wide")

st.title("💸 AI Personal Budget Planner")
st.write("Track expenses, monitor your savings goals, and get AI-powered financial advice.")

# --- Sidebar Configuration ---
st.sidebar.header("API Configuration")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get your API key from Google AI Studio")

# --- 1. Core Budget Inputs ---
st.subheader("1. Income & Goals")
col1, col2 = st.columns(2)
with col1:
    income = st.number_input("Monthly Income ($)", min_value=0.0, value=5000.0, step=100.0)
with col2:
    savings_goal = st.number_input("Monthly Savings Goal ($)", min_value=0.0, value=1000.0, step=100.0)

# --- 2. Expense Tracking (Pandas) ---
st.subheader("2. Monthly Expenses")
st.write("Edit your expenses below. You can add or delete rows directly in the interactive table.")

# Initialize default dataframe if not present in session state
if "expenses_df" not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame(
        [
            {"Category": "Rent/Mortgage", "Amount": 1500.0},
            {"Category": "Groceries", "Amount": 400.0},
            {"Category": "Utilities", "Amount": 200.0},
            {"Category": "Transportation", "Amount": 150.0},
            {"Category": "Entertainment", "Amount": 200.0},
            {"Category": "Miscellaneous", "Amount": 100.0},
        ]
    )

# Streamlit's data editor natively handles pandas DataFrames
edited_df = st.data_editor(st.session_state.expenses_df, num_rows="dynamic", use_container_width=True)

# --- 3. Rule-Based Calculator ---
st.subheader("3. Budget Summary")
total_expenses = edited_df["Amount"].sum()
remaining_balance = income - total_expenses
savings_progress = (remaining_balance / savings_goal) * 100 if savings_goal > 0 else 0

# Metrics display
col3, col4, col5 = st.columns(3)
col3.metric("Total Expenses", f"${total_expenses:,.2f}", f"{(total_expenses/income)*100:.1f}% of income" if income > 0 else "")
col4.metric("Actual Savings", f"${remaining_balance:,.2f}", f"${remaining_balance - savings_goal:,.2f} vs goal")
col5.metric("Goal Progress", f"{savings_progress:.1f}%")

# --- 4. AI Financial Advisor ---
st.subheader("4. 🤖 AI Financial Advisor")
if st.button("Generate Actionable Advice"):
    if not api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to unlock the AI advisor.")
    else:
        with st.spinner("Analyzing your budget constraints..."):
            try:
                # Initialize the standard Google GenAI client
                client = genai.Client(api_key=api_key)
                
                # Format dataframe to a readable string for the prompt
                expense_str = edited_df.to_string(index=False)
                
                prompt = f"""
                You are an expert financial advisor. Analyze the following monthly budget:
                
                - Monthly Income: ${income}
                - Savings Goal: ${savings_goal}
                - Total Expenses: ${total_expenses}
                - Remaining Balance (Actual Savings): ${remaining_balance}
                
                Expense Breakdown:
                {expense_str}
                
                Please provide:
                1. A brief evaluation of the budget allocation (compare it to standard frameworks like the 50/30/20 rule).
                2. Identify any specific categories where spending is disproportionately high.
                3. Provide 3 specific, actionable steps to help the user achieve or exceed their savings goal.
                
                Format with bolding and bullet points for readability. Keep it concise.
                """
                
                # Generate content using Gemini 2.5 Flash
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
                
                st.info("💡 AI Recommendations")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while calling the Gemini API: {e}")
