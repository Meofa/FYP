import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="SmartHost Financial Dashboard", layout="wide")

# ==========================================
# 2. CUSTOM CSS (Matching Interface Design)
# ==========================================
st.markdown("""
<style>
.block-container { padding-top: 1rem; padding-bottom: 0rem; }
.kpi-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.kpi-card {
    flex: 1; padding: 20px; border-radius: 5px; text-align: center;
    color: black; font-weight: bold; border: 1px solid #000;
}
.net-profit { background-color: #2ecc71; }
.expenses { background-color: #e74c3c; }
.revenue { background-color: #3498db; }
.margin { background-color: #f1c40f; }
.cash { background-color: #9b59b6; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Dashboard</h1>", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR (Data Control + Configuration)
# ==========================================
with st.sidebar:
    st.header("Data Control")
    
    # TEMPLATE DOWNLOAD
    st.markdown("### 📥 Get Started")
    st.markdown("New here? Download the template, fill in your data, and upload it below 🚀")

    with open("Dummy.xlsx", "rb") as file:
        st.download_button(
            label="⬇️ Download Template",
            data=file,
            file_name="Financial_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")
    
    # User Input for Startup Capital
    st.subheader("💰 Financial Configuration")
    startup_money = st.number_input(
        "Enter Startup Capital (RM)", 
        min_value=0.0, 
        value=15000.0, 
        step=500.0,
        help="Initial money invested before transactions began."
    )
    
    st.markdown("---")

    # File Uploader
    uploaded_file = st.file_uploader(
        "📤 Upload your completed template",
        type=["csv", "xlsx"]
    )

# Default Values for KPI Cards
metrics = {"net": 0, "exp": 0, "rev": 0, "margin": 0, "cash": startup_money}
df = None
df_view = None

# ==========================================
# 4. PROCESSING ENGINE
# ==========================================
if uploaded_file:
    try:
        # Load the file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Standardize column names
        df.columns = df.columns.str.strip().str.lower()

        # Validate required columns
        required_columns = ['date', 'sales', 'target_sales', 'rent', 'utilities', 'supplies', 'payroll']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Invalid Template! Missing columns: {missing_cols}")
            st.stop()

        # Convert Date Column (Handles Excel serial dates and dd/mm/yyyy)
        if pd.api.types.is_numeric_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], origin='1899-12-30', unit='D')
        else:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

        # Drop invalid dates and sort
        df = df.dropna(subset=['date']).sort_values(by='date')

        # Clean Numeric Columns
        num_cols = ['sales', 'target_sales', 'rent', 'utilities', 'supplies', 'payroll']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 📅 DATE RANGE SLIDER
        min_date, max_date = df['date'].min(), df['date'].max()
        with st.sidebar:
            st.subheader("📅 Filter by Date")
            date_range = st.slider(
                "Select Date Range",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime())
            )

        start_date, end_date = date_range

        # ---------------------------------------------------------
        # CUMULATIVE LOGIC CALCULATION
        # ---------------------------------------------------------
        # 1. df_view: Only the data inside the selected range (for Bar/Pie charts)
        df_view = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # 2. df_until_now: All data from the beginning up to the end of the range
        # This is the "Logical" way to calculate Cash Position
        df_until_now = df[df['date'] <= end_date]

        # Calculate KPIs for the selected view
        rev_val = df_view['sales'].sum()
        total_exp = df_view[['rent', 'utilities', 'supplies', 'payroll']].sum().sum()
        net_val = rev_val - total_exp
        margin_val = (net_val / rev_val * 100) if rev_val > 0 else 0
        
        # Cash Position = Startup Money + All profit made up to the end of selected range
        cum_profit = df_until_now['sales'].sum() - df_until_now[['rent', 'utilities', 'supplies', 'payroll']].sum().sum()
        cash_position = startup_money + cum_profit

        metrics = {
            "net": net_val,
            "exp": total_exp,
            "rev": rev_val,
            "margin": margin_val,
            "cash": cash_position
        }

        st.success("✅ Analysis Updated!")

    except Exception as e:
        st.error(f"Unexpected error: {e}")

# ==========================================
# 5. KPI DISPLAY (TOP 5 VIEW)
# ==========================================
kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-card net-profit">Net Profit<br>RM {metrics['net']:,.0f}</div>
    <div class="kpi-card expenses">Expenses<br>RM {metrics['exp']:,.0f}</div>
    <div class="kpi-card revenue">Revenue<br>RM {metrics['rev']:,.0f}</div>
    <div class="kpi-card margin">Margin<br>{metrics['margin']:.1f}%</div>
    <div class="kpi-card cash">Cash Position<br>RM {metrics['cash']:,.0f}</div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ==========================================
# 6. VISUALIZATION WORKSPACE
# ==========================================
if df_view is not None and not df_view.empty:
    st.markdown("<h3>Revenue Trends</h3>", unsafe_allow_html=True)
    fig_line = px.line(
        df_view, x='date', y='sales', 
        markers=True, template="plotly_white", height=300
    )
    fig_line.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<h3>Actual vs Target</h3>", unsafe_allow_html=True)
        # Applying the Dark Green (#006400) and Light Green (#90EE90)
        fig_bar = px.bar(
            df_view, x='date', y=['sales', 'target_sales'], 
            barmode='group', height=250,
            color_discrete_map={'sales': '#006400', 'target_sales': '#90EE90'}
        )
        fig_bar.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text='Legend')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.markdown("<h3>Expense Distribution</h3>", unsafe_allow_html=True)
        exp_summary = {
            'Rent': df_view['rent'].sum(),
            'Utilities': df_view['utilities'].sum(),
            'Supplies': df_view['supplies'].sum(),
            'Payroll': df_view['payroll'].sum()
        }
        fig_pie = px.pie(
            values=list(exp_summary.values()), 
            names=list(exp_summary.keys()), 
            height=250,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("System Initialized. Please upload your template in the sidebar to begin.")