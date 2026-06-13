import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nodal Analysis Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS: Bank-Maintain style ──────────────────────────────
st.markdown("""
<style>
/* ---- Google Font ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ---- Global reset ---- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #F0F2F8;
}

/* ---- Hide default Streamlit chrome ---- */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #1A1A2E !important;
    width: 230px !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] * { color: #B0B8D1 !important; }

/* Logo bar */
.sidebar-logo {
    background: linear-gradient(135deg, #8B5CF6, #EC4899);
    padding: 20px 18px;
    border-radius: 0;
    margin-bottom: 10px;
}
.sidebar-logo h2 {
    color: white !important;
    font-size: 17px;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.3px;
}

/* Nav items */
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 8px;
    margin: 2px 8px;
    cursor: pointer;
    transition: all 0.2s;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSlider label { font-size: 12px !important; }
[data-testid="stSidebar"] .stNumberInput input { font-size: 13px !important; }

/* Section headers in sidebar */
[data-testid="stSidebar"] h2 {
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #555E7A !important;
    padding: 16px 16px 6px;
    margin: 0;
}

/* ── TOP NAV BAR ─────────────────────────────────────────────── */
.top-nav {
    background: white;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-bottom: 24px;
}
.top-nav h1 {
    font-size: 22px;
    font-weight: 700;
    color: #1A1A2E;
    margin: 0;
}
.top-nav .breadcrumb {
    font-size: 12px;
    color: #8892A4;
    margin-bottom: 2px;
}
.btn-export {
    background: linear-gradient(135deg, #8B5CF6, #EC4899);
    color: white !important;
    border: none;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
}

/* ── KPI CARDS ───────────────────────────────────────────────── */
.kpi-row { display: flex; gap: 16px; padding: 0 28px 20px; flex-wrap: wrap; }
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 18px 20px;
    flex: 1;
    min-width: 160px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.1); }
.kpi-icon {
    width: 44px; height: 44px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
}
.kpi-label { font-size: 11px; color: #8892A4; font-weight: 500; margin-bottom: 3px; }
.kpi-value { font-size: 18px; font-weight: 700; color: #1A1A2E; }
.kpi-sub   { font-size: 11px; color: #8892A4; }

/* icon colours */
.icon-purple { background: #F3EEFF; }
.icon-teal   { background: #E6FAF5; }
.icon-orange { background: #FFF3E8; }
.icon-pink   { background: #FEE8F3; }

/* ── MAIN CONTENT AREA ───────────────────────────────────────── */
.main-grid {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 20px;
    padding: 0 28px 28px;
}
.panel {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.panel-title {
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 4px;
}
.panel-sub {
    font-size: 12px;
    color: #8892A4;
    margin-bottom: 18px;
}

/* ── STATUS BADGE ─────────────────────────────────────────────── */
.badge-ok   { background:#E6FAF5; color:#0D9F6E; border-radius:20px; padding:4px 12px; font-size:12px; font-weight:600; display:inline-block; }
.badge-warn { background:#FFF3E8; color:#E07B00; border-radius:20px; padding:4px 12px; font-size:12px; font-weight:600; display:inline-block; }

/* ── RIGHT PANEL STAT ROWS ───────────────────────────────────── */
.stat-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #F4F5F8; }
.stat-row:last-child { border-bottom: none; }
.stat-name { font-size:12px; color:#8892A4; }
.stat-val  { font-size:14px; font-weight:700; color:#1A1A2E; }

/* ── DONUT LEGEND ─────────────────────────────────────────────── */
.donut-legend { display:flex; gap:18px; margin-top:14px; justify-content:center; }
.leg-item { display:flex; align-items:center; gap:6px; font-size:12px; color:#555; }
.leg-dot  { width:10px; height:10px; border-radius:50%; }

/* ── WARN BOX ─────────────────────────────────────────────────── */
.warn-box {
    background:#FFF3E8; border-left:4px solid #F59E0B;
    border-radius:8px; padding:12px 16px;
    font-size:12px; color:#92400E; margin-top:16px;
}

/* override Streamlit plotly container padding */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>🛢️ Nodal Analysis Pro</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Reservoir (IPR)")
    Pr       = st.number_input("Reservoir Pressure (Pr) [psi]",    1000, 8000, 3500, 100)
    Pwf_test = st.number_input("Test Flowing Pressure (Pwf) [psi]", 500,  7500, 2500, 100)
    Q_test   = st.number_input("Test Flow Rate (Q) [STB/day]",      100,  5000, 1200, 50)

    st.markdown("## Wellbore (TPR)")
    Depth        = st.number_input("TVD [ft]",           2000, 15000, 8000, 500)
    Pwh          = st.number_input("Wellhead Pressure [psi]", 50, 1500, 300, 50)
    fluid_grad   = st.slider("Fluid Gradient [psi/ft]",  0.15, 0.50, 0.35, 0.01,
                             help="Water ~0.433 | Light Oil ~0.30–0.35")
    friction_coef = st.slider("Tubing Friction Coef.",   0.1, 10.0, 2.0, 0.1,
                              help="Higher = smaller tubing diameter")


# ── CALCULATIONS ──────────────────────────────────────────────────
error = Pwf_test >= Pr
if not error:
    vogel_denom = 1 - 0.2*(Pwf_test/Pr) - 0.8*(Pwf_test/Pr)**2
    Qmax = Q_test / vogel_denom if vogel_denom > 0 else 0
    PI   = Q_test / (Pr - Pwf_test)

    q_arr   = np.linspace(0, Qmax, 300)
    pwf_ipr = np.array([
        ((-0.2 + np.sqrt(max(0, 0.04 + 3.2*(1 - q/Qmax)))) / 1.6) * Pr
        for q in q_arr
    ])
    delta_hyd = fluid_grad * Depth
    pwf_tpr   = Pwh + delta_hyd + (friction_coef * 1e-4 * (q_arr ** 1.85))

    diff            = np.abs(pwf_ipr - pwf_tpr)
    idx_op          = np.argmin(diff)
    q_op            = q_arr[idx_op]
    pwf_op          = pwf_ipr[idx_op]
    is_flowing      = not (pwf_tpr[0] > Pr or q_op <= 1.0)
    if not is_flowing:
        q_op = pwf_op = 0.0

    drawdown_pct = round((1 - pwf_op/Pr)*100, 1) if is_flowing else 0
    efficiency   = round((q_op/Qmax)*100, 1)     if is_flowing else 0


# ── TOP NAV ───────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div>
    <div class="breadcrumb">Dashboard › Analytics</div>
    <h1>Well Performance Analytics</h1>
  </div>
  <div style="display:flex;gap:10px;align-items:center;">
    <span style="font-size:13px;color:#8892A4;">Vogel IPR · Physical TPR</span>
    <span class="btn-export">⬇ Export</span>
  </div>
</div>
""", unsafe_allow_html=True)

if error:
    st.error("❌ Test Pwf must be less than Reservoir Pressure (Pr).")
    st.stop()


# ── KPI CARDS ─────────────────────────────────────────────────────
badge = '<span class="badge-ok">● Flowing</span>' if is_flowing else '<span class="badge-warn">● No Flow</span>'

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-icon icon-purple">⚡</div>
    <div>
      <div class="kpi-label">Operating Flow Rate</div>
      <div class="kpi-value">{q_op:,.0f}</div>
      <div class="kpi-sub">STB/day &nbsp;{badge}</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon icon-teal">📉</div>
    <div>
      <div class="kpi-label">Operating BHP (Pwf_op)</div>
      <div class="kpi-value">{pwf_op:,.0f}</div>
      <div class="kpi-sub">psi</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon icon-orange">🏆</div>
    <div>
      <div class="kpi-label">Max Potential (Qmax)</div>
      <div class="kpi-value">{Qmax:,.0f}</div>
      <div class="kpi-sub">STB/day</div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon icon-pink">📈</div>
    <div>
      <div class="kpi-label">Productivity Index (PI)</div>
      <div class="kpi-value">{PI:.3f}</div>
      <div class="kpi-sub">STB/day/psi</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── MAIN GRID ─────────────────────────────────────────────────────
col_main, col_side = st.columns([3, 1])

