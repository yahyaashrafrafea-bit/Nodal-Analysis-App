import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nodal Analysis Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Minimal clean CSS ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FAFAFA;
    border-right: 1px solid #EFEFEF;
}

/* Metric cards: just a subtle shadow */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #EFEFEF;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* Metric label */
[data-testid="metric-container"] label {
    font-size: 12px !important;
    color: #888 !important;
    font-weight: 500 !important;
}

/* Metric value */
[data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────
st.sidebar.title("⚙️ Parameters")

st.sidebar.markdown("#### Reservoir (IPR)")
Pr       = st.sidebar.number_input("Reservoir Pressure — Pr (psi)",     1000, 8000, 3500, 100)
Pwf_test = st.sidebar.number_input("Test Flowing Pressure — Pwf (psi)", 500,  7500, 2500, 100)
Q_test   = st.sidebar.number_input("Test Flow Rate — Q (STB/day)",      100,  5000, 1200, 50)

st.sidebar.markdown("#### Wellbore (TPR)")
Depth         = st.sidebar.number_input("TVD (ft)",                2000, 15000, 8000, 500)
Pwh           = st.sidebar.number_input("Wellhead Pressure (psi)", 50,   1500,  300,  50)
fluid_grad    = st.sidebar.slider("Fluid Gradient (psi/ft)",   0.15, 0.50, 0.35, 0.01,
                                  help="Water ≈ 0.433 | Light oil ≈ 0.30–0.35")
friction_coef = st.sidebar.slider("Tubing Friction Coefficient", 0.1, 10.0, 2.0, 0.1,
                                  help="Higher = smaller tubing / more restriction")

# ── HEADER ─────────────────────────────────────────────────────
st.markdown("## 🛢️ Nodal Analysis Dashboard")
st.markdown(
    "<p style='color:#888; margin-top:-12px; font-size:14px;'>"
    "Vogel IPR · Physical TPR · Operating Point</p>",
    unsafe_allow_html=True
)
st.divider()

# ── VALIDATION ─────────────────────────────────────────────────
if Pwf_test >= Pr:
    st.error("❌ Test Pwf must be less than Reservoir Pressure (Pr).")
    st.stop()

# ── CALCULATIONS ───────────────────────────────────────────────
vogel_denom = 1 - 0.2*(Pwf_test/Pr) - 0.8*(Pwf_test/Pr)**2
Qmax = Q_test / vogel_denom if vogel_denom > 0 else 0
PI   = Q_test / (Pr - Pwf_test)

q_arr   = np.linspace(0, Qmax, 300)
pwf_ipr = np.array([
    ((-0.2 + np.sqrt(max(0.0, 0.04 + 3.2*(1 - q/Qmax)))) / 1.6) * Pr
    for q in q_arr
])
delta_hyd = fluid_grad * Depth
pwf_tpr   = Pwh + delta_hyd + (friction_coef * 1e-4 * (q_arr ** 1.85))

diff   = np.abs(pwf_ipr - pwf_tpr)
idx_op = np.argmin(diff)
q_op   = q_arr[idx_op]
pwf_op = pwf_ipr[idx_op]

is_flowing = not (pwf_tpr[0] > Pr or q_op <= 1.0)
if not is_flowing:
    q_op = pwf_op = 0.0

efficiency   = round((q_op / Qmax) * 100, 1) if is_flowing else 0.0
drawdown_pct = round((1 - pwf_op / Pr) * 100, 1) if is_flowing else 0.0

# ── KPI METRICS ────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("⚡ Operating Rate (Q_op)",     f"{q_op:,.0f} STB/day")
c2.metric("📉 Operating BHP (Pwf_op)",   f"{pwf_op:,.0f} psi")
c3.metric("🏆 Maximum Rate (Qmax)",       f"{Qmax:,.0f} STB/day")
c4.metric("📈 Productivity Index (PI)",   f"{PI:.3f} STB/d/psi")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

if not is_flowing:
    st.warning("⚠️ Well cannot flow naturally — static fluid column exceeds reservoir energy. Consider artificial lift.")

# ── ANIMATED CHART ─────────────────────────────────────────────
n      = len(q_arr)
steps  = 40

frames = []
for i in range(1, steps + 1):
    end = max(2, int(n * i / steps))
    fd  = [
        go.Scatter(x=q_arr[:end], y=pwf_ipr[:end],
                   mode="lines", line=dict(color="#4F8EF7", width=2.5)),
        go.Scatter(x=q_arr[:end], y=pwf_tpr[:end],
                   mode="lines", line=dict(color="#F76B6B", width=2.5)),
    ]
    if i == steps and is_flowing:
        fd.append(go.Scatter(
            x=[q_op], y=[pwf_op],
            mode="markers+text",
            marker=dict(color="#2DB37A", size=13, symbol="diamond",
                        line=dict(width=2, color="white")),
            text=[f"  ({q_op:.0f} STB/d,  {pwf_op:.0f} psi)"],
            textposition="top right",
            textfont=dict(size=12, color="#2DB37A")
        ))
    frames.append(go.Frame(data=fd, name=str(i)))

fig = go.Figure(
    data=[
        go.Scatter(x=[], y=[], mode="lines",
                   name="IPR — Inflow",
                   line=dict(color="#4F8EF7", width=2.5),
                   fill="tozeroy", fillcolor="rgba(79,142,247,0.07)"),
        go.Scatter(x=[], y=[], mode="lines",
                   name="TPR — Tubing",
                   line=dict(color="#F76B6B", width=2.5),
                   fill="tozeroy", fillcolor="rgba(247,107,107,0.06)"),
        go.Scatter(x=[], y=[], mode="markers+text",
                   name="Operating Point",
                   marker=dict(color="#2DB37A", size=13, symbol="diamond",
                               line=dict(width=2, color="white"))),
    ],
    frames=frames
)

fig.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#444"),
    xaxis=dict(
        title="Liquid Flow Rate (STB/day)",
        gridcolor="#F0F0F0",
        zeroline=False,
        rangemode="tozero",
    ),
    yaxis=dict(
        title="Bottomhole Flowing Pressure, Pwf (psi)",
        gridcolor="#F0F0F0",
        zeroline=False,
        range=[0, Pr * 1.05],
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left",  x=0,
        font=dict(size=12),
        bgcolor="rgba(255,255,255,0)",
    ),
    hovermode="x unified",
    margin=dict(l=60, r=20, t=50, b=50),
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=1.0, y=1.12, xanchor="right",
        buttons=[dict(
            label="▶  Play Animation",
            method="animate",
            args=[None, dict(
                frame=dict(duration=35, redraw=True),
                fromcurrent=False,
                transition=dict(duration=0)
            )]
        )]
    )]
)

