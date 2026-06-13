import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import base64

# إعدادات الصفحة المتقدمة
st.set_page_config(page_title="Advanced Nodal Analysis Pro", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------
# --- 1. إصلاح وتطوير صورة الغلاف (خلفية سينمائية هادئة) ---
# ----------------------------------------------------------------
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_base64 = get_base64_of_bin_file("c62c32fd813457de68c38c156d74dda6.jpg")
    
    # CSS مطور: تعتيم قوي للصورة لتندمج مع اللون الأسود، وتحسين المربعات
    custom_css = f"""
    <style>
        .banner-container {{
            width: 100vw;
            height: 280px; /* تقليل الارتفاع لتصبح لافتة علوية أنيقة */
            background-image: linear-gradient(to bottom, rgba(14,17,23,0.7) 0%, rgba(14,17,23,1) 100%), url('data:image/jpeg;base64,{img_base64}');
            background-size: cover;
            background-position: center 20%;
            background-repeat: no-repeat;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 0;
        }}
        .block-container {{
            margin-top: 40px !important;
            padding-top: 2rem !important;
            z-index: 1;
            position: relative;
        }}
        h1, h2, h3, p {{
            text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
        }}
        [data-testid="metric-container"] {{
            background: rgba(30, 33, 40, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        }}
    </style>
    <div class="banner-container"></div>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ----------------------------------------------------------------
# العناوين الرئيسية
# ----------------------------------------------------------------
st.title("🛢️ Production Optimization Dashboard")
st.markdown("Perform robust **Nodal Analysis** by intersecting **Vogel's IPR** with **Physical TPR** to determine the optimal well operating point.")
st.divider()

# ----------------------------------------------------------------
# 2. Sidebar Inputs
# ----------------------------------------------------------------
st.sidebar.header("📋 Reservoir Parameters (IPR)")
Pr       = st.sidebar.number_input("Reservoir Pressure (Pr) [psi]",    min_value=1000, max_value=8000, value=3500, step=100)
Pwf_test = st.sidebar.number_input("Test Flowing Pressure (Pwf) [psi]", min_value=500,  max_value=7500, value=2500, step=100)
Q_test   = st.sidebar.number_input("Test Flow Rate (Q) [STB/day]",      min_value=100,  max_value=5000, value=1200, step=50)

st.sidebar.header("📋 Wellbore & Tubing Parameters (TPR)")
Depth         = st.sidebar.number_input("True Vertical Depth (TVD) [ft]",  min_value=2000, max_value=15000, value=8000, step=500)
Pwh           = st.sidebar.number_input("Wellhead Pressure (Pwh) [psi]",   min_value=50,   max_value=1500,  value=300,  step=50)
fluid_grad    = st.sidebar.slider("Fluid Pressure Gradient [psi/ft]", min_value=0.15, max_value=0.50, value=0.35, step=0.01)
friction_coef = st.sidebar.slider("Tubing Friction Factor Coefficient", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

# ----------------------------------------------------------------
# 3. Calculations
# ----------------------------------------------------------------
if Pwf_test >= Pr:
    st.error("❌ Error: Test Pwf must be strictly less than Reservoir Pressure (Pr).")
else:
    vogel_denom = 1 - 0.2 * (Pwf_test / Pr) - 0.8 * (Pwf_test / Pr)**2
    Qmax = Q_test / vogel_denom if vogel_denom > 0 else 0
    PI = Q_test / (Pr - Pwf_test)

    if Qmax > 0:
        q_arr = np.linspace(0, Qmax, 200)
        
        # IPR
        pwf_ipr = []
        for q in q_arr:
            radial_val = 0.04 + 3.2 * (1 - (q / Qmax))
            x = (-0.2 + np.sqrt(radial_val)) / 1.6
            pwf_ipr.append(x * Pr)
        pwf_ipr = np.array(pwf_ipr)

        # TPR
        delta_p_hydrostatic = fluid_grad * Depth
        pwf_tpr = Pwh + delta_p_hydrostatic + (friction_coef * 1e-4 * (q_arr ** 1.85))

        # Operating point
        diff = np.abs(pwf_ipr - pwf_tpr)
        idx_intersection = np.argmin(diff)
        q_op = q_arr[idx_intersection]
        pwf_op = pwf_ipr[idx_intersection]

        is_flowing = True
        if pwf_tpr[0] > Pr or q_op <= 1.0:
            is_flowing = False
            q_op = 0.0
            pwf_op = 0.0

        # إنشاء جدول البيانات للتصدير
        df_results = pd.DataFrame({
            "Flow Rate (STB/d)": np.round(q_arr, 1),
            "IPR Pressure (psi)": np.round(pwf_ipr, 1),
            "TPR Pressure (psi)": np.round(pwf_tpr, 1)
        })

        # ----------------------------------------------------------------
        # 4. بناء التبويبات (Tabs) لعرض احترافي
        # ----------------------------------------------------------------
        tab1, tab2 = st.tabs(["📊 Nodal Analysis Chart", "📥 Data Export & Tables"])

        with tab1:
            st.subheader("Well Performance Summary")
            col1, col2, col3, col4 = st.columns(4)

            if is_flowing:
                col1.metric("⚡ Flow Rate (Q_op)", f"{q_op:,.1f} STB/d")
                col2.metric("📉 Bottomhole Pressure", f"{pwf_op:,.1f} psi")
                col3.metric("🏆 Max Potential (Qmax)", f"{Qmax:,.1f} STB/d")
                col4.metric("📈 Productivity Index", f"{PI:.3f}")
            else:
                col1.metric("⚡ Flow Rate (Q_op)", "0.0 STB/d", delta="Well Dead", delta_color="inverse")
                col2.metric("📉 Bottomhole Pressure", "N/A")
                col3.metric("🏆 Max Potential (Qmax)", f"{Qmax:,.1f} STB/d")
                col4.metric("📈 Productivity Index", f"{PI:.3f}")
                st.error("⚠️ The well cannot flow naturally. Tubing pressure exceeds reservoir pressure.")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=q_arr, y=pwf_ipr, mode='lines', name='IPR Curve', line=dict(color='#1f77b4', width=3)))
            fig.add_trace(go.Scatter(x=q_arr, y=pwf_tpr, mode='lines', name='TPR Curve', line=dict(color='#d62728', width=3)))
            
            if is_flowing:
                fig.add_trace(go.Scatter(
                    x=[q_op], y=[pwf_op], mode='markers+text', name='Operating Point',
                    marker=dict(color='#2ca02c', size=14, symbol='diamond', line=dict(width=2, color='white')),
                    text=[f"  ({q_op:.0f} STB/d, {pwf_op:.0f} psi)"], textposition="top right", textfont=dict(size=13, color='#2ca02c')
                ))

            fig.update_layout(
                xaxis_title="Liquid Flow Rate (STB/day)",
                yaxis_title="Bottomhole Flowing Pressure, Pwf (psi)",
                xaxis=dict(gridcolor='rgba(200,200,200,0.1)', rangemode='tozero'),
                yaxis=dict(gridcolor='rgba(200,200,200,0.1)', range=[0, Pr * 1.05]),
                hovermode="x unified",
                template="plotly_dark",
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
                margin=dict(l=40, r=20, t=40, b=40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Raw Data Table")
            st.markdown("Review the calculated IPR and TPR pressure points across different flow rates.")
            
            # عرض الجدول
            st.dataframe(df_results, use_container_width=True, height=300)
            
            # زر تحميل البيانات
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name='nodal_analysis_data.csv',
                mime='text/csv',
            )
