# ============================================================
#           Canadian Retail Sales Dashboard — Dash 
# ============================================================
# Run:  python retail_dashboard.py
# Open: http://127.0.0.1:8050
#
# FIX: suppress_callback_exceptions=True is REQUIRED because
#      chart IDs live inside tab content that is rendered
#      dynamically — Dash would error if it checked IDs before
#      the tab is drawn.
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ── 1. LOAD DATA ─────────────────────────────────────────────
df = pd.read_csv("Dataset/retail_sales_cleaned.csv")
df["REF_DATE"] = pd.to_datetime(df["REF_DATE"])

# Top-level industries only (avoids double-counting sub-sectors)
TOP_INDUSTRIES = [
    "Motor vehicle and parts dealers",
    "Building material and garden equipment and supplies dealers",
    "Food and beverage retailers",
    "Furniture, home furnishings, electronics and appliances retailers",
    "General merchandise retailers",
    "Health and personal care retailers",
    "Gasoline stations and fuel vendors",
    "Clothing, clothing accessories, shoes, jewellery, luggage and leather goods retailers",
    "Sporting goods, hobby, musical instrument, book, and miscellaneous retailers",
    "Cannabis retailers",
]

# Shorter names for chart labels
SHORT = {
    "Motor vehicle and parts dealers": "Motor Vehicle & Parts",
    "Building material and garden equipment and supplies dealers": "Building Materials",
    "Food and beverage retailers": "Food & Beverage",
    "Furniture, home furnishings, electronics and appliances retailers": "Furniture & Electronics",
    "General merchandise retailers": "General Merchandise",
    "Health and personal care retailers": "Health & Personal Care",
    "Gasoline stations and fuel vendors": "Gasoline & Fuel",
    "Clothing, clothing accessories, shoes, jewellery, luggage and leather goods retailers": "Clothing & Accessories",
    "Sporting goods, hobby, musical instrument, book, and miscellaneous retailers": "Sporting & Hobby",
    "Cannabis retailers": "Cannabis",
}

PROVINCES   = sorted(df[df["Geo_Level"] == "Province"]["GEO"].unique())
YEARS       = sorted(df["Year"].unique())
MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── 2. COLOURS (Power BI palette) ────────────────────────────
BG        = "#f3f2f1"
CARD_BG   = "#ffffff"
ACCENT    = "#0078d4"   # Power BI blue
ACCENT2   = "#e67e22"   # orange for contrast
TEXT_DARK = "#252423"
TEXT_GREY = "#605e5c"
HEADER_BG = "#0078d4"


# ── 3. UTILITY: empty figure when no data ────────────────────
def empty_fig(msg="No data for selection"):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=13, color=TEXT_GREY))
    fig.update_layout(paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      margin=dict(t=10, b=10, l=10, r=10))
    return fig


