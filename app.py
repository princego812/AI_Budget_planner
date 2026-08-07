import streamlit as st
import pandas as pd
import json
import re
import time
import plotly.express as px
import plotly.graph_objects as go
from google import genai
from fpdf import FPDF

# ==========================================
# 1. PAGE CONFIGURATION & METADATA
# ==========================================
st.set_page_config(
    page_title="FinAI | Enterprise Wealth Terminal", 
    page_icon="💠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED CSS INJECTION (UI/UX)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
        
        :root {
            --bg-base: #0B0E14; --bg-panel: #151A23; --text-main: #F8FAFC;
            --text-muted: #94A3B8; --accent-primary: #10B981; --accent-glow: rgba(16, 185, 129, 0.3);
            --border-color: #2D3748;
        }
        
        .stApp { background-color: var(--bg-base); color: var(--text-main); font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4, h5, h6 { color: var(--text-main) !important; font-weight: 700 !important; letter-spacing: -0.03em; }
        p { color: var(--text-muted); line-height: 1.6; }
        
        [data-testid="stSidebar"] { background-color: var(--bg-panel); border-right: 1px solid var(--border-color); }
        [data-testid="stSidebar"] hr { border-color: var(--border-color); }
        
        .stButton > button {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: #FFFFFF !important; border: none !important; border-radius: 12px !important;
            font-weight: 600 !important; padding: 0.75rem 2rem !important; transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px var(--accent-glow); width: 100%;
        }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 24px var(--accent-glow); }
        
        .stDownloadButton > button { background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .stDownloadButton > button:hover { box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5); }
        
        [data-testid="metric-container"] {
            background: rgba(21, 26, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px); border-radius: 16px; padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); transition: transform 0.2s ease;
        }
        [data-testid="metric-container"]:hover { transform: translateY(-4px); border-color: rgba(16, 185, 129, 0.4); }
        [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 800 !important; color: var(--accent-primary) !important; font-family: 'JetBrains Mono', monospace; }
        [data-testid="stMetricLabel"] { font-size: 1rem !important; color: var(--text-muted) !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 1px; }
        
        [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); background: var(--bg-panel); }
        [data-testid="stTabs"] { background: transparent; }
        [data-baseweb="tab-list"] { gap: 1rem; background-color: var(--bg-panel); padding: 0.5rem; border-radius: 12px; border: 1px solid var(--border-color); }
        [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; padding: 0.5rem 1rem; color: var(--text-muted); font-weight: 600; border: none; }
        [aria-selected="true"] { background-color: rgba(16, 185, 129, 0.15) !important; color: var(--accent-primary) !important; }
        
        .globe-wrapper { display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 2rem; }
        .hologram-globe {
            width: 240px; height: 240px; border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #34D399, #10B981, #064E3B);
            box-shadow: 0 0 40px rgba(16, 185, 129, 0.3), inset -15px -15px 30px rgba(0,0,0,0.6), inset 15px 15px 30px rgba(255,255,255,0.2);
            animation: float 6s ease-in-out infinite, pulse-glow 4s ease-in-out infinite alternate; display: flex; justify-content: center; align-items: center; position: relative;
        }
        .globe-value { font-family: 'JetBrains Mono', monospace; color: #FFFFFF; font-size: 2.2rem; font-weight: 900; text-shadow: 0px 4px 15px rgba(0,0,0,0.8); z-index: 2; }
        .globe-subtitle { margin-top: 1.5rem; font-size: 1rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 3px; }
        
        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-15px); } 100% { transform: translateY(0px); } }
        @keyframes pulse-glow { 0% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.2); } 100% { box-shadow: 0 0 60px rgba(16, 185, 129, 0.5); } }
        
        [data-testid="stChatMessage"] { background-color: var(--bg-panel); border-radius: 12px; padding: 1rem; border: 1px solid var(--border-color); margin-bottom: 1rem; }
        [data-testid="stChatInput"] { background-color: var(--bg-panel) !important; border: 1px solid var(--accent-primary) !important; border-radius: 16px; box-shadow: 0 0 15px rgba(16, 185, 129, 0.1); }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 3. STATE MANAGEMENT & INITIALIZATION
# ==========================================
def init_state():
    defaults = {
        "setup_complete": False,
        "expenses_df": pd.DataFrame([{"Category": "Pending Setup...", "Amount": 0.0}]),
        "chat_history": [{"role": "assistant", "content": "💠 **Terminal Active.** Enter your income and list your expenses. I will architect your budget."}],
        "wealth_tier": "Unranked",
        "split_ratios": {"Savings": 20, "Short_Term": 20, "Long_Term": 30, "Fun_Money": 15, "Outing": 15}
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ==========================================
# 4. CORE FINANCIAL LOGIC & HELPERS
# ==========================================
def get_wealth_tier(savings_rate):
    if savings_rate >= 0.50: return "💎 Diamond (FIRE Achiever)"
    elif savings_rate >= 0.30: return "🥇 Gold (Wealth Builder)"
    elif savings_rate >= 0.15: return "🥈 Silver (Solid Foundation)"
    elif savings_rate > 0.0: return "🥉 Bronze (Getting Started)"
    return "⚠️ Unranked (Action Required)"

def calc_metrics(df, income):
    df_clean = df.copy()
    df_clean["Amount"] = pd.to_numeric(df_clean["Amount"], errors="coerce").fillna(0)
    
    total_alloc = df_clean["Amount"].sum()
    unalloc = income - total_alloc
    
    # Identify savings/investments
    sav_mask = df_clean["Category"].str.contains("invest|sav|emergency|short-term|long-term|stocks|crypto", case=False, na=False)
    actual_sav = df_clean.loc[sav_mask, "Amount"].sum() + (unalloc if unalloc > 0 else 0)
    sav_rate = actual_sav / income if income > 0 else 0
    
    return total_alloc, unalloc, actual_sav, sav_rate

def generate_pdf_report(income, alloc, unalloc, wealth, tier, df, curr):
    """Generates a PDF bytes object mapping currencies to safe ASCII text for FPDF"""
    curr_map = {"$": "USD", "₹": "INR", "€": "EUR", "£": "GBP"}
    safe_curr = curr_map.get(curr, "Units")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FinAI Enterprise - Wealth Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Wealth Tier: {tier}", ln=True)
    pdf.cell(0, 8, f"Monthly Income: {income:,.2f} {safe_curr}", ln=True)
    pdf.cell(0, 8, f"Total Allocated: {alloc:,.2f} {safe_curr}", ln=True)
    pdf.cell(0, 8, f"Unallocated Capital: {unalloc:,.2f} {safe_curr}", ln=True)
    pdf.cell(0, 8, f"Secured Net Wealth: {wealth:,.0f} {safe_curr}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Expense Breakdown Ledger:", ln=True)
    pdf.set_font("Arial", size=12)
    
    for _, row in df.iterrows():
        # Ensure text is safe for standard latin-1 PDF encoding
        cat = str(row['Category']).encode('latin-1', 'replace').decode('latin-1')
        amt = float(row['Amount'])
        pdf.cell(0, 8, f"- {cat}: {amt:,.2f} {safe_curr}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. SIDEBAR NAVIGATION & SETTINGS
# ==========================================
with st.sidebar:
    st.markdown("## 💠 FinAI Enterprise")
    st.caption("v2.1.0 | AI Wealth Architect")
    st.divider()
    
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("### ⚙️ Global Settings")
    currency_choice = st.selectbox("Base Currency", ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "Custom"])
    curr = st.text_input("Custom Symbol", value="¤") if currency_choice == "Custom" else currency_choice.split("(")[1].replace(")", "")
    
    income = st.number_input(f"Monthly Income ({curr})", min_value=0.0, value=5000.0, step=100.0)
    
    st.divider()
    st.markdown("### 📊 Portfolio & Lifestyle Split")
    st.caption("How your unallocated capital is distributed.")
    st.session_state.split_ratios["Savings"] = st.slider("Liquid Savings (%)", 0, 100, st.session_state.split_ratios["Savings"])
    st.session_state.split_ratios["Short_Term"] = st.slider("Short-Term Investing (%)", 0, 100, st.session_state.split_ratios["Short_Term"])
    st.session_state.split_ratios["Long_Term"] = st.slider("Long-Term Investing (%)", 0, 100, st.session_state.split_ratios["Long_Term"])
    st.session_state.split_ratios["Fun_Money"] = st.slider("Fun Money (%)", 0, 100, st.session_state.split_ratios["Fun_Money"])
    st.session_state.split_ratios["Outing"] = st.slider("Outing & Dining (%)", 0, 100, st.session_state.split_ratios["Outing"])
    
    total_ratio = sum(st.session_state.split_ratios.values())
    if total_ratio != 100:
        st.warning(f"Ratios total {total_ratio}%. Must equal exactly 100%.")
    
    st.divider()
    st.markdown("### 🔋 System Status")
    if api_key: st.success("Neural Link: ONLINE")
    else: st.error("Neural Link: OFFLINE (Key Required)")

# Calculate Core Data
total_alloc, unalloc, total_wealth, sav_rate = calc_metrics(st.session_state.expenses_df, income)
st.session_state.wealth_tier = get_wealth_tier(sav_rate)

# ==========================================
# 6. MAIN DASHBOARD HEADER
# ==========================================
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("Command Center")
    st.markdown(f"**Current Status:** Building Wealth | **Tier:** {st.session_state.wealth_tier}")
with col2:
    st.download_button(
        label="📄 Download PDF Report",
        data=generate_pdf_report(income, total_alloc, unalloc, total_wealth, st.session_state.wealth_tier, st.session_state.expenses_df, curr),
        file_name="FinAI_Wealth_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
with col3:
    if st.button("🔄 Hard Reset Data", use_container_width=True):
        st.session_state.expenses_df = pd.DataFrame([{"Category": "Pending Setup...", "Amount": 0.0}])
        st.session_state.setup_complete = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. TABBED INTERFACE
# ==========================================
tab_dash, tab_budget, tab_wealth, tab_ai = st.tabs([
    "🌐 Hologram Dashboard", 
    "💰 Budget Engine", 
    "📈 Wealth Allocator", 
    "🤖 Neural Advisor"
])

# ------------------------------------------
# TAB 1: HOLOGRAM DASHBOARD & CHARTS
# ------------------------------------------
with tab_dash:
    metric_cols = st.columns(3)
    metric_cols[0].metric("Total Income", f"{curr}{income:,.2f}")
    metric_cols[1].metric("Active Allocation", f"{curr}{total_alloc:,.2f}")
    metric_cols[2].metric("Unallocated Capital", f"{curr}{unalloc:,.2f}", 
                         delta="Deficit Risk" if unalloc < 0 else "Ready for Sweep", 
                         delta_color="inverse" if unalloc < 0 else "normal")
    
    st.divider()
    
    dash_col1, dash_col2 = st.columns([1, 1.2])
    with dash_col1:
        st.markdown(f"""
        <div class="globe-wrapper">
            <div class="hologram-globe">
                <div class="globe-value">{curr}{total_wealth:,.0f}</div>
            </div>
            <div class="globe-subtitle">Secured Net Wealth</div>
        </div>
        """, unsafe_allow_html=True)
        
    with dash_col2:
        if st.session_state.setup_complete and len(st.session_state.expenses_df) > 1:
            st.markdown("### Expense Distribution")
            df_plot = st.session_state.expenses_df.copy()
            df_plot = df_plot[df_plot["Amount"] > 0]
            
            fig = px.pie(df_plot, values='Amount', names='Category', hole=0.6, color_discrete_sequence=px.colors.sequential.Mint)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"), margin=dict(t=20, b=20, l=0, r=0))
            fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#151A23', width=2)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chart will generate once budget is populated via the Neural Advisor.")

# ------------------------------------------
# TAB 2: BUDGET ENGINE (DATA EDITOR)
# ------------------------------------------
with tab_budget:
    st.subheader("Dynamic Ledger")
    st.caption("Manually adjust your entries. AI generation will overwrite this grid.")
    
    edited_df = st.data_editor(
        st.session_state.expenses_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.TextColumn("Expense Category", required=True),
            "Amount": st.column_config.NumberColumn(f"Amount ({curr})", min_value=0.0, format="%.2f")
        }
    )
    if not edited_df.equals(st.session_state.expenses_df):
        st.session_state.expenses_df = edited_df
        st.rerun()

# ------------------------------------------
# TAB 3: WEALTH ALLOCATOR (THE SPLIT MECHANIC)
# ------------------------------------------
with tab_wealth:
    st.subheader("Automated Wealth Distribution")
    st.markdown("Route unallocated capital safely into your defined financial and lifestyle buckets.")
    
    if unalloc > 0:
        if total_ratio != 100:
            st.error(f"Cannot execute sweep. Check sidebar ratios. Current total: {total_ratio}%")
        else:
            st.success(f"**{curr}{unalloc:,.2f}** is awaiting distribution.")
            
            # Calculate values
            val_savings = unalloc * (st.session_state.split_ratios["Savings"] / 100)
            val_short = unalloc * (st.session_state.split_ratios["Short_Term"] / 100)
            val_long = unalloc * (st.session_state.split_ratios["Long_Term"] / 100)
            val_fun = unalloc * (st.session_state.split_ratios["Fun_Money"] / 100)
            val_outing = unalloc * (st.session_state.split_ratios["Outing"] / 100)
            
            # Display metrics in two rows
            w_col1, w_col2, w_col3 = st.columns(3)
            w_col1.metric("💧 Liquid Savings", f"{curr}{val_savings:,.2f}")
            w_col2.metric("📈 Short-Term Investing", f"{curr}{val_short:,.2f}")
            w_col3.metric("🏛️ Long-Term Wealth", f"{curr}{val_long:,.2f}")
            
            w_col4, w_col5, _ = st.columns(3)
            w_col4.metric("🎮 Fun Money", f"{curr}{val_fun:,.2f}")
            w_col5.metric("🍸 Outing & Dining", f"{curr}{val_outing:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Execute Portfolio Sweep"):
                df = st.session_state.expenses_df
                
                def add_or_update(current_df, cat, amt):
                    if cat in current_df["Category"].values:
                        current_df.loc[current_df["Category"] == cat, "Amount"] += amt
                    else:
                        new_row = pd.DataFrame([{"Category": cat, "Amount": amt}])
                        current_df = pd.concat([current_df, new_row], ignore_index=True)
                    return current_df
                
                if val_savings > 0: df = add_or_update(df, "Savings (Liquid)", val_savings)
                if val_short > 0: df = add_or_update(df, "Investments (Short-Term)", val_short)
                if val_long > 0: df = add_or_update(df, "Investments (Long-Term)", val_long)
                if val_fun > 0: df = add_or_update(df, "Fun Money (Lifestyle)", val_fun)
                if val_outing > 0: df = add_or_update(df, "Outing & Dining (Lifestyle)", val_outing)
                
                st.session_state.expenses_df = df
                st.rerun()
                
    elif unalloc < 0:
        st.error(f"Cannot distribute wealth. You are currently running a deficit of {curr}{abs(unalloc):,.2f}.")
    else:
        st.info("Zero-Based Budget achieved. No unallocated funds remaining to sweep.")
        
    st.divider()
    st.subheader("Current Allocations")
    df_port = st.session_state.expenses_df
    port_mask = df_port["Category"].str.contains("sav|invest|short|long|fun|outing", case=False, na=False)
    port_data = df_port.loc[port_mask]
    
    if not port_data.empty and port_data["Amount"].sum() > 0:
        fig_bar = px.bar(port_data, x='Amount', y='Category', orientation='h', color='Category', color_discrete_sequence=px.colors.sequential.Emrld)
        fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"))
        st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------
# TAB 4: NEURAL ADVISOR (AI CHAT)
# ------------------------------------------
with tab_ai:
    st.subheader("FinAI Neural Network")
    
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    if prompt := st.chat_input("Enter expenses or ask for financial advice..."):
        if not api_key:
            st.error("Please insert your Gemini API Key in the sidebar.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
            client = genai.Client(api_key=api_key)
            
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Processing financial data..."):
                        try:
                            if not st.session_state.setup_complete:
                                sys_prompt = f"""
                                The user earns {curr}{income}. They are describing their expenses: "{prompt}"
                                
                                Task 1: Extract expenses into a JSON array. 
                                Task 2: If there is remaining money ({income} minus total expenses), DO NOT dump it all into one 'Investments' category. 
                                Instead, split the remaining money into five specific categories based on default ratios:
                                - "Savings (Liquid)" (20% of remainder)
                                - "Investments (Short-Term)" (20% of remainder)
                                - "Investments (Long-Term)" (30% of remainder)
                                - "Fun Money (Lifestyle)" (15% of remainder)
                                - "Outing & Dining (Lifestyle)" (15% of remainder)
                                
                                Format EXACTLY as: [{{"Category": "Rent", "Amount": 1000}}]
                                
                                Task 3: Type exactly '===ADVICE===' after the JSON.
                                Task 4: Provide a brief financial analysis covering their savings rate and immediate risks.
                                """
                                response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=sys_prompt)
                                
                                if "===ADVICE===" in response.text:
                                    json_part, advice_part = response.text.split("===ADVICE===")
                                    match = re.search(r'\[.*\]', json_part, re.DOTALL)
                                    
                                    if match:
                                        st.session_state.expenses_df = pd.DataFrame(json.loads(match.group(0)))
                                        st.session_state.setup_complete = True
                                        st.markdown(advice_part.strip())
                                        st.session_state.chat_history.append({"role": "assistant", "content": advice_part.strip()})
                                        time.sleep(1.5)
                                        st.rerun()
                                    else:
                                        msg = "Could not parse numbers. Please list as 'Rent 1000, Food 500'."
                                        st.markdown(msg)
                                        st.session_state.chat_history.append({"role": "assistant", "content": msg})
                                else:
                                    st.error("AI formulation error. Please retry.")
                                    
                            else:
                                exp_str = st.session_state.expenses_df.to_string(index=False)
                                sys_prompt = f"""
                                You are FinAI. 
                                Income: {curr}{income} | Unallocated: {curr}{unalloc} | Wealth Tier: {st.session_state.wealth_tier}
                                Budget: \n{exp_str}
                                
                                Answer directly, technically, and ruthlessly optimize their wealth. Keep it under 4 sentences.
                                """
                                response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=f"{sys_prompt}\n\nUser Question: {prompt}")
                                st.markdown(response.text)
                                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                                
                        except Exception as e:
                            st.error(f"Neural API Error: {e}")
