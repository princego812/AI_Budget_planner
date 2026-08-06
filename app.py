import os
import io
import contextlib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

# Set page configuration
st.set_page_config(
    page_title="AI Powered Data Analyst Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered Data Analyst Agent")
st.markdown("Upload your dataset (CSV/Excel) to perform automated EDA, generate charts (Univariate, Bivariate, Multivariate), execute dynamic analysis, and chat with your data!")

# --- BACKEND FUNCTION ---
def perform_eda(df: pd.DataFrame):
    """Performs basic Exploratory Data Analysis (EDA) on a pandas DataFrame.
    
    Parameters:
    df (pd.DataFrame): The dataset to analyze.
    """
    eda_output = []
    eda_output.append("=" * 60)
    eda_output.append(" 📊 EXPLORATORY DATA ANALYSIS (EDA) REPORT")
    eda_output.append("=" * 60)
    
    # 1. Dataset Shape
    eda_output.append("\n[1] DATASET SHAPE")
    eda_output.append(f"Total Rows: {df.shape[0]}")
    eda_output.append(f"Total Columns: {df.shape[1]}")
    
    # 2. Columns & Data Types
    eda_output.append("\n[2] COLUMNS AND DATA TYPES")
    dtype_df = pd.DataFrame({
        "Data Type": df.dtypes,
        "Non-Null Count": df.notnull().sum(),
        "Null Count": df.isnull().sum()
    })
    eda_output.append(dtype_df.to_string())
    
    # 3. Missing Values Summary
    eda_output.append("\n[3] MISSING VALUES SUMMARY")
    missing_count = df.isnull().sum()
    missing_percentage = (df.isnull().sum() / len(df)) * 100
    missing_df = pd.DataFrame({
        "Missing Values": missing_count,
        "Percentage (%)": missing_percentage
    })
    missing_df = missing_df[missing_df["Missing Values"] > 0].sort_values(by="Missing Values", ascending=False)
    
    if missing_df.empty:
        eda_output.append("🎉 Great news! There are no missing values in this dataset.")
    else:
        eda_output.append(missing_df.to_string())
        
    # 4. Duplicate Rows
    eda_output.append("\n[4] DUPLICATE ROWS")
    duplicates = df.duplicated().sum()
    eda_output.append(f"Number of duplicate rows: {duplicates} ({(duplicates / len(df)) * 100:.2f}%)")
    
    # 5. Statistical Summary (Numerical Features)
    eda_output.append("\n[5] STATISTICAL SUMMARY (Numerical Columns)")
    num_df = df.select_dtypes(include=['number'])
    if not num_df.empty:
        eda_output.append(num_df.describe().T.to_string())
    else:
        eda_output.append("No numerical columns found in the dataset.")
        
    # 6. Statistical Summary (Categorical Features)
    eda_output.append("\n[6] STATISTICAL SUMMARY (Categorical Columns)")
    cat_df = df.select_dtypes(include=['object', 'category'])
    if not cat_df.empty:
        eda_output.append(cat_df.describe().T.to_string())
    else:
        eda_output.append("No categorical columns found in the dataset.")
        
    eda_output.append("\n" + "=" * 60)
    eda_output.append(" END OF EDA REPORT")
    eda_output.append("=" * 60)
    
    return "\n".join(eda_output)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration & Data Input")
api_key = st.sidebar.text_input("Enter Groq / OpenAI API Key", type="password")
model_name = st.sidebar.selectbox("Select Model", ["gpt-4o-mini", "llama-3.3-70b-versatile", "gpt-4o"])
provider = "openai" if "gpt" in model_name else "groq"

# If using groq, make sure provider/env is handled appropriately or passed via init_chat_model
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key if "gpt" in model_name else ""
    os.environ["GROQ_API_KEY"] = api_key if "groq" in model_name else ""

uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        try:
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            else:
                return pd.read_excel(file)
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None

    df = load_data(uploaded_file)
    
    if df is not None:
        st.success("File successfully uploaded!")
        
        # Tabs for layout
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Automated EDA", "📈 Visualizations", "⚡ AI Code Executor", "💬 Chat with Data"])
        
        # --- TAB 1: AUTOMATED EDA ---
        with tab1:
            st.subheader("Automated Exploratory Data Analysis Report")
            eda_report_text = perform_eda(df)
            st.text(eda_report_text)
            
            st.subheader("Raw Data Preview")
            st.dataframe(df.head(10))

        # --- TAB 2: VISUALIZATIONS ---
        with tab2:
            st.subheader("Automated Analysis & Visualizations")
            
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Univariate Analysis
            st.markdown("### 📊 Univariate Analysis")
            uni_col = st.selectbox("Select column for Univariate Analysis", df.columns)
            if uni_col:
                fig, ax = plt.subplots(figsize=(8, 4))
                if uni_col in num_cols:
                    sns.histplot(df[uni_col], kde=True, ax=ax, color='skyblue')
                    ax.set_title(f"Distribution of {uni_col}")
                else:
                    sns.countplot(x=df[uni_col], ax=ax, order=df[uni_col].value_counts().index[:10], palette='viridis')
                    ax.set_title(f"Count Plot of {uni_col}")
                    plt.xticks(rotation=45)
                st.pyplot(fig)
            
            # Bivariate Analysis
            st.markdown("### 📈 Bivariate Analysis")
            if len(df.columns) >= 2:
                col1 = st.selectbox("Select X-axis / Feature 1", df.columns, key="biv_1")
                col2 = st.selectbox("Select Y-axis / Feature 2", df.columns, key="biv_2", index=min(1, len(df.columns)-1))
                
                fig, ax = plt.subplots(figsize=(8, 4))
                if col1 in num_cols and col2 in num_cols:
                    sns.scatterplot(data=df, x=col1, y=col2, ax=ax, color='teal')
                    ax.set_title(f"Scatter Plot: {col1} vs {col2}")
                elif col1 in cat_cols and col2 in num_cols:
                    sns.boxplot(data=df, x=col1, y=col2, ax=ax, palette='Set2')
                    ax.set_title(f"Box Plot: {col2} by {col1}")
                    plt.xticks(rotation=45)
                else:
                    sns.countplot(data=df, x=col1, hue=col2, ax=ax)
                    ax.set_title(f"Count Plot of {col1} grouped by {col2}")
                    plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.info("Need at least 2 columns for bivariate analysis.")
                
            # Multivariate Analysis
            st.markdown("### 🌐 Multivariate Analysis")
            if len(num_cols) >= 2:
                fig, ax = plt.subplots(figsize=(8, 6))
                corr = df[num_cols].corr()
                sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
                ax.set_title("Correlation Heatmap (Numerical Features)")
                st.pyplot(fig)
            else:
                st.info("Need at least 2 numerical columns for a correlation heatmap.")

        # --- TAB 3: AI CODE EXECUTOR ---
        with tab3:
            st.subheader("AI-Powered Dynamic Code Generator & Executor")
            st.markdown("Ask the AI to generate python code (using pandas, matplotlib, seaborn) to analyze the dataset. The code will execute automatically and show output/plots.")
            
            user_prompt = st.text_input("What would you like to compute or plot?", "Show the top 5 rows with the highest value in the first numerical column.")
            
            if st.button("Generate & Execute Code") and api_key:
                try:
                    # Initialize LangChain Chat Model
                    chat = init_chat_model(model_name, model_provider=provider)
                    
                    system_prompt = (
                        "You are an expert Python Data Analyst. Given a pandas DataFrame named `df`, "
                        "write executable Python code to answer the user's request. "
                        "Return ONLY valid Python code block wrapped in python markdown. "
                        "You can print results or display matplotlib/seaborn plots using plt.show(). "
                        "Do not include any conversational text, only the code."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"Columns are: {list(df.columns)}. Data types: {df.dtypes.to_dict()}. Request: {user_prompt}")
                    ]
                    
                    response = chat.invoke(messages)
                    code_content = response.content
                    
                    # Clean code block formatting if returned
                    if "```python" in code_content:
                        code_content = code_content.split("```python")[1].split("```")[0]
                    elif "```" in code_content:
                        code_content = code_content.split("```")[1].split("```")[0]
                        
                    st.markdown("### Generated Code:")
                    st.code(code_content, language="python")
                    
                    st.markdown("### Execution Output:")
                    # Capture stdout and execute
                    buffer = io.StringIO()
                    try:
                        local_vars = {"df": df, "pd": pd, "plt": plt, "sns": sns}
                        with contextlib.redirect_stdout(buffer):
                            exec(code_content, local_vars)
                        output_result = buffer.getvalue()
                        if output_result:
                            st.text(output_result)
                        if plt.get_fignums():
                            st.pyplot(plt.gcf())
                            plt.clf()
                    except Exception as exec_error:
                        st.error(f"Error executing code: {exec_error}")
                        
                except Exception as e:
                    st.error(f"AI Generation Error: {e}")
            elif not api_key:
                st.warning("Please provide your API key in the sidebar to use the AI Code Executor.")

        # --- TAB 4: CHAT WITH DATA ---
        with tab4:
            st.subheader("💬 Chat with your Data Agent")
            st.markdown("Have a conversation with your dataset powered by LangChain.")
            
            if "messages" not in st.session_state:
                st.session_state.messages = []
                
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
            if chat_prompt := st.chat_input("Ask a question about your data..."):
                st.session_state.messages.append({"role": "user", "content": chat_prompt})
                with st.chat_message("user"):
                    st.markdown(chat_prompt)
                    
                if api_key:
                    try:
                        chat = init_chat_model(model_name, model_provider=provider)
                        
                        # Summarize info for context
                        df_summary = f"DataFrame Shape: {df.shape}\nColumns: {list(df.columns)}\nData Types:\n{df.dtypes}\nHead:\n{df.head(3).to_string()}"
                        
                        system_msg = SystemMessage(content=f"You are a helpful data analyst assistant. Here is summary info about the dataset:\n{df_summary}")
                        
                        # Build history
                        history = [system_msg]
                        for m in st.session_state.messages:
                            if m["role"] == "user":
                                history.append(HumanMessage(content=m["content"]))
                            else:
                                history.append(SystemMessage(content=m["content"]))
                                
                        response = chat.invoke(history)
                        ai_reply = response.content
                        
                        with st.chat_message("assistant"):
                            st.markdown(ai_reply)
                        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                        
                    except Exception as e:
                        st.error(f"Chat Error: {e}")
                else:
                    st.warning("Please enter your API key in the sidebar to chat with the data.")

else:
    st.info("👈 Please upload a dataset from the sidebar to get started.")