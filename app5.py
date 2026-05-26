import streamlit as st
import pandas as pd
import plotly.express as px
import re
import plotly.graph_objects as go

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Financial Dashboard", layout="wide")

# ==============================================================================
# CSS STYLING
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Roboto', sans-serif !important; background-color: #faf6ee !important; }
.block-container { padding-top: 5rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }

/* SIDEBAR STYLING */
section[data-testid="stSidebar"] { background-color: #08254a !important; border-right: 2px solid rgba(255,255,255,0.08); }
[data-testid="stSidebarContent"] { padding-top: 20px !important; padding-left: 18px !important; padding-right: 18px !important; }
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] { color: white !important; }
[data-testid="stSidebar"] button[aria-label="Remove file"] { color: white !important; }
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] label { color: white !important; }

.sidebar-title { color: white; font-size: 2.2rem; font-weight: 900; letter-spacing: 1px; margin-top: 5px; margin-bottom: 15px; text-transform: uppercase; }
.sidebar-divider { border-bottom: 4px solid white; margin-bottom: 15px; }
.sidebar-section { color: white; font-size: 1.15rem; font-weight: 900; margin-bottom: 10px; }
.sidebar-subtitle { color: white; font-size: 1rem; font-weight: 900; margin-top: 10px; margin-bottom: 10px; }
.sidebar-text { color: white; font-size: 0.95rem; line-height: 1.6; margin-bottom: 10px; }
.stDownloadButton button { background-color: #1b2d52 !important; color: white !important; border-radius: 10px !important; width: 100%; height: 42px; font-weight: 700; }
section[data-testid="stSidebar"] label { color: white !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] input { background-color: black !important; color: white !important; border-radius: 10px !important; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background-color: #f2f2f2 !important; border-radius: 15px !important; border: 4px solid #cfcfcf !important; padding: 10px !important; }

/* KPI CARDS */
.kpi-container { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 160px; padding: 10px 10px; border-radius: 15px; text-align: center; border: 3px solid #2d3436; box-shadow: 4px 4px 0 rgba(0,0,0,0.15); background-color: white; }
.kpi-label { font-size: 1.1rem !important; font-weight: 900 !important; color: #2d3436 !important; margin-bottom: 4px; }
.kpi-value { font-size: 1.8rem !important; font-weight: 900 !important; color: #2d3436 !important; }
.net-profit { background-color: #2ecc71; }
.expenses { background-color: #e74c3c; }
.revenue { background-color: #3498db; }
.margin { background-color: #f1c40f; }
.cash { background-color: #9b59b6; }

/* CHARTS */
.stPlotlyChart { background-color: #ffffff !important; border-radius: 20px !important; border: 3px solid #2d3436 !important; padding: 10px !important; overflow: hidden !important; }
h3, .stSubheader { font-size: 1rem !important; font-weight: 900 !important; color: #2d3436 !important; margin-top: 5px !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR UI
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-subtitle">📥 GET STARTED</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-text">Download the template here</div>', unsafe_allow_html=True)
    
    try:
        with open("Wrong_Headers_Financial_Data_2026.xlsx", "rb") as file:
            st.download_button(label="⬇️ Download Template", data=file, file_name="Financial_Template.xlsx")
    except: st.info("Template file not found")

    st.markdown("---")
    startup_money = st.number_input("Enter Startup Capital (RM)", min_value=0.0, value=15000.0, step=500.0)
    st.markdown("---")
    uploaded_file = st.file_uploader("📤 UPLOAD TEMPLATE", type=["csv", "xlsx"])

# ==============================================================================
# DATA PIPELINE
# ==============================================================================
metrics = {"net": 0, "exp": 0, "rev": 0, "margin": 0, "cash": startup_money}
df_view = None
valid_file = False
file_error = False

def clean_numeric(val):
    if isinstance(val, (int, float)): return val
    clean_val = re.sub(r'[^0-9.-]', '', str(val))
    try: return float(clean_val)
    except: return 0.0

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()
        required_cols = ['date', 'sales', 'rent', 'utilities', 'supplies', 'payroll', 'target_sales']
        
        if not all(col in df.columns for col in required_cols):
            file_error = True
        else:
            valid_file = True
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['date']).sort_values(by='date')
            
            numeric_cols = ['sales', 'rent', 'utilities', 'supplies', 'payroll', 'target_sales']
            for col in numeric_cols: df[col] = df[col].apply(clean_numeric)
            
            with st.sidebar:
                st.markdown("---")
                dr = st.slider("DATE RANGE", df['date'].min().to_pydatetime(), df['date'].max().to_pydatetime(), 
                               (df['date'].min().to_pydatetime(), df['date'].max().to_pydatetime()))
            
            df_view = df[(df['date'] >= dr[0]) & (df['date'] <= dr[1])]
            df_cum = df[df['date'] <= dr[1]]
            
            rev = df_view['sales'].sum()
            exp = df_view[['rent', 'utilities', 'supplies', 'payroll']].sum().sum()
            net = rev - exp
            total_rev_all = df_cum['sales'].sum()
            total_exp_all = df_cum[['rent', 'utilities', 'supplies', 'payroll']].sum().sum()
            cash_pos = startup_money + (total_rev_all - total_exp_all)
            
            metrics = {"net": net, "exp": exp, "rev": rev, "margin": (net/rev*100) if rev > 0 else 0, "cash": cash_pos}
    except Exception as e: file_error = True

# ==============================================================================
# UI RENDER
# ==============================================================================
if file_error:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error("⚠️ WRONG FILE DETECTED!", icon="🚨")
    st.warning("The file uploaded is corrupted or does not match the template format. Please download the correct template from the sidebar.", icon="💡")
elif not valid_file:
    st.markdown("""
    <div style="text-align: center; padding-top: 50px;">
        <h1 style="color: #08254a; font-size: 3rem;">👋 Welcome to Your Financial Dashboard</h1>
        <p style="color: #2d3436; font-size: 1.2rem;">Get started by uploading your financial data template via the sidebar.</p>
        <div style="border: 3px dashed #b2bec3; padding: 40px; border-radius: 20px; display: inline-block; width: 60%; margin-top: 20px;">
            <h2 style="color: #08254a;">How to use:</h2>
            <p>1. Download the template from the sidebar.</p>
            <p>2. Fill in your data.</p>
            <p>3. Upload it here to see your insights!</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card net-profit"><div class="kpi-label">NET PROFIT</div><div class="kpi-value">RM {metrics['net']:,.0f}</div></div>
        <div class="kpi-card expenses"><div class="kpi-label">EXPENSES</div><div class="kpi-value">RM {metrics['exp']:,.0f}</div></div>
        <div class="kpi-card revenue"><div class="kpi-label">REVENUE</div><div class="kpi-value">RM {metrics['rev']:,.0f}</div></div>
        <div class="kpi-card margin"><div class="kpi-label">MARGIN</div><div class="kpi-value">{metrics['margin']:.1f}%</div></div>
        <div class="kpi-card cash"><div class="kpi-label">CASH</div><div class="kpi-value">RM {metrics['cash']:,.0f}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📈 Revenue Trends")
    fig = go.Figure()
    
    # Add markers
    fig.add_trace(go.Scatter(
        x=df_view['date'], 
        y=df_view['sales'], 
        mode='markers', 
        name='Sales', 
        marker=dict(color='#2d3436', size=8),
        showlegend=False # Membuang legend untuk marker
    ))
    
    # Add colored segments (Green for up, Red for down)
    for i in range(len(df_view) - 1):
        color = '#00ff00' if df_view['sales'].iloc[i+1] >= df_view['sales'].iloc[i] else '#ff0000'
        fig.add_trace(go.Scatter(
            x=[df_view['date'].iloc[i], df_view['date'].iloc[i+1]],
            y=[df_view['sales'].iloc[i], df_view['sales'].iloc[i+1]],
            mode='lines',
            line=dict(color=color, width=3),
            showlegend=False # Memastikan tiada legend untuk setiap segmen
        ))
    
    fig.update_layout(
        height=250, 
        margin=dict(l=20, r=20, t=20, b=20), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#ecf0f1'),
        showlegend=False # Memastikan keseluruhan carta tiada legend
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Actual VS Target")
        fig_bar = px.bar(
            df_view, 
            x='date', 
            y=['sales', 'target_sales'], 
            barmode='group', 
            height=250,
            color_discrete_map={
                'sales': 'darkgreen',
                'target_sales': 'cyan'
            }
        )
        fig_bar.update_traces(marker_line_color='#2d3436', marker_line_width=1.5, opacity=0.9)
        fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3),
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    with col2:
        st.subheader("💸 Expense Distribution")
        exp_sum = {'Rent': df_view['rent'].sum(), 'Utilities': df_view['utilities'].sum(), 'Supplies': df_view['supplies'].sum(), 'Payroll': df_view['payroll'].sum()}
        
        # Enhanced Pie Chart (Donut style)
        fig_pie = px.pie(
            values=list(exp_sum.values()), 
            names=list(exp_sum.keys()), 
            hole=0.5, 
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig_pie.update_traces(
            textinfo='percent+label', 
            textposition='outside',
            marker=dict(line=dict(color='#ffffff', width=3))
        )
        
        fig_pie.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            # Tambah baris ini untuk tukar warna label kepada hitam
            font=dict(color="black", size=12, family="Roboto")
        )
        
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