# ── 4. UTILITY: apply shared chart style ─────────────────────
def style_fig(fig, y_fmt=None, x_fmt=None):
    """Consistent Power BI-style chart formatting."""
    fig.update_layout(
        paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
        font=dict(family="Segoe UI, Arial", size=11, color=TEXT_DARK),
        margin=dict(t=10, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, font=dict(size=9),
                    bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False,
                     tickfont=dict(size=10), title_text="")
    fig.update_yaxes(showgrid=True, gridcolor="#edebe9", zeroline=False,
                     tickfont=dict(size=10), title_text="")
    if y_fmt:
        fig.update_yaxes(tickformat=y_fmt)
    if x_fmt:
        fig.update_xaxes(tickformat=x_fmt)


# ── 5. LAYOUT HELPERS ────────────────────────────────────────
def card(children, extra_style=None):
    """White rounded card — matches Power BI visual container."""
    s = {"background": CARD_BG, "borderRadius": "8px",
         "boxShadow": "0 1px 4px rgba(0,0,0,.12)",
         "padding": "16px", "marginBottom": "0"}
    if extra_style:
        s.update(extra_style)
    return html.Div(children, style=s)


def kpi_card(label, value, delta=None, delta_label=""):
    """Single KPI tile (Power BI card visual)."""
    delta_el = []
    if delta is not None:
        color = "#107c10" if delta >= 0 else "#d13438"
        arrow = "▲" if delta >= 0 else "▼"
        delta_el = [html.Span(f"{arrow} {abs(delta):.1f}% {delta_label}",
                              style={"color": color, "fontSize": "11px"})]
    return html.Div([
        html.P(label, style={"margin": "0", "fontSize": "11px", "color": TEXT_GREY,
                             "fontWeight": "600", "textTransform": "uppercase",
                             "letterSpacing": "0.5px"}),
        html.H3(value, style={"margin": "4px 0", "color": TEXT_DARK,
                               "fontSize": "20px", "fontWeight": "700"}),
        *delta_el,
    ], style={"background": CARD_BG, "borderRadius": "8px",
              "boxShadow": "0 1px 4px rgba(0,0,0,.12)",
              "padding": "14px 18px",
              "borderLeft": f"4px solid {ACCENT}",
              "flex": "1", "minWidth": "140px"})


# ── 6. APP — suppress_callback_exceptions is the key fix ─────
# Without this Dash raises "ID not found in layout" because the
# chart <div>s only appear after a tab is selected.
app = Dash(__name__,
           title="Canadian Retail Dashboard",
           suppress_callback_exceptions=True)   # ← THE FIX


# ── 7. ROOT LAYOUT ───────────────────────────────────────────
# Important: every Output ID used in callbacks must either be
# in this static layout OR suppress_callback_exceptions=True.
app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif",
           "background": BG, "minHeight": "100vh"},
    children=[

        # Header
        html.Div([
            html.H2("🛒  Canadian Retail Sales Dashboard",
                    style={"margin": "0", "color": "#fff", "fontSize": "20px"}),
            html.Span("Statistics Canada · 2017 – 2026",
                      style={"color": "#c8e4f8", "fontSize": "12px"}),
        ], style={"background": HEADER_BG, "padding": "14px 24px",
                  "display": "flex", "justifyContent": "space-between",
                  "alignItems": "center"}),

        # Global filter bar
        html.Div([
            html.Div([
                html.Label("Province",
                           style={"fontSize": "11px", "fontWeight": "600",
                                  "color": TEXT_GREY, "display": "block",
                                  "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="filter-province",
                    options=[{"label": "All Provinces", "value": "All"}] +
                            [{"label": p, "value": p} for p in PROVINCES],
                    value="All", clearable=False,
                ),
            ], style={"flex": "1", "minWidth": "160px"}),

            html.Div([
                html.Label("Year",
                           style={"fontSize": "11px", "fontWeight": "600",
                                  "color": TEXT_GREY, "display": "block",
                                  "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="filter-year",
                    options=[{"label": "All Years", "value": 0}] +
                            [{"label": str(y), "value": y} for y in YEARS],
                    value=0, clearable=False,
                ),
            ], style={"flex": "1", "minWidth": "120px"}),

            html.Div([
                html.Label("Adjustment Type",
                           style={"fontSize": "11px", "fontWeight": "600",
                                  "color": TEXT_GREY, "display": "block",
                                  "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="filter-adj",
                    options=[{"label": "Unadjusted",          "value": "Unadjusted"},
                             {"label": "Seasonally Adjusted", "value": "Seasonally adjusted"}],
                    value="Unadjusted", clearable=False,
                ),
            ], style={"flex": "1", "minWidth": "180px"}),
        ], style={"display": "flex", "gap": "16px", "padding": "12px 24px",
                  "background": "#fff", "borderBottom": "1px solid #edebe9",
                  "flexWrap": "wrap"}),

        # Tab navigation (Power BI pages)
        html.Div([
            dcc.Tabs(
                id="tabs", value="exec",
                children=[
                    dcc.Tab(label="📊  Executive Overview",   value="exec"),
                    dcc.Tab(label="🏭  Industry Performance", value="industry"),
                    dcc.Tab(label="🗺️  Geographic Analysis",  value="geo"),
                    dcc.Tab(label="📈  Forecasting",          value="forecast"),
                ],
                colors={"border": ACCENT, "primary": ACCENT, "background": BG},
            ),
        ], style={"padding": "0 24px", "background": "#fff",
                  "borderBottom": f"2px solid {ACCENT}"}),

        # ↓ Tab content is injected here dynamically by the callback below
        html.Div(id="tab-content", style={"padding": "20px 24px"}),
    ]
)


# ── 8. TAB ROUTER — renders the correct page HTML ─────────────
# This single callback swaps the entire page content.
# Chart-level callbacks fire only after this renders their IDs.
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
)
def render_tab(tab):
    if tab == "exec":
        return exec_page()
    elif tab == "industry":
        return industry_page()
    elif tab == "geo":
        return geo_page()
    else:
        return forecast_page()


# ══════════════════════════════════════════════════════════════
#  PAGE 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════
def exec_page():
    """Returns the HTML skeleton for the Executive Overview tab."""
    row = {"display": "flex", "gap": "16px", "marginBottom": "16px"}
    return html.Div([
        # KPI tiles
        html.Div(id="exec-kpis",
                 style={"display": "flex", "gap": "12px",
                        "flexWrap": "wrap", "marginBottom": "16px"}),
        # Row 1
        html.Div([
            card([html.H4("Monthly Sales Trend",
                          style={"margin": "0 0 8px", "fontSize": "13px",
                                 "color": TEXT_DARK}),
                  dcc.Graph(id="exec-trend", style={"height": "280px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "2"}),
            card([html.H4("Industry Market Share",
                          style={"margin": "0 0 8px", "fontSize": "13px",
                                 "color": TEXT_DARK}),
                  dcc.Graph(id="exec-donut", style={"height": "280px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
        # Row 2
        html.Div([
            card([html.H4("Top Industries by Total Sales",
                          style={"margin": "0 0 8px", "fontSize": "13px",
                                 "color": TEXT_DARK}),
                  dcc.Graph(id="exec-bar", style={"height": "260px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
            card([html.H4("E-Commerce Share of Total Retail",
                          style={"margin": "0 0 8px", "fontSize": "13px",
                                 "color": TEXT_DARK}),
                  dcc.Graph(id="exec-ecomm", style={"height": "260px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
    ])


@app.callback(
    Output("exec-kpis",  "children"),
    Output("exec-trend", "figure"),
    Output("exec-donut", "figure"),
    Output("exec-bar",   "figure"),
    Output("exec-ecomm", "figure"),
    Input("filter-province", "value"),
    Input("filter-year",     "value"),
    Input("filter-adj",      "value"),
)
def cb_exec(prov, year, adj):
    geo = "Canada" if prov == "All" else prov

    # National / selected-province total retail series
    base = df[
        (df["GEO"] == geo) &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == adj)
    ].sort_values("REF_DATE").copy()
    if year:
        base = base[base["Year"] == year]

    # --- KPIs ---
    total   = base["Sales_Actual"].sum()
    avg_mon = base["Sales_Actual"].mean() if not base.empty else 0
    mom = ((base["Sales_Actual"].iloc[-1] - base["Sales_Actual"].iloc[-2])
           / base["Sales_Actual"].iloc[-2] * 100) if len(base) >= 2 else None
    yoy = ((base["Sales_Actual"].iloc[-1] - base["Sales_Actual"].iloc[-13])
           / base["Sales_Actual"].iloc[-13] * 100) if len(base) >= 13 else None

    def fmt(v):
        return f"${v/1e12:.2f}T" if v >= 1e12 else f"${v/1e9:.1f}B"

    kpis = [
        kpi_card("Total Retail Sales", fmt(total)),
        kpi_card("Avg Monthly Sales",  fmt(avg_mon)),
        kpi_card("MoM Growth",
                 f"{mom:+.1f}%" if mom is not None else "N/A",
                 delta=mom, delta_label="vs prev month"),
        kpi_card("YoY Growth",
                 f"{yoy:+.1f}%" if yoy is not None else "N/A",
                 delta=yoy, delta_label="vs same month last year"),
    ]

    # --- Monthly trend area chart ---
    if base.empty:
        trend_fig = empty_fig()
    else:
        trend_fig = px.area(base, x="REF_DATE", y="Sales_Actual",
                            color_discrete_sequence=[ACCENT])
        trend_fig.update_traces(
            fill="tozeroy", line_color=ACCENT,
            fillcolor="rgba(0,120,212,0.15)",
            hovertemplate="%{x|%b %Y}  $%{y:,.0f}<extra></extra>",
        )
        style_fig(trend_fig, y_fmt="$,.2s")

    # --- Industry donut ---
    ind = df[
        (df["GEO"] == "Canada") &
        (df["Industry"].isin(TOP_INDUSTRIES)) &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].copy()
    if year:
        ind = ind[ind["Year"] == year]
    ind_sum = ind.groupby("Industry")["Sales_Actual"].sum().reset_index()
    ind_sum["Label"] = ind_sum["Industry"].map(SHORT)

    if ind_sum.empty:
        donut_fig = empty_fig()
    else:
        donut_fig = px.pie(ind_sum, values="Sales_Actual", names="Label",
                           hole=0.55,
                           color_discrete_sequence=px.colors.qualitative.Set2)
        donut_fig.update_traces(
            textinfo="percent",
            hovertemplate="%{label}<br>$%{value:,.0f}<extra></extra>",
        )
        donut_fig.update_layout(
            paper_bgcolor=CARD_BG, margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(font=dict(size=9)),
        )

    # --- Top industries horizontal bar ---
    ind_bar = ind_sum.sort_values("Sales_Actual").tail(8)
    if ind_bar.empty:
        bar_fig = empty_fig()
    else:
        bar_fig = px.bar(ind_bar, x="Sales_Actual", y="Label",
                         orientation="h",
                         color_discrete_sequence=[ACCENT])
        bar_fig.update_traces(
            hovertemplate="%{y}  $%{x:,.0f}<extra></extra>",
        )
        style_fig(bar_fig, x_fmt="$,.2s")

    # --- E-commerce share line ---
    ec = df[
        (df["GEO"] == "Canada") &
        (df["Industry"] == "Retail trade") &
        (df["Adjustments"] == "Unadjusted")
    ].copy()
    if year:
        ec = ec[ec["Year"] == year]
    tot_s  = ec[ec["Sales"] == "Total retail sales"].groupby("REF_DATE")["Sales_Actual"].sum()
    ecom_s = ec[ec["Sales"] == "Retail e-commerce sales"].groupby("REF_DATE")["Sales_Actual"].sum()
    share  = (ecom_s / tot_s * 100).reset_index()
    share.columns = ["REF_DATE", "Share"]

    if share.empty:
        ecomm_fig = empty_fig()
    else:
        ecomm_fig = px.line(share, x="REF_DATE", y="Share",
                            color_discrete_sequence=[ACCENT2])
        ecomm_fig.update_traces(
            line_width=2,
            hovertemplate="%{x|%b %Y}  %{y:.2f}%<extra></extra>",
        )
        style_fig(ecomm_fig)
        ecomm_fig.update_yaxes(ticksuffix="%")

    return kpis, trend_fig, donut_fig, bar_fig, ecomm_fig


# ══════════════════════════════════════════════════════════════
#  PAGE 2 — INDUSTRY PERFORMANCE
# ══════════════════════════════════════════════════════════════
def industry_page():
    row = {"display": "flex", "gap": "16px", "marginBottom": "16px"}
    return html.Div([
        html.Div([
            card([html.H4("Industry Sales Trend",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="ind-trend", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "2"}),
            card([html.H4("Growth Rate 2017 → Latest",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="ind-growth", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
        html.Div([
            card([html.H4("Seasonality Heatmap  (Industry × Month)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="ind-heat", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
            card([html.H4("Adjusted vs Unadjusted Sales",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="ind-adj", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
    ])


@app.callback(
    Output("ind-trend",  "figure"),
    Output("ind-growth", "figure"),
    Output("ind-heat",   "figure"),
    Output("ind-adj",    "figure"),
    Input("filter-year", "value"),
    Input("filter-adj",  "value"),
)
def cb_industry(year, adj):
    # --- Trend lines per industry ---
    ind = df[
        (df["GEO"] == "Canada") &
        (df["Industry"].isin(TOP_INDUSTRIES)) &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == adj)
    ].copy()
    if year:
        ind = ind[ind["Year"] == year]
    ind["Label"] = ind["Industry"].map(SHORT)

    if ind.empty:
        trend_fig = empty_fig()
    else:
        agg = ind.groupby(["REF_DATE", "Label"])["Sales_Actual"].sum().reset_index()
        trend_fig = px.line(agg, x="REF_DATE", y="Sales_Actual", color="Label",
                            color_discrete_sequence=px.colors.qualitative.Set2)
        trend_fig.update_traces(line_width=1.8)
        style_fig(trend_fig, y_fmt="$,.2s")

    # --- Growth rate bar ---
    gr = df[
        (df["GEO"] == "Canada") &
        (df["Industry"].isin(TOP_INDUSTRIES)) &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].groupby(["Year", "Industry"])["Sales_Actual"].sum().reset_index()

    f_yr, l_yr = gr["Year"].min(), gr["Year"].max()
    fv = gr[gr["Year"] == f_yr].set_index("Industry")["Sales_Actual"]
    lv = gr[gr["Year"] == l_yr].set_index("Industry")["Sales_Actual"]
    growth = ((lv - fv) / fv * 100).reset_index()
    growth.columns = ["Industry", "Growth_pct"]
    growth["Label"] = growth["Industry"].map(SHORT)
    growth = growth.sort_values("Growth_pct")

    if growth.empty:
        growth_fig = empty_fig()
    else:
        growth_fig = px.bar(growth, x="Growth_pct", y="Label",
                            orientation="h", color="Growth_pct",
                            color_continuous_scale=["#d13438", "#f0f0f0", "#107c10"])
        growth_fig.update_traces(
            hovertemplate="%{y}  %{x:.1f}%<extra></extra>",
        )
        style_fig(growth_fig)
        growth_fig.update_xaxes(ticksuffix="%")
        growth_fig.update_coloraxes(showscale=False)

    # --- Seasonality heatmap ---
    heat = df[
        (df["GEO"] == "Canada") &
        (df["Industry"].isin(TOP_INDUSTRIES)) &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].copy()
    heat["Label"] = heat["Industry"].map(SHORT)
    pivot = heat.groupby(["Label", "Month"])["Sales_Actual"].mean().unstack()
    pivot.columns = MONTH_NAMES

    if pivot.empty:
        heat_fig = empty_fig()
    else:
        heat_fig = px.imshow(pivot / 1e9, text_auto=".1f",
                             color_continuous_scale="Blues",
                             labels=dict(color="Avg $B"), aspect="auto")
        heat_fig.update_layout(
            paper_bgcolor=CARD_BG, margin=dict(t=10, b=30, l=10, r=10),
            coloraxis_colorbar=dict(title="$B", thickness=10),
        )

    # --- Adjusted vs Unadjusted ---
    both = df[
        (df["GEO"] == "Canada") &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales")
    ].copy()
    if year:
        both = both[both["Year"] == year]

    if both.empty:
        adj_fig = empty_fig()
    else:
        agg2 = both.groupby(["REF_DATE", "Adjustments"])["Sales_Actual"].sum().reset_index()
        adj_fig = px.line(agg2, x="REF_DATE", y="Sales_Actual", color="Adjustments",
                          color_discrete_map={"Unadjusted": ACCENT,
                                              "Seasonally adjusted": ACCENT2})
        adj_fig.update_traces(line_width=2)
        style_fig(adj_fig, y_fmt="$,.2s")

    return trend_fig, growth_fig, heat_fig, adj_fig


# ══════════════════════════════════════════════════════════════
#  PAGE 3 — GEOGRAPHIC ANALYSIS
# ══════════════════════════════════════════════════════════════
def geo_page():
    row = {"display": "flex", "gap": "16px", "marginBottom": "16px"}
    return html.Div([
        html.Div([
            card([html.H4("Top Provinces by Sales",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="geo-bar", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
            card([html.H4("Regional Contribution (%)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="geo-donut", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
        html.Div([
            card([html.H4("Provincial Sales Trend",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="geo-trend", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "2"}),
            card([html.H4("Provincial Growth Rate 2017 → Latest",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="geo-growth", style={"height": "300px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
    ])


@app.callback(
    Output("geo-bar",    "figure"),
    Output("geo-donut",  "figure"),
    Output("geo-trend",  "figure"),
    Output("geo-growth", "figure"),
    Input("filter-year", "value"),
    Input("filter-adj",  "value"),
)
def cb_geo(year, adj):
    prov = df[
        (df["Geo_Level"] == "Province") &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == adj)
    ].copy()
    if year:
        prov = prov[prov["Year"] == year]

    psum = prov.groupby("GEO")["Sales_Actual"].sum().reset_index()
    psum = psum.sort_values("Sales_Actual", ascending=False)

    if psum.empty:
        return empty_fig(), empty_fig(), empty_fig(), empty_fig()

    # Bar
    bar_fig = px.bar(psum.sort_values("Sales_Actual"),
                     x="Sales_Actual", y="GEO", orientation="h",
                     color="Sales_Actual",
                     color_continuous_scale=[[0, "#c8e4f8"], [1, ACCENT]])
    bar_fig.update_traces(hovertemplate="%{y}  $%{x:,.0f}<extra></extra>")
    style_fig(bar_fig, x_fmt="$,.2s")
    bar_fig.update_coloraxes(showscale=False)

    # Donut
    donut_fig = px.pie(psum, values="Sales_Actual", names="GEO", hole=0.55,
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    donut_fig.update_traces(textinfo="percent",
                            hovertemplate="%{label}  %{percent}<extra></extra>")
    donut_fig.update_layout(paper_bgcolor=CARD_BG,
                            margin=dict(t=10, b=10, l=10, r=10),
                            legend=dict(font=dict(size=9)))

    # Trend
    tall = df[
        (df["Geo_Level"] == "Province") &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == adj)
    ].copy()
    if year:
        tall = tall[tall["Year"] == year]
    tagg = tall.groupby(["REF_DATE", "GEO"])["Sales_Actual"].sum().reset_index()
    trend_fig = px.line(tagg, x="REF_DATE", y="Sales_Actual", color="GEO",
                        color_discrete_sequence=px.colors.qualitative.Set1)
    trend_fig.update_traces(line_width=1.6)
    style_fig(trend_fig, y_fmt="$,.2s")

    # Growth
    gr = df[
        (df["Geo_Level"] == "Province") &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].groupby(["Year", "GEO"])["Sales_Actual"].sum().reset_index()
    fv = gr[gr["Year"] == gr["Year"].min()].set_index("GEO")["Sales_Actual"]
    lv = gr[gr["Year"] == gr["Year"].max()].set_index("GEO")["Sales_Actual"]
    g2 = ((lv - fv) / fv * 100).reset_index()
    g2.columns = ["GEO", "Growth_pct"]
    g2 = g2.sort_values("Growth_pct")

    growth_fig = px.bar(g2, x="Growth_pct", y="GEO", orientation="h",
                        color="Growth_pct",
                        color_continuous_scale=["#d13438", "#f0f0f0", "#107c10"])
    growth_fig.update_traces(hovertemplate="%{y}  %{x:.1f}%<extra></extra>")
    style_fig(growth_fig)
    growth_fig.update_xaxes(ticksuffix="%")
    growth_fig.update_coloraxes(showscale=False)

    return bar_fig, donut_fig, trend_fig, growth_fig


# ══════════════════════════════════════════════════════════════
#  PAGE 4 — FORECASTING
# ══════════════════════════════════════════════════════════════
def forecast_page():
    row = {"display": "flex", "gap": "16px", "marginBottom": "16px"}
    return html.Div([
        html.Div([
            card([html.H4("12-Month Forecast  (Holt-Winters)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="fc-line", style={"height": "340px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "2"}),
            card([html.H4("Monthly Sales Heatmap  (Year × Month)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="fc-heat", style={"height": "340px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
        html.Div([
            card([html.H4("Holiday Sales Spike  (Nov & Dec vs Annual Avg)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="fc-holiday", style={"height": "260px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
            card([html.H4("Seasonal Stability Score by Industry  (lower CV = more stable)",
                          style={"margin": "0 0 8px", "fontSize": "13px", "color": TEXT_DARK}),
                  dcc.Graph(id="fc-stable", style={"height": "260px"},
                            config={"displayModeBar": False})],
                 extra_style={"flex": "1"}),
        ], style=row),
    ])


@app.callback(
    Output("fc-line",    "figure"),
    Output("fc-heat",    "figure"),
    Output("fc-holiday", "figure"),
    Output("fc-stable",  "figure"),
    Input("filter-adj",  "value"),
)
def cb_forecast(adj):
    # National unadjusted series (always use unadjusted for forecasting)
    ts_df = df[
        (df["GEO"] == "Canada") &
        (df["Industry"] == "Retail trade") &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].sort_values("REF_DATE").copy()

    # --- Holt-Winters forecast ---
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        ts = ts_df.set_index("REF_DATE")["Sales_Actual"]
        model    = ExponentialSmoothing(ts, trend="add", seasonal="add",
                                        seasonal_periods=12).fit(optimized=True)
        fitted   = model.fittedvalues
        forecast = model.forecast(12)

        fc_fig = go.Figure()
        fc_fig.add_trace(go.Scatter(
            x=ts.index, y=ts.values / 1e9, name="Historical",
            line=dict(color=ACCENT, width=2),
            hovertemplate="%{x|%b %Y}  $%{y:.2f}B<extra></extra>",
        ))
        fc_fig.add_trace(go.Scatter(
            x=fitted.index, y=fitted.values / 1e9, name="Model Fit",
            line=dict(color="#107c10", width=1.5, dash="dash"),
            hovertemplate="%{x|%b %Y}  $%{y:.2f}B<extra></extra>",
        ))
        fc_fig.add_trace(go.Scatter(
            x=forecast.index, y=forecast.values / 1e9, name="Forecast 12 mo",
            line=dict(color=ACCENT2, width=2.5),
            hovertemplate="%{x|%b %Y}  $%{y:.2f}B<extra></extra>",
        ))
        # ±5% confidence band
        fc_fig.add_trace(go.Scatter(
            x=list(forecast.index) + list(forecast.index[::-1]),
            y=list(forecast.values * 1.05 / 1e9) + list(forecast.values * 0.95 / 1e9)[::-1],
            fill="toself", fillcolor="rgba(230,126,34,0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            name="±5% Band",
        ))
        style_fig(fc_fig)
        fc_fig.update_yaxes(ticksuffix="B")

    except Exception as e:
        # statsmodels not installed — fallback to plain line
        fc_fig = px.line(ts_df, x="REF_DATE", y="Sales_Actual",
                         color_discrete_sequence=[ACCENT],
                         title=f"Historical only (statsmodels error: {e})")
        style_fig(fc_fig, y_fmt="$,.2s")

    # --- Year × Month heatmap ---
    pivot = ts_df.pivot_table(index="Year", columns="Month",
                              values="Sales_Actual", aggfunc="mean")
    pivot.columns = MONTH_NAMES
    heat_fig = px.imshow(pivot / 1e9, text_auto=".0f",
                         color_continuous_scale="YlOrRd",
                         labels=dict(color="Avg $B"), aspect="auto")
    heat_fig.update_layout(paper_bgcolor=CARD_BG,
                           margin=dict(t=10, b=30, l=10, r=10),
                           coloraxis_colorbar=dict(title="$B", thickness=10))

    # --- Holiday spike ---
    hol = ts_df.copy()
    avg_yr = hol.groupby("Year")["Sales_Actual"].mean()
    hol["Annual_Avg"] = hol["Year"].map(avg_yr)
    hol["Spike_pct"]  = (hol["Sales_Actual"] - hol["Annual_Avg"]) / hol["Annual_Avg"] * 100

    # Month order map
    mon_order = {m: i for i, m in enumerate(
        ["January","February","March","April","May","June",
         "July","August","September","October","November","December"])}
    spike_by_month = hol.groupby("Month_Name")["Spike_pct"].mean().reset_index()
    spike_by_month["ord"] = spike_by_month["Month_Name"].map(mon_order)
    spike_by_month = spike_by_month.sort_values("ord")

    hol_fig = px.bar(spike_by_month, x="Month_Name", y="Spike_pct",
                     color="Spike_pct",
                     color_continuous_scale=["#c8e4f8", ACCENT, "#d13438"])
    hol_fig.update_traces(hovertemplate="%{x}  %{y:.1f}%<extra></extra>")
    style_fig(hol_fig)
    hol_fig.update_yaxes(ticksuffix="%")
    hol_fig.update_coloraxes(showscale=False)
    hol_fig.add_hline(y=0, line_dash="dot", line_color=TEXT_GREY)

    # --- Stability score (Coefficient of Variation) ---
    stab = df[
        (df["GEO"] == "Canada") &
        (df["Industry"].isin(TOP_INDUSTRIES)) &
        (df["Sales"] == "Total retail sales") &
        (df["Adjustments"] == "Unadjusted")
    ].groupby("Industry")["Sales_Actual"].agg(["std","mean"]).reset_index()
    stab["CV_pct"] = stab["std"] / stab["mean"] * 100
    stab["Label"]  = stab["Industry"].map(SHORT)
    stab = stab.sort_values("CV_pct")

    stab_fig = px.bar(stab, x="CV_pct", y="Label", orientation="h",
                      color="CV_pct",
                      color_continuous_scale=["#107c10", "#f0f0f0", "#d13438"])
    stab_fig.update_traces(hovertemplate="%{y}  CV: %{x:.1f}%<extra></extra>")
    style_fig(stab_fig)
    stab_fig.update_xaxes(ticksuffix="%")
    stab_fig.update_coloraxes(showscale=False)

    return fc_fig, heat_fig, hol_fig, stab_fig


# ── 9. RUN ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Canadian Retail Dashboard")
    print("  Open → http://127.0.0.1:8050")
    print("=" * 55)
    app.run(debug=True, port=8050)
