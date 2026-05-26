import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================================================================
# 1. PAGE CONFIGURATION & INSTITUTIONAL CORES
# ==============================================================================
st.set_page_config(page_title="SmartHost Dashboard", layout="wide")

# ==============================================================================
# 2. UNIVERSAL PRODUCTION-SAFE STYLING CSS
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');

    /* Target all possible body containers to ensure background color uniformity on the cloud */
    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Roboto', sans-serif;
        background-color: #faf6ee !important; 
    }
    
    /* FIX: Standardized top spacing to guarantee layout synchronization across cloud viewports */
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 98% !important; 
    }

    /* Sidebar Customization - Sleek Navy Blue */
    section[data-testid="stSidebar"] {
        background-color: #0a2240 !important;
    }
    
    /* Ensuring sidebar labels, paragraphs, and standard headers are crisp white */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    /* Prevent the download button text from turning white and becoming invisible */
    section[data-testid="stSidebar"] button p {
        color: #2d3436 !important;
    }

    /* Hardened the file uploader outline to solid black for a highly professional look */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        border: 4px solid #2d3436 !important; 
        background-color: #ffffff !important;  
        border-radius: 15px !important;
    }

    /* Sidebar Title Customization */
    .sidebar-title {
        font-size: 2.2rem; 
        font-weight: 900;
        color: #ffffff;
        text-transform: uppercase;
        margin-top: 10px; 
        margin-bottom: 15px;
        border-bottom: 4px solid #ffffff;
        padding-bottom: 8px;
        letter-spacing: 1px;
    }

    /* KPI Cards Layout Setup */
    .kpi-container { 
        display: flex; 
        justify-content: space-between; 
        gap: 10px; 
        margin-bottom: 20px; 
    }
    .kpi-card {
        flex: 1; 
        padding: 15px 10px; 
        min-height: 110px;   
        border-radius: 20px; 
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: black; 
        border: 4px solid #2d3436 !important; 
        box-shadow: 8px 8px 0px rgba(0,0,0,0.2);
    }
    .kpi-label { 
        font-size: 0.9rem; 
        font-weight: 900; 
        text-transform: uppercase; 
        margin-bottom: 4px; 
    }
    .kpi-value { 
        font-size: 1.6rem; 
        font-weight: 900; 
    }

    .net-profit { background-color: #2ecc71; }
    .expenses { background-color: #e74c3c; }
    .revenue { background-color: #3498db; }
    .margin { background-color: #f1c40f; }
    .cash { background-color: #9b59b6; }

    /* PRODUCTION FIX: Stable, cloud-proof CSS selector for chart containers */
    div.element-container:has(iframe), .stPlotlyChart {
        background-color: #f4ebd9 !important;
        border-radius: 30px !important;
        border: 5px solid #2d3436 !important; 
        box-shadow: 10px 10px 0px rgba(0,0,0,0.15) !important;
        padding: 12px !important;
        display: block;
    }

    /* Drop-shadow rendering layer for SVG assets */
    .main svg.main-svg {
        filter: drop-shadow(4px 6px 4px rgba(0, 0, 0, 0.08));
    }

    h3, .stSubheader { 
        font-size: 1.1rem !important; 
        font-weight: 900 !important; 
        text-transform: uppercase; 
        color: #2d3436 !important;
        margin-top: 10px !important;
        margin-bottom: 5px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. SIDEBAR CONTROLS & DATA LOADING PIPELINE 
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">Dashboard</div>', unsafe_allow_html=True)
    st.header("⚙️ DATA CONTROL")
    
    st.markdown("### 📥 Get Started")
    st.markdown("New here? Download the template, fill in your data, and upload it below")

    try:
        with open("Wrong_Headers_Financial_Data_2026.xlsx", "rb") as file:
            st.download_button(
                label="⬇️ Download Template",
                data=file,
                file_name="Financial_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.download_button(label="⬇️ Download Template", data="", file_name="Financial_Template.xlsx")
        
    startup_money = st.number_input("Enter Startup Capital (RM)", min_value=0.0, value=15000.0, step=500.0)
    uploaded_file = st.file_uploader("📤 UPLOAD TEMPLATE", type=["csv", "xlsx"])

# Initialize default empty structures
metrics = {"net": 0, "exp": 0, "rev": 0, "margin": 0, "cash": startup_money}
df_view = None
valid_file_pipeline = False

# Core Data Integrity Validation & ETL Pipeline
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()
        
        required_template_headers = ['date', 'sales', 'target_sales', 'rent', 'utilities', 'supplies', 'payroll']
        has_correct_structure = all(header in df.columns for header in required_template_headers)
        
        if not has_correct_structure:
            st.sidebar.warning("⚠️ Please using the template")
        else:
            valid_file_pipeline = True
            df = df.drop_duplicates()
            
            if 'date' in df.columns:
                if df['date'].dtype == 'object':
                    df['date'] = df['date'].astype(str).str.strip()
                    
                if pd.api.types.is_numeric_dtype(df['date']):
                    df['date'] = pd.to_datetime(df['date'], origin='1899-12-30', unit='D')
                else:
                    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
                
                df = df.dropna(subset=['date']).sort_values(by='date')
            
            for col in ['sales', 'target_sales', 'rent', 'utilities', 'supplies', 'payroll']:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            with st.sidebar:
                st.markdown("---")
                dr = st.slider(
                    "DATE RANGE", 
                    df['date'].min().to_pydatetime(), 
                    df['date'].max().to_pydatetime(), 
                    (df['date'].min().to_pydatetime(), df['date'].max().to_pydatetime())
                )
            
            df_view = df[(df['date'] >= dr[0]) & (df['date'] <= dr[1])]
            df_cum = df[df['date'] <= dr[1]]

            rev = df_view['sales'].sum()
            total_exp = df_view[['rent', 'utilities', 'supplies', 'payroll']].sum().sum()
            net = rev - total_exp
            cash = startup_money + (df_cum['sales'].sum() - df_cum[['rent', 'utilities', 'supplies', 'payroll']].sum().sum())

            metrics = {
                "net": net, 
                "exp": total_exp, 
                "rev": rev, 
                "margin": (net / rev * 100) if rev > 0 else 0, 
                "cash": cash
            }
    except Exception as e:
        st.error(f"System Error: {e}")

# ==============================================================================
# 4. MAIN USER INTERFACE RENDERING
# ==============================================================================

# Section 4.1: Strategic KPI Ribbon
st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-card net-profit"><div class="kpi-label">NET PROFIT</div><div class="kpi-value">RM {metrics['net']:,.0f}</div></div>
    <div class="kpi-card expenses"><div class="kpi-label">EXPENSES</div><div class="kpi-value">RM {metrics['exp']:,.0f}</div></div>
    <div class="kpi-card revenue"><div class="kpi-label">REVENUE</div><div class="kpi-value">RM {metrics['rev']:,.0f}</div></div>
    <div class="kpi-card margin"><div class="kpi-label">MARGIN</div><div class="kpi-value">{metrics['margin']:.1f}%</div></div>
    <div class="kpi-card cash"><div class="kpi-label">CASH POSITION</div><div class="kpi-value">RM {metrics['cash']:,.0f}</div></div>
</div>
""", unsafe_allow_html=True)

# Section 4.2: Row 1 (Revenue Trends)
st.subheader("📈 REVENUE TRENDS")
if valid_file_pipeline and df_view is not None and not df_view.empty:
    fig_line = px.line(df_view, x='date', y='sales', markers=True, template="plotly_white", height=230)
    fig_line.update_traces(line_color='#6c5ce7', line_width=4)
    fig_line.update_layout(
        font=dict(family="Roboto", size=14), 
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff'
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.markdown('<div style="text-align:center; background-color: #f4ebd9; border: 5px solid #2d3436; border-radius: 30px; padding:50px; color:#888; font-weight:900;">WAITING FOR VALID TEMPLATE...</div>', unsafe_allow_html=True)

# Section 4.3: Row 2 (Comparative Analytics & Expense Distribution)
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🎯 ACTUAL VS TARGET")
    if valid_file_pipeline and df_view is not None and not df_view.empty:
        fig_bar = px.bar(
            df_view, x='date', y=['sales', 'target_sales'], barmode='group', height=230,
            template="plotly_white", 
            color_discrete_map={'sales': '#1b5e20', 'target_sales': '#a5d6a7'}
        )
        fig_bar.update_layout(
            font=dict(family="Roboto", size=14), 
            legend=dict(orientation="h", y=-0.2, font=dict(size=16)), 
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.markdown('<div style="text-align:center; background-color: #f4ebd9; border: 5px solid #2d3436; border-radius: 30px; padding:50px; color:#888; font-weight:900;">WAITING FOR VALID TEMPLATE...</div>', unsafe_allow_html=True)

with col_right:
    st.subheader("💸 EXPENSE DISTRIBUTION")
    if valid_file_pipeline and df_view is not None and not df_view.empty:
        exp_sum = {
            'Rent': df_view['rent'].sum(), 
            'Utilities': df_view['utilities'].sum(),
            'Supplies': df_view['supplies'].sum(), 
            'Payroll': df_view['payroll'].sum()
            }
        fig_pie = px.pie(
            values=list(exp_sum.values()), names=list(exp_sum.keys()), hole=0, height=230,
            template="plotly_white", 
            color_discrete_sequence=['#6c5ce7', '#ff7675', '#fdcb6e', '#0984e3']
        )
        fig_pie.update_traces(
            textinfo='percent',
            insidetextfont=dict(family="Roboto", size=14, color='#000000'),
            marker=dict(line=dict(color='#ffffff', width=3))
        )
        fig_pie.update_layout(
            font=dict(family="Roboto", size=14), 
            legend=dict(orientation="h", y=-0.2, font=dict(size=16)), 
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='#ffffff'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.markdown('<div style="text-align:center; background-color: #f4ebd9; border: 5px solid #2d3436; border-radius: 30px; padding:50px; color:#888; font-weight:900;">WAITING FOR VALID TEMPLATE...</div>', unsafe_allow_html=True)
