import streamlit as st
import numpy as np
import plotly.graph_objects as go
import base64

# إعدادات الصفحة المتقدمة
st.set_page_config(page_title="Advanced Nodal Analysis Pro", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------
# --- إضافة صورة الغلاف بتأثير التلاشي الداكن الاحترافي ---
# ----------------------------------------------------------------
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    # تحويل الصورة إلى نص برمجي
    img_base64 = get_base64_of_bin_file("c62c32fd813457de68c38c156d74dda6.jpg")
    
    # دمج الصورة مع تدرج داكن (Linear Gradient) يطابق خلفية ستريم ليت
    custom_css = f"""
    <style>
        .banner-container {{
            width: 100vw;
            height: 350px;
            /* السر هنا: وضع طبقة داكنة فوق الصورة تتلاشى للأسود بالتدريج */
            background-image: linear-gradient(to bottom, rgba(14,17,23,0.3) 0%, rgba(14,17,23,1) 90%), url('data:image/jpeg;base64,{img_base64}');
            background-size: cover;
            background-position: center 30%;
            background-repeat: no-repeat;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 0;
        }}
        
        /* دفع المحتوى للأسفل وإبقائه فوق الخلفية */
        .block-container {{
            margin-top: 50px !important;
            padding-top: 2rem !important;
            z-index: 1;
            position: relative;
        }}

        /* إضافة ظل خفيف للنصوص لتبرز أكثر */
        h1, h2, h3, p {{
            text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
        }}

        /* تصميم مربعات النتائج لتناسب الوضع الداكن (Dark Theme) */
        [data-testid="metric-container"] {{
            background: rgba(30, 33, 40, 0.6); /* لون داكن شبه شفاف */
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            backdrop-filter: blur(5px);
        }}
    </style>
    <div class="banner-container"></div>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
except FileNotFoundError:
    # في حال عدم وجود الصورة
    pass

# ----------------------------------------------------------------
# العناوين الرئيسية
# ----------------------------------------------------------------
st.title("🛢️ Production Optimization Dashboard: Nodal Analysis")
st.markdown("This tool performs **Nodal Analysis** by intersecting **Vogel's IPR** with a **Tubing Performance Relationship (TPR)** to find the well operating point.")

# ----------------------------------------------------------------
# 1. Sidebar Inputs
# ----------------------------------------------------------------
st.sidebar.header("📋 Reservoir Parameters (IPR)")
Pr       = st.sidebar.number_input("Reservoir Pressure (Pr) [psi]",    min_value=1000, max_value=8000, value=3500, step=100)
Pwf_test = st.sidebar.number_input("Test Flowing Pressure (Pwf) [psi]", min_value=500,  max_value=7500, value=2500, step=100)
Q_test   = st.sidebar.number_input("Test Flow Rate (Q) [STB/day]",      min_value=100,  max_value=5000, value=1200, step=50)

st.sidebar.header("📋 Wellbore & Tubing Parameters (TPR)")
Depth         = st.sidebar.number_input("True Vertical Depth (TVD) [ft]",  min_value=2000, max_value=15000, value=8000, step=500)
Pwh           = st.sidebar.number_input("Wellhead Pressure (Pwh) [psi]",   min_value=50,   max_value=1500,  value=300,  step=50)
fluid_grad    = st.sidebar.slider("Fluid Pressure Gradient [psi/ft]", min_value=0.15, max_value=0.50, value=0.35, step=0.01,
                                  help="Water: ~0.433 psi/ft, Light Oil: ~0.3-0.35 psi/ft")
friction_coef = st.sidebar.slider("Tubing Friction Factor Coefficient", min_value=0.1, max_value=10.0, value=2.0, step=0.1,
                                  help="Simulates restriction in tubing. Higher value = smaller tubing diameter.")

# ----------------------------------------------------------------
# 2. Calculations
# ----------------------------------------------------------------
if Pwf_test >= Pr:
    st.error("❌ Error: Test Pwf must be strictly less than Reservoir Pressure (Pr).")
else:
    # Vogel Qmax
    vogel_denom = 1 - 0.2 * (Pwf_test / Pr) - 0.8 * (Pwf_test / Pr)**2
    Qmax = Q_test / vogel_denom if vogel_denom > 0 else 0

    # Productivity Index
    PI = Q_test / (Pr - Pwf_test)

    if Qmax > 0:
        q_arr = np.linspace(0, Qmax, 200)

        # IPR curve (reverse Vogel)
        pwf_ipr = []
        for q in q_arr:
            radial_val = 0.04 + 3.2 * (1 - (q / Qmax))
            x = (-0.2 + np.sqrt(radial_val)) / 1.6
            pwf_ipr.append(x * Pr)
        pwf_ipr = np.array(pwf_ipr)

        # TPR curve 
        delta_p_hydrostatic = fluid_grad * Depth
        pwf_tpr = Pwh + delta_p_hydrostatic + (friction_coef * 1e-4 * (q_arr ** 1.85))

        # Operating point
        diff             = np.abs(pwf_ipr - pwf_tpr)
        idx_intersection = np.argmin(diff)
        q_op             = q_arr[idx_intersection]
        pwf_op           = pwf_ipr[idx_intersection]

        # Natural flow check
        is_flowing = True
        if pwf_tpr[0] > Pr or q_op <= 1.0:
            is_flowing = False
            q_op = 0.0
            pwf_op = 0.0

        # ----------------------------------------------------------------
        # 3. Results
        # ----------------------------------------------------------------
        st.subheader("📊 Well Performance Summary")
        col1, col2, col3, col4 = st.columns(4)

        if is_flowing:
            col1.metric("⚡ Operating Flow Rate (Q_op)",        f"{q_op:,.1f} STB/day")
            col2.metric("📉 Operating BHP (Pwf_op)",            f"{pwf_op:,.1f} psi")
            col3.metric("🏆 Maximum Potential (Qmax)",          f"{Qmax:,.1f} STB/day")
            col4.metric("📈 Productivity Index (PI)",           f"{PI:.3f} STB/day/psi")
        else:
            col1.metric("⚡ Operating Flow Rate (Q_op)", "0.0 STB/day",
                        delta="Well cannot flow naturally", delta_color="inverse")
            col2.metric("📉 Operating BHP (Pwf_op)",    "N/A")
            col3.metric("🏆 Maximum Potential (Qmax)",  f"{Qmax:,.1f} STB/day")
            col4.metric("📈 Productivity Index (PI)",   f"{PI:.3f} STB/day/psi")
            st.warning("⚠️ High backpressure detected. The static fluid column exceeds reservoir energy.")

        # ----------------------------------------------------------------
        # 4. Chart
        # ----------------------------------------------------------------
        fig = go.Figure()

        # IPR curve
        fig.add_trace(go.Scatter(
            x=q_arr, y=pwf_ipr,
            mode='lines', name='Inflow Performance (IPR)',
            line=dict(color='#1f77b4', width=3)
        ))

        # TPR curve
        fig.add_trace(go.Scatter(
            x=q_arr, y=pwf_tpr,
            mode='lines', name='Tubing Performance (TPR)',
            line=dict(color='#d62728', width=3)
        ))

        # Operating point
        if is_flowing:
            fig.add_trace(go.Scatter(
                x=[q_op], y=[pwf_op],
                mode='markers+text', name='Operating Point',
                marker=dict(color='#2ca02c', size=14, symbol='diamond',
                            line=dict(width=2, color='white')),
                text=[f"  ({q_op:.0f} STB/d,  {pwf_op:.0f} psi)"],
                textposition="top right",
                textfont=dict(size=13, color='#2ca02c')
            ))

        fig.update_layout(
            title="<b>Nodal Analysis Plot — Vogel IPR vs. Physical TPR</b>",
            xaxis_title="Liquid Flow Rate (STB/day)",
            yaxis_title="Bottomhole Flowing Pressure, Pwf (psi)",
            xaxis=dict(gridcolor='rgba(200,200,200,0.1)', rangemode='tozero'),
            yaxis=dict(gridcolor='rgba(200,200,200,0.1)', range=[0, Pr * 1.05]),
            hovermode="x unified",
            template="plotly_dark", # تغيير الثيم ليتناسب مع الخلفية الداكنة
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            margin=dict(l=60, r=20, t=60, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)