st.plotly_chart(fig, use_container_width=True)

# ── BOTTOM INFO ROW ────────────────────────────────────────────
st.divider()
b1, b2, b3, b4 = st.columns(4)
b1.markdown(f"**Drawdown** &nbsp; `{drawdown_pct}%`")
b2.markdown(f"**Efficiency vs Qmax** &nbsp; `{efficiency}%`")
b3.markdown(f"**Hydrostatic ΔP** &nbsp; `{delta_hyd:,.0f} psi`")
b4.markdown(f"**Well Status** &nbsp; {'✅ Flowing' if is_flowing else '🔴 No natural flow'}")
import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nodal Analysis Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Minimal clean CSS ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FAFAFA;
    border-right: 1px solid #EFEFEF;
}

/* Metric cards: just a subtle shadow */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #EFEFEF;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* Metric label */
[data-testid="metric-container"] label {
    font-size: 12px !important;
    color: #888 !important;
    font-weight: 500 !important;
}

/* Metric value */
[data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────
st.sidebar.title("⚙️ Parameters")

st.sidebar.markdown("#### Reservoir (IPR)")
Pr       = st.sidebar.number_input("Reservoir Pressure — Pr (psi)",     1000, 8000, 3500, 100)
Pwf_test = st.sidebar.number_input("Test Flowing Pressure — Pwf (psi)", 500,  7500, 2500, 100)
Q_test   = st.sidebar.number_input("Test Flow Rate — Q (STB/day)",      100,  5000, 1200, 50)

st.sidebar.markdown("#### Wellbore (TPR)")
Depth         = st.sidebar.number_input("TVD (ft)",                2000, 15000, 8000, 500)
Pwh           = st.sidebar.number_input("Wellhead Pressure (psi)", 50,   1500,  300,  50)
fluid_grad    = st.sidebar.slider("Fluid Gradient (psi/ft)",   0.15, 0.50, 0.35, 0.01,
                                  help="Water ≈ 0.433 | Light oil ≈ 0.30–0.35")
friction_coef = st.sidebar.slider("Tubing Friction Coefficient", 0.1, 10.0, 2.0, 0.1,
                                  help="Higher = smaller tubing / more restriction")

# ── HEADER ─────────────────────────────────────────────────────
st.markdown("## 🛢️ Nodal Analysis Dashboard")
st.markdown(
    "<p style='color:#888; margin-top:-12px; font-size:14px;'>"
    "Vogel IPR · Physical TPR · Operating Point</p>",
    unsafe_allow_html=True
)
st.divider()

# ── VALIDATION ─────────────────────────────────────────────────
if Pwf_test >= Pr:
    st.error("❌ Test Pwf must be less than Reservoir Pressure (Pr).")
    st.stop()

# ── CALCULATIONS ───────────────────────────────────────────────
vogel_denom = 1 - 0.2*(Pwf_test/Pr) - 0.8*(Pwf_test/Pr)**2
Qmax = Q_test / vogel_denom if vogel_denom > 0 else 0
PI   = Q_test / (Pr - Pwf_test)

q_arr   = np.linspace(0, Qmax, 300)
pwf_ipr = np.array([
    ((-0.2 + np.sqrt(max(0.0, 0.04 + 3.2*(1 - q/Qmax)))) / 1.6) * Pr
    for q in q_arr
])
delta_hyd = fluid_grad * Depth
pwf_tpr   = Pwh + delta_hyd + (friction_coef * 1e-4 * (q_arr ** 1.85))

diff   = np.abs(pwf_ipr - pwf_tpr)
idx_op = np.argmin(diff)
q_op   = q_arr[idx_op]
pwf_op = pwf_ipr[idx_op]

is_flowing = not (pwf_tpr[0] > Pr or q_op <= 1.0)
if not is_flowing:
    q_op = pwf_op = 0.0

efficiency   = round((q_op / Qmax) * 100, 1) if is_flowing else 0.0
drawdown_pct = round((1 - pwf_op / Pr) * 100, 1) if is_flowing else 0.0

# ── KPI METRICS ────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("⚡ Operating Rate (Q_op)",     f"{q_op:,.0f} STB/day")
c2.metric("📉 Operating BHP (Pwf_op)",   f"{pwf_op:,.0f} psi")
c3.metric("🏆 Maximum Rate (Qmax)",       f"{Qmax:,.0f} STB/day")
c4.metric("📈 Productivity Index (PI)",   f"{PI:.3f} STB/d/psi")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

if not is_flowing:
    st.warning("⚠️ Well cannot flow naturally — static fluid column exceeds reservoir energy. Consider artificial lift.")

# ── ANIMATED CHART ─────────────────────────────────────────────
n      = len(q_arr)
steps  = 40

frames = []
for i in range(1, steps + 1):
    end = max(2, int(n * i / steps))
    fd  = [
        go.Scatter(x=q_arr[:end], y=pwf_ipr[:end],
                   mode="lines", line=dict(color="#4F8EF7", width=2.5)),
        go.Scatter(x=q_arr[:end], y=pwf_tpr[:end],
                   mode="lines", line=dict(color="#F76B6B", width=2.5)),
    ]
    if i == steps and is_flowing:
        fd.append(go.Scatter(
            x=[q_op], y=[pwf_op],
            mode="markers+text",
            marker=dict(color="#2DB37A", size=13, symbol="diamond",
                        line=dict(width=2, color="white")),
            text=[f"  ({q_op:.0f} STB/d,  {pwf_op:.0f} psi)"],
            textposition="top right",
            textfont=dict(size=12, color="#2DB37A")
        ))
    frames.append(go.Frame(data=fd, name=str(i)))

fig = go.Figure(
    data=[
        go.Scatter(x=[], y=[], mode="lines",
                   name="IPR — Inflow",
                   line=dict(color="#4F8EF7", width=2.5),
                   fill="tozeroy", fillcolor="rgba(79,142,247,0.07)"),
        go.Scatter(x=[], y=[], mode="lines",
                   name="TPR — Tubing",
                   line=dict(color="#F76B6B", width=2.5),
                   fill="tozeroy", fillcolor="rgba(247,107,107,0.06)"),
        go.Scatter(x=[], y=[], mode="markers+text",
                   name="Operating Point",
                   marker=dict(color="#2DB37A", size=13, symbol="diamond",
                               line=dict(width=2, color="white"))),
    ],
    frames=frames
)

fig.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#444"),
    xaxis=dict(
        title="Liquid Flow Rate (STB/day)",
        gridcolor="#F0F0F0",
        zeroline=False,
        rangemode="tozero",
    ),
    yaxis=dict(
        title="Bottomhole Flowing Pressure, Pwf (psi)",
        gridcolor="#F0F0F0",
        zeroline=False,
        range=[0, Pr * 1.05],
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="left",  x=0,
        font=dict(size=12),
        bgcolor="rgba(255,255,255,0)",
    ),
    hovermode="x unified",
    margin=dict(l=60, r=20, t=50, b=50),
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        x=1.0, y=1.12, xanchor="right",
        buttons=[dict(
            label="▶  Play Animation",
            method="animate",
            args=[None, dict(
                frame=dict(duration=35, redraw=True),
                fromcurrent=False,
                transition=dict(duration=0)
            )]
        )]
    )]
)

st.plotly_chart(fig, use_container_width=True)

# ── BOTTOM INFO ROW ────────────────────────────────────────────
st.divider()
b1, b2, b3, b4 = st.columns(4)
b1.markdown(f"**Drawdown** &nbsp; `{drawdown_pct}%`")
b2.markdown(f"**Efficiency vs Qmax** &nbsp; `{efficiency}%`")
b3.markdown(f"**Hydrostatic ΔP** &nbsp; `{delta_hyd:,.0f} psi`")
b4.markdown(f"**Well Status** &nbsp; {'✅ Flowing' if is_flowing else '🔴 No natural flow'}")