with col_main:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Nodal Analysis Plot</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Vogel IPR  ·  Physical TPR  ·  Operating Point</div>', unsafe_allow_html=True)

    # ── ANIMATED PLOTLY CHART ────────────────────────────────────
    n = len(q_arr)

    # Build animation frames: curves draw in progressively
    frames = []
    steps  = 30
    for i in range(1, steps + 1):
        end = max(2, int(n * i / steps))
        frame_traces = [
            go.Scatter(x=q_arr[:end], y=pwf_ipr[:end],
                       mode='lines', line=dict(color='#8B5CF6', width=3)),
            go.Scatter(x=q_arr[:end], y=pwf_tpr[:end],
                       mode='lines', line=dict(color='#EC4899', width=3)),
        ]
        if i == steps and is_flowing:
            frame_traces.append(
                go.Scatter(
                    x=[q_op], y=[pwf_op],
                    mode='markers+text',
                    marker=dict(color='#0D9F6E', size=14, symbol='diamond',
                                line=dict(width=2, color='white')),
                    text=[f"  ({q_op:.0f} STB/d, {pwf_op:.0f} psi)"],
                    textposition="top right",
                    textfont=dict(size=13, color='#0D9F6E')
                )
            )
        frames.append(go.Frame(data=frame_traces, name=str(i)))

    # Initial (empty) traces
    fig = go.Figure(
        data=[
            go.Scatter(x=[], y=[], mode='lines',
                       name='IPR (Vogel)',
                       line=dict(color='#8B5CF6', width=3),
                       fill='tozeroy',
                       fillcolor='rgba(139,92,246,0.08)'),
            go.Scatter(x=[], y=[], mode='lines',
                       name='TPR (Physical)',
                       line=dict(color='#EC4899', width=3),
                       fill='tozeroy',
                       fillcolor='rgba(236,72,153,0.06)'),
            go.Scatter(x=[], y=[], mode='markers+text',
                       name='Operating Point',
                       marker=dict(color='#0D9F6E', size=14, symbol='diamond',
                                   line=dict(width=2, color='white'))),
        ],
        frames=frames
    )

    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=12, color='#555E7A'),
        xaxis=dict(
            title='Liquid Flow Rate (STB/day)',
            gridcolor='rgba(200,205,220,0.4)',
            zeroline=False, rangemode='tozero',
            title_font=dict(size=12)
        ),
        yaxis=dict(
            title='Bottomhole Flowing Pressure, Pwf (psi)',
            gridcolor='rgba(200,205,220,0.4)',
            zeroline=False, range=[0, Pr*1.05],
            title_font=dict(size=12)
        ),
        legend=dict(
            yanchor='top', y=0.97, xanchor='right', x=0.99,
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#E5E7EB', borderwidth=1,
            font=dict(size=12)
        ),
        hovermode='x unified',
        margin=dict(l=60, r=20, t=20, b=50),
        updatemenus=[dict(
            type='buttons', showactive=False,
            y=1.08, x=0.0, xanchor='left',
            buttons=[dict(
                label='▶  Animate',
                method='animate',
                args=[None, dict(
                    frame=dict(duration=40, redraw=True),
                    fromcurrent=False,
                    transition=dict(duration=0)
                )]
            )]
        )]
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


with col_side:
    # ── RIGHT PANEL: Well Summary ─────────────────────────────────
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Well Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Reservoir & Tubing</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-row"><span class="stat-name">Reservoir Pressure</span><span class="stat-val">{Pr:,} psi</span></div>
    <div class="stat-row"><span class="stat-name">Test Pwf</span><span class="stat-val">{Pwf_test:,} psi</span></div>
    <div class="stat-row"><span class="stat-name">Test Flow Rate</span><span class="stat-val">{Q_test:,} STB/d</span></div>
    <div class="stat-row"><span class="stat-name">TVD</span><span class="stat-val">{Depth:,} ft</span></div>
    <div class="stat-row"><span class="stat-name">Wellhead Pressure</span><span class="stat-val">{Pwh} psi</span></div>
    <div class="stat-row"><span class="stat-name">Fluid Gradient</span><span class="stat-val">{fluid_grad} psi/ft</span></div>
    <div class="stat-row"><span class="stat-name">Hydrostatic ΔP</span><span class="stat-val">{delta_hyd:,.0f} psi</span></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── RIGHT PANEL: Donut chart ──────────────────────────────────
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Well Efficiency</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">% of Maximum Potential</div>', unsafe_allow_html=True)

    unused = max(0, 100 - efficiency)
    donut  = go.Figure(go.Pie(
        values=[efficiency, unused],
        labels=['Producing', 'Remaining'],
        hole=0.68,
        marker=dict(colors=['#8B5CF6', '#EC4899']),
        textinfo='none',
        hovertemplate='%{label}: %{value:.1f}%<extra></extra>'
    ))
    donut.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='white',
        annotations=[dict(
            text=f'<b>{efficiency}%</b>',
            x=0.5, y=0.5, font=dict(size=22, color='#1A1A2E', family='Inter'),
            showarrow=False
        )]
    )
    st.plotly_chart(donut, use_container_width=True, config={'displayModeBar': False})

    st.markdown(f"""
    <div class="donut-legend">
      <div class="leg-item"><div class="leg-dot" style="background:#8B5CF6"></div>{efficiency}% Producing</div>
      <div class="leg-item"><div class="leg-dot" style="background:#EC4899"></div>{unused:.1f}% Remaining</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:16px">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-row"><span class="stat-name">Drawdown</span><span class="stat-val">{drawdown_pct}%</span></div>
    <div class="stat-row"><span class="stat-name">Drive Energy</span><span class="stat-val">{"✅ Sufficient" if is_flowing else "❌ Insufficient"}</span></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not is_flowing:
        st.markdown("""
        <div class="warn-box">
          ⚠️ Static fluid column exceeds reservoir energy. Consider artificial lift.
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
