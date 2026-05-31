"""
app.py — MoneyMoves: Wealth Path Simulator

A three-path interactive financial simulator showing the long-term impact
of traditional savings, stock market investing, and an optimised strategy.

Built by Dorcas Aina — github.com/dorcas-aina-analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MoneyMoves — Wealth Path Simulator",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour palette ─────────────────────────────────────────────────────────────

OLIVE        = "#556B2F"
OLIVE_LIGHT  = "#7A8C4A"
PINK         = "#E8758A"
PINK_LIGHT   = "#F4A7B9"
GOLD         = "#8B6914"
DARK_TEXT    = "#2C1A0E"
MID_TEXT     = "#5C4033"
CREAM        = "#FDF6F0"
LINEN        = "#F0E6D8"
BORDER       = "#C9B89A"
CHART_GRID   = "#DDD0BE"
RED          = "#C0392B"
GREEN_SIGNAL = "#2D6A4F"

# ── Metric font size override ──────────────────────────────────────────────────
# Reduces Streamlit's default large metric value font to 1.5rem

st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── UK reference data ──────────────────────────────────────────────────────────

UK_AVERAGES = {
    "median_salary":        35000,
    "average_savings_rate": 0.08,
    "isa_allowance":        20000,
    "state_pension_weekly": 221.20,
    "inflation_rate":       0.025,
}

RETURN_ASSUMPTIONS = {
    "savings_account": 0.045,
    "stocks_isa":      0.07,
    "optimised":       0.08,
}

PATH_DESCRIPTIONS = {
    "Path 1: Traditional Savings":  "Your money sits in a savings account earning interest. Safe but slow — inflation quietly eats into your real returns over time.",
    "Path 2: Stocks & Shares ISA":  "Same amount invested in a global index fund, completely tax-free. Your money works harder because markets grow faster than savings rates.",
    "Path 3: Optimised Strategy":   "Emergency fund first, then ISA wrapper, then diversified investments. Not more money — the same money, structured more intelligently.",
}

# ── Helper functions ───────────────────────────────────────────────────────────

def format_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"£{value/1_000_000:.2f}m"
    elif value >= 1_000:
        return f"£{value:,.0f}"
    else:
        return f"£{value:.2f}"


def calculate_path(
    monthly_amount: float,
    annual_return: float,
    years: int,
    inflation_rate: float = 0.025,
    lump_sum: float = 0.0
) -> pd.DataFrame:
    monthly_rate = annual_return / 12
    data = []
    balance = lump_sum
    total_contributed = lump_sum

    for year in range(1, years + 1):
        for month in range(12):
            balance = balance * (1 + monthly_rate) + monthly_amount
            total_contributed += monthly_amount
        real_value = balance / ((1 + inflation_rate) ** year)
        growth = balance - total_contributed
        data.append({
            "Year":              year,
            "Nominal Value":     round(balance, 2),
            "Real Value":        round(real_value, 2),
            "Total Contributed": round(total_contributed, 2),
            "Growth":            round(max(growth, 0), 2),
        })
    return pd.DataFrame(data)


def calculate_retirement_income(final_pot: float) -> dict:
    withdrawal_rate = 0.035
    annual_withdrawal = final_pot * withdrawal_rate
    state_pension_annual = UK_AVERAGES["state_pension_weekly"] * 52
    total_annual = annual_withdrawal + state_pension_annual
    return {
        "annual_from_pot":  round(annual_withdrawal, 2),
        "monthly_from_pot": round(annual_withdrawal / 12, 2),
        "state_pension":    round(state_pension_annual, 2),
        "total_annual":     round(total_annual, 2),
        "total_monthly":    round(total_annual / 12, 2),
    }


def required_monthly(target: float, annual_return: float,
                     years: int, lump_sum: float = 0) -> float:
    monthly_rate = annual_return / 12
    n = years * 12
    if monthly_rate == 0:
        return max(0, (target - lump_sum) / n)
    lump_future = lump_sum * ((1 + monthly_rate) ** n)
    remaining_target = target - lump_future
    if remaining_target <= 0:
        return 0.0
    return max(0, remaining_target * monthly_rate / (((1 + monthly_rate) ** n) - 1))


def years_to_reach(target: float, monthly_amount: float,
                   annual_return: float, lump_sum: float = 0) -> float:
    if monthly_amount <= 0:
        return 999
    monthly_rate = annual_return / 12
    balance = lump_sum
    count = 0
    for _ in range(100 * 12):
        balance = balance * (1 + monthly_rate) + monthly_amount
        count += 1
        if balance >= target:
            return count / 12
    return 999


def traffic_light(value, low, high):
    if value >= high:
        return "🟢"
    elif value >= low:
        return "🟡"
    else:
        return "🔴"


def section_header(text: str, colour: str = OLIVE):
    st.markdown(
        f"<h2 style='color:{colour}; font-size:1.5rem; "
        f"font-weight:700; margin:1.5rem 0 0.5rem 0;'>{text}</h2>",
        unsafe_allow_html=True,
    )


def sub_label(text: str):
    st.markdown(
        f"<p style='color:{MID_TEXT}; font-size:0.85rem; "
        f"margin:0 0 1rem 0;'>{text}</p>",
        unsafe_allow_html=True,
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"<p style='color:{OLIVE}; font-size:11px; font-weight:700; "
        f"letter-spacing:1px; margin-bottom:8px;'>ABOUT YOU</p>",
        unsafe_allow_html=True,
    )

    age = st.slider("Current age", min_value=18, max_value=60, value=28, step=1)
    retirement_age = st.slider("Target retirement age", min_value=50, max_value=75, value=67, step=1)
    years = retirement_age - age

    annual_salary = st.number_input(
        "Annual salary (£)", min_value=10000, max_value=500000, value=35000, step=1000
    )
    monthly_take_home = st.number_input(
        "Monthly take-home pay (£)", min_value=500, max_value=20000, value=2200, step=50,
        help="After tax and National Insurance"
    )

    st.divider()

    st.markdown(
        f"<p style='color:{OLIVE}; font-size:11px; font-weight:700; "
        f"letter-spacing:1px; margin-bottom:8px;'>MONTHLY SPENDING</p>",
        unsafe_allow_html=True,
    )

    expenses_rent      = st.number_input("Rent / mortgage & bills (£)", min_value=0, max_value=5000, value=900,  step=25)
    expenses_food      = st.number_input("Food & groceries (£)",         min_value=0, max_value=2000, value=250,  step=25)
    expenses_transport = st.number_input("Transport (£)",                 min_value=0, max_value=1000, value=100,  step=10)
    expenses_enjoyment = st.number_input("Enjoyment & lifestyle (£)",     min_value=0, max_value=2000, value=150,  step=25,
                                         help="Eating out, subscriptions, hobbies, clothing")

    total_expenses = expenses_rent + expenses_food + expenses_transport + expenses_enjoyment

    st.divider()

    st.markdown(
        f"<p style='color:{OLIVE}; font-size:11px; font-weight:700; "
        f"letter-spacing:1px; margin-bottom:8px;'>SAVING & INVESTING</p>",
        unsafe_allow_html=True,
    )

    current_savings    = st.number_input("Current savings (£)",                    min_value=0, max_value=500000, value=5000, step=500)
    monthly_emergency  = st.number_input("Monthly emergency fund contribution (£)", min_value=0, max_value=2000,  value=100,  step=25,
                                         help="Into an easy-access savings account before investing")
    monthly_investment = st.number_input("Monthly investment amount (£)",           min_value=0, max_value=10000, value=200,  step=25,
                                         help="How much you want to invest each month — your choice")

    total_outgoings = total_expenses + monthly_emergency + monthly_investment
    remaining       = monthly_take_home - total_outgoings
    remaining_col   = GREEN_SIGNAL if remaining >= 0 else RED
    remaining_label = "Left over" if remaining >= 0 else "Overspending by"

    st.divider()

    st.markdown(
        f"<p style='color:{OLIVE}; font-size:11px; font-weight:700; "
        f"letter-spacing:1px; margin-bottom:8px;'>ASSUMPTIONS</p>",
        unsafe_allow_html=True,
    )

    inflation_rate = st.slider("Inflation rate (%)", min_value=1.0, max_value=6.0, value=2.5, step=0.5) / 100

    st.divider()

    st.markdown(
        f"""
        <div style='background:{LINEN}; border-left:4px solid {OLIVE};
        border-radius:6px; padding:12px 14px; font-size:12px; line-height:2;'>
            <p style='margin:0; color:{DARK_TEXT};'>
                <span style='color:{OLIVE}; font-weight:700;'>Total spending:</span>
                {format_currency(total_expenses)}/mo
            </p>
            <p style='margin:0; color:{DARK_TEXT};'>
                <span style='color:{OLIVE}; font-weight:700;'>Emergency fund:</span>
                {format_currency(monthly_emergency)}/mo
            </p>
            <p style='margin:0; color:{DARK_TEXT};'>
                <span style='color:{OLIVE}; font-weight:700;'>Investing:</span>
                {format_currency(monthly_investment)}/mo
            </p>
            <p style='margin:0;'>
                <span style='color:{OLIVE}; font-weight:700;'>{remaining_label}:</span>
                <span style='color:{remaining_col}; font-weight:700;'>
                {format_currency(abs(remaining))}</span>
            </p>
            <p style='margin:0; color:{DARK_TEXT};'>
                <span style='color:{OLIVE}; font-weight:700;'>Years to retirement:</span>
                {years}
            </p>
            <p style='margin:6px 0 0 0; color:{DARK_TEXT};'>
                <span style='color:{OLIVE}; font-weight:700;'>Built by:</span>
                <a href='https://dorcasainaa-dotcom.github.io'
                style='color:{PINK}; font-weight:700;'>Dorcas Aina</a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main page ──────────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div style='padding:1.5rem 0 0.5rem 0; border-bottom:3px solid {OLIVE};
    margin-bottom:1.5rem;'>
        <h1 style='color:{OLIVE}; margin:0; font-size:2.4rem; font-weight:900;'>
            💸 Your Wealth, Your Choice
        </h1>
        <p style='color:{DARK_TEXT}; font-size:1.05rem; margin:8px 0 0 0;
        font-weight:500;'>
            See exactly what your financial decisions look like over the next
            <b style='color:{OLIVE};'>{years} years</b>.
            Three paths. One choice.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Validation ─────────────────────────────────────────────────────────────────

if monthly_investment <= 0:
    st.warning("Set a monthly investment amount in the sidebar to see your wealth paths.")
    st.stop()

if remaining < -50:
    st.error(
        f"Your total outgoings exceed your take-home pay by "
        f"{format_currency(abs(remaining))} per month. "
        "Adjust your spending or investment amount."
    )
    st.stop()

# ── Calculate paths ────────────────────────────────────────────────────────────

path1 = calculate_path(monthly_investment, RETURN_ASSUMPTIONS["savings_account"], years, inflation_rate, current_savings)
path2 = calculate_path(monthly_investment, RETURN_ASSUMPTIONS["stocks_isa"],      years, inflation_rate, current_savings)
path3 = calculate_path(monthly_investment, RETURN_ASSUMPTIONS["optimised"],       years, inflation_rate, current_savings)

final1 = path1["Nominal Value"].iloc[-1]
final2 = path2["Nominal Value"].iloc[-1]
final3 = path3["Nominal Value"].iloc[-1]

# ── Headline metric cards ──────────────────────────────────────────────────────

st.markdown(
    f"<p style='color:{OLIVE}; font-size:11px; font-weight:700; "
    f"letter-spacing:1px;'>YOUR THREE WEALTH PATHS AT RETIREMENT</p>",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("You are investing monthly", format_currency(monthly_investment),
              delta=f"UK avg £{UK_AVERAGES['median_salary']/12 * UK_AVERAGES['average_savings_rate']:,.0f}/mo")
with col2:
    st.metric("Path 1: Traditional Savings", format_currency(final1))
with col3:
    st.metric("Path 2: Stocks & Shares ISA", format_currency(final2),
              delta=f"+{format_currency(final2 - final1)} vs savings")
with col4:
    st.metric("Path 3: Optimised Strategy",  format_currency(final3),
              delta=f"+{format_currency(final3 - final1)} vs savings")

st.divider()

# ── Main wealth chart ──────────────────────────────────────────────────────────

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=path1["Year"], y=path1["Nominal Value"], mode="lines",
    name="Traditional Savings",
    line=dict(color=BORDER, width=2, dash="dash"),
    hovertemplate="Year %{x}<br>%{y:£,.0f}<extra>Traditional Savings</extra>"
))
fig.add_trace(go.Scatter(
    x=path2["Year"], y=path2["Nominal Value"], mode="lines",
    name="Stocks & Shares ISA",
    line=dict(color=PINK, width=2.5),
    hovertemplate="Year %{x}<br>%{y:£,.0f}<extra>Stocks & Shares ISA</extra>"
))
fig.add_trace(go.Scatter(
    x=path3["Year"], y=path3["Nominal Value"], mode="lines",
    name="Optimised Strategy",
    line=dict(color=OLIVE, width=3),
    hovertemplate="Year %{x}<br>%{y:£,.0f}<extra>Optimised Strategy</extra>"
))
fig.add_trace(go.Scatter(
    x=pd.concat([path1["Year"], path3["Year"].iloc[::-1]]),
    y=pd.concat([path1["Nominal Value"], path3["Nominal Value"].iloc[::-1]]),
    fill="toself", fillcolor="rgba(85, 107, 47, 0.08)",
    line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
))

fig.update_layout(
    title=dict(
        text=f"Wealth Growth Over {years} Years - Three Paths",
        font=dict(color=OLIVE, size=16, family="Arial"),
        x=0.01
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=DARK_TEXT, family="Arial"),
    xaxis=dict(
        title=dict(text="Years from now", font=dict(color=DARK_TEXT)),
        gridcolor=CHART_GRID, showgrid=True, zeroline=False,
        tickfont=dict(color=DARK_TEXT),
    ),
    yaxis=dict(
        title=dict(text="Portfolio Value", font=dict(color=DARK_TEXT)),
        gridcolor=CHART_GRID, showgrid=True, zeroline=False,
        tickprefix="£", tickformat=",.0f",
        tickfont=dict(color=DARK_TEXT),
    ),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=DARK_TEXT)),
    margin=dict(l=60, r=20, t=60, b=60),
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Return assumptions explainer ───────────────────────────────────────────────

with st.expander("📖 How are these returns calculated? And can I change them?"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""<div style='background:{LINEN}; border-top:3px solid {BORDER};
            border-radius:6px; padding:1rem;'>
            <h4 style='color:{MID_TEXT}; margin:0 0 8px 0;'>Path 1: Savings Account</h4>
            <p style='color:{OLIVE}; font-size:1.4rem; font-weight:900; margin:0;'>4.5% per year</p>
            <p style='color:{DARK_TEXT}; font-size:12px; margin:8px 0 0 0; line-height:1.6;'>
            Based on current UK high-yield savings account rates (2024). This changes with Bank of
            England base rate decisions. In 2021 this was closer to 0.1%. In 2023 it peaked at 5.2%.
            We use 4.5% as a realistic mid-term average.</p></div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div style='background:{LINEN}; border-top:3px solid {PINK};
            border-radius:6px; padding:1rem;'>
            <h4 style='color:{PINK}; margin:0 0 8px 0;'>Path 2: Stocks & Shares ISA</h4>
            <p style='color:{OLIVE}; font-size:1.4rem; font-weight:900; margin:0;'>7% per year</p>
            <p style='color:{DARK_TEXT}; font-size:12px; margin:8px 0 0 0; line-height:1.6;'>
            The global stock market has returned approximately 9-10% annually before inflation
            over the past 100 years. After adjusting for 2-3% inflation, the real return is around 7%.
            This is why index fund investing beats savings accounts so dramatically over long periods.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div style='background:{LINEN}; border-top:3px solid {OLIVE};
            border-radius:6px; padding:1rem;'>
            <h4 style='color:{OLIVE}; margin:0 0 8px 0;'>Path 3: Optimised Strategy</h4>
            <p style='color:{OLIVE}; font-size:1.4rem; font-weight:900; margin:0;'>8% per year</p>
            <p style='color:{DARK_TEXT}; font-size:12px; margin:8px 0 0 0; line-height:1.6;'>
            Slightly higher than Path 2 because the optimised strategy uses an ISA wrapper
            (tax-free growth), avoids platform fees where possible, and includes a mix of equities
            rebalanced over time. The 1% difference compounds to a significant gap over 30+ years.</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div style='background:{LINEN}; border-left:4px solid {GOLD};
        border-radius:6px; padding:1rem; margin-top:1rem;'>
        <h4 style='color:{GOLD}; margin:0 0 8px 0;'>What about 10%, 12%, or more?</h4>
        <p style='color:{DARK_TEXT}; font-size:13px; margin:0; line-height:1.6;'>
        You may have seen claims of 10-12% annual returns — these are often quoted as the
        S&P 500 nominal (before inflation) historical average. They are real but come with
        caveats: they assume US-only investment, reinvested dividends, no selling during crashes,
        and no fees or taxes. A globally diversified ISA investor is more likely to achieve
        7-9% over the long term. We use conservative estimates so you are not disappointed —
        any outperformance is a bonus.</p></div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<p style='color:{OLIVE}; font-weight:700; font-size:13px; margin-top:1rem;'>"
        f"Want to use your own return assumptions?</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        custom_r1 = st.slider("Path 1 return (%)", 1.0, 8.0,  RETURN_ASSUMPTIONS["savings_account"] * 100, 0.5) / 100
    with c2:
        custom_r2 = st.slider("Path 2 return (%)", 3.0, 15.0, RETURN_ASSUMPTIONS["stocks_isa"] * 100, 0.5) / 100
    with c3:
        custom_r3 = st.slider("Path 3 return (%)", 3.0, 15.0, RETURN_ASSUMPTIONS["optimised"] * 100, 0.5) / 100

    if st.button("Apply custom returns", type="primary"):
        path1  = calculate_path(monthly_investment, custom_r1, years, inflation_rate, current_savings)
        path2  = calculate_path(monthly_investment, custom_r2, years, inflation_rate, current_savings)
        path3  = calculate_path(monthly_investment, custom_r3, years, inflation_rate, current_savings)
        final1 = path1["Nominal Value"].iloc[-1]
        final2 = path2["Nominal Value"].iloc[-1]
        final3 = path3["Nominal Value"].iloc[-1]
        st.success(f"Applied: Path 1 = {custom_r1*100:.1f}%, Path 2 = {custom_r2*100:.1f}%, Path 3 = {custom_r3*100:.1f}%")

# ── The gap callout ────────────────────────────────────────────────────────────

st.divider()

gap = final3 - final1
gap_monthly = gap / (years * 12)

st.markdown(
    f"""
    <div style='background:{LINEN}; border-left:5px solid {PINK};
    padding:1.2rem 1.5rem; border-radius:6px; margin-bottom:1.5rem;'>
        <p style='color:{MID_TEXT}; font-size:11px; font-weight:700;
        letter-spacing:1px; margin:0 0 4px 0;'>THE COST OF DOING NOTHING DIFFERENT</p>
        <h2 style='color:{PINK}; margin:0; font-size:2rem; font-weight:900;'>
        {format_currency(gap)}</h2>
        <p style='color:{DARK_TEXT}; margin:6px 0 0 0; font-size:14px;'>
        That is the difference between keeping your money in a savings account
        and using an optimised strategy — with the exact same
        <b>{format_currency(monthly_investment)}/month</b>.
        Equivalent to <b>{format_currency(gap_monthly)}</b> every month
        for {years} years, left on the table.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Work backwards from your goal ─────────────────────────────────────────────

section_header("Work Backwards From Your Goal")
sub_label("Set your target retirement pot and see exactly what you need to do to get there.")

goal_col1, goal_col2 = st.columns([1, 2])

with goal_col1:
    st.markdown(
        f"<p style='color:{OLIVE}; font-size:12px; font-weight:700; "
        f"margin-bottom:8px;'>YOUR RETIREMENT TARGET</p>",
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4 = st.columns(4)
    preset_target = None
    with p1:
        if st.button("£250k"): preset_target = 250000
    with p2:
        if st.button("£500k"): preset_target = 500000
    with p3:
        if st.button("£1m"):   preset_target = 1000000
    with p4:
        if st.button("£2m"):   preset_target = 2000000

    target_pot = st.number_input(
        "Or enter your own target (£)", min_value=10000, max_value=10000000,
        value=preset_target if preset_target else 1000000, step=10000,
        help="The total pot you want to have by retirement"
    )
    target_years = st.number_input(
        "Years to achieve this", min_value=1, max_value=50, value=years, step=1,
        help="Adjust if different from your retirement target age"
    )

    st.markdown(
        f"""
        <div style='background:{LINEN}; border-left:4px solid {GOLD};
        border-radius:6px; padding:0.8rem 1rem; margin-top:1rem;'>
            <p style='color:{GOLD}; font-weight:700; font-size:13px; margin:0;'>
            Target: {format_currency(target_pot)}</p>
            <p style='color:{DARK_TEXT}; font-size:12px; margin:4px 0 0 0;'>
            in {target_years} years</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with goal_col2:
    req1 = required_monthly(target_pot, RETURN_ASSUMPTIONS["savings_account"], target_years, current_savings)
    req2 = required_monthly(target_pot, RETURN_ASSUMPTIONS["stocks_isa"],      target_years, current_savings)
    req3 = required_monthly(target_pot, RETURN_ASSUMPTIONS["optimised"],       target_years, current_savings)

    yrs1 = years_to_reach(target_pot, monthly_investment, RETURN_ASSUMPTIONS["savings_account"], current_savings)
    yrs2 = years_to_reach(target_pot, monthly_investment, RETURN_ASSUMPTIONS["stocks_isa"],      current_savings)
    yrs3 = years_to_reach(target_pot, monthly_investment, RETURN_ASSUMPTIONS["optimised"],       current_savings)

    def goal_status(req):
        shortfall = req - monthly_investment
        if shortfall <= 0:
            return "🟢", GREEN_SIGNAL, "On track"
        elif shortfall <= 100:
            return "🟡", GOLD, f"Need +{format_currency(shortfall)}/mo"
        else:
            return "🔴", RED, f"Need +{format_currency(shortfall)}/mo"

    e1, c1, l1 = goal_status(req1)
    e2, c2, l2 = goal_status(req2)
    e3, c3, l3 = goal_status(req3)

    st.markdown(
        f"""
        <table style='width:100%; border-collapse:collapse;
        font-size:13px; color:{DARK_TEXT};'>
            <thead>
                <tr style='background:{OLIVE}; color:white;'>
                    <th style='padding:10px 12px; text-align:left;'>Path</th>
                    <th style='padding:10px 12px; text-align:right;'>Monthly needed</th>
                    <th style='padding:10px 12px; text-align:right;'>Status</th>
                    <th style='padding:10px 12px; text-align:right;'>Years at current rate</th>
                    <th style='padding:10px 12px; text-align:center;'></th>
                </tr>
            </thead>
            <tbody>
                <tr style='background:{LINEN};'>
                    <td style='padding:10px 12px; font-weight:700; color:{MID_TEXT};'>Traditional Savings</td>
                    <td style='padding:10px 12px; text-align:right;'>{format_currency(req1)}/mo</td>
                    <td style='padding:10px 12px; text-align:right; color:{c1}; font-weight:700;'>{l1}</td>
                    <td style='padding:10px 12px; text-align:right;'>{"Never" if yrs1==999 else f"{yrs1:.1f} yrs"}</td>
                    <td style='padding:10px 12px; text-align:center; font-size:1.2rem;'>{e1}</td>
                </tr>
                <tr style='background:white;'>
                    <td style='padding:10px 12px; font-weight:700; color:{PINK};'>Stocks & Shares ISA</td>
                    <td style='padding:10px 12px; text-align:right;'>{format_currency(req2)}/mo</td>
                    <td style='padding:10px 12px; text-align:right; color:{c2}; font-weight:700;'>{l2}</td>
                    <td style='padding:10px 12px; text-align:right;'>{"Never" if yrs2==999 else f"{yrs2:.1f} yrs"}</td>
                    <td style='padding:10px 12px; text-align:center; font-size:1.2rem;'>{e2}</td>
                </tr>
                <tr style='background:{LINEN};'>
                    <td style='padding:10px 12px; font-weight:700; color:{OLIVE};'>Optimised Strategy</td>
                    <td style='padding:10px 12px; text-align:right;'>{format_currency(req3)}/mo</td>
                    <td style='padding:10px 12px; text-align:right; color:{c3}; font-weight:700;'>{l3}</td>
                    <td style='padding:10px 12px; text-align:right;'>{"Never" if yrs3==999 else f"{yrs3:.1f} yrs"}</td>
                    <td style='padding:10px 12px; text-align:center; font-size:1.2rem;'>{e3}</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    saving = req1 - req3
    if saving > 0:
        st.markdown(
            f"""
            <div style='background:{LINEN}; border-left:5px solid {OLIVE};
            border-radius:6px; padding:1rem; margin-top:1rem;'>
                <p style='color:{DARK_TEXT}; font-size:13px; margin:0; line-height:1.6;'>
                To reach <b style='color:{OLIVE};'>{format_currency(target_pot)}</b>
                in {target_years} years, the Optimised Strategy needs
                <b style='color:{OLIVE};'>{format_currency(saving)}/month less</b>
                than Traditional Savings. Same goal. Less effort. Smarter structure.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── What does retirement actually look like (expander) ────────────────────────

with st.expander("💰 What does this pot mean in retirement?"):
    sub_label("Based on a 3.5% sustainable withdrawal rate — your pot keeps growing while you draw from it.")

    ret1 = calculate_retirement_income(final1)
    ret2 = calculate_retirement_income(final2)
    ret3 = calculate_retirement_income(final3)

    rc1, rc2, rc3 = st.columns(3)

    def income_card(col, title, colour, ret):
        with col:
            st.markdown(
                f"<h4 style='color:{colour}; font-weight:700; margin-bottom:8px;'>{title}</h4>",
                unsafe_allow_html=True,
            )
            st.metric("Monthly income from pot",    format_currency(ret["monthly_from_pot"]))
            st.metric("State pension (if eligible)", format_currency(ret["state_pension"] / 12))
            st.metric("Total monthly income",        format_currency(ret["total_monthly"]))

    income_card(rc1, "Traditional Savings", MID_TEXT, ret1)
    income_card(rc2, "Stocks & Shares ISA", PINK,     ret2)
    income_card(rc3, "Optimised Strategy",  OLIVE,    ret3)

st.divider()

# ── Path by path breakdown ─────────────────────────────────────────────────────

section_header("Path by Path Breakdown")
sub_label("Same monthly investment. Very different outcomes.")

col1, col2, col3 = st.columns(3)

def path_card(col, title, colour, path_df, final_pot, return_pct):
    with col:
        st.markdown(
            f"<h3 style='color:{colour}; font-size:1.1rem; font-weight:700; margin-bottom:4px;'>"
            f"{title}</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color:{MID_TEXT}; font-size:12px; margin:0 0 12px 0; "
            f"line-height:1.5;'>{PATH_DESCRIPTIONS[title]}</p>",
            unsafe_allow_html=True,
        )
        st.metric("Final pot",                       format_currency(final_pot))
        st.metric("Real value (inflation-adjusted)",  format_currency(path_df["Real Value"].iloc[-1]))
        st.metric("Total contributed",                format_currency(path_df["Total Contributed"].iloc[-1]))
        st.metric("Growth from returns",              format_currency(path_df["Growth"].iloc[-1]))
        st.metric("Annual return assumed",            return_pct)

path_card(col1, "Path 1: Traditional Savings", BORDER, path1, final1, "4.5%")
path_card(col2, "Path 2: Stocks & Shares ISA", PINK,   path2, final2, "7.0%")
path_card(col3, "Path 3: Optimised Strategy",  OLIVE,  path3, final3, "8.0%")

st.divider()

# ── Emergency fund check ───────────────────────────────────────────────────────

section_header("Before You Invest: Emergency Fund Check")
sub_label("The foundation of smart money management. No exceptions.")

emergency_target = total_expenses * 6
ef_status = traffic_light(current_savings, emergency_target * 0.5, emergency_target)
months_to_ef = max(0, (emergency_target - current_savings) / monthly_emergency) if monthly_emergency > 0 else 0

ef1, ef2 = st.columns(2)

with ef1:
    st.metric("Recommended emergency fund (6 months)", format_currency(emergency_target))
    st.metric("Your current savings",                  format_currency(current_savings))
    advice = (
        "You have a solid emergency fund. Start investing your surplus."
        if current_savings >= emergency_target
        else f"Build your emergency fund first. Target: {format_currency(emergency_target)} in an easy-access account."
    )
    st.markdown(
        f"<p style='color:{DARK_TEXT}; font-size:14px;'>{ef_status} {advice}</p>",
        unsafe_allow_html=True,
    )

with ef2:
    st.metric("Months to reach target",
              f"{months_to_ef:.0f} months" if months_to_ef > 0 else "Already there")
    st.metric("Monthly emergency fund contribution", format_currency(monthly_emergency))

st.divider()

# ── Savings boost cards ────────────────────────────────────────────────────────

section_header("What If I Invested a Little More?")
sub_label("Small increases compound dramatically over time. All figures use the Optimised Strategy.")

bc1, bc2, bc3, bc4 = st.columns(4)
boost_cols = [bc1, bc2, bc3, bc4]

for i, extra in enumerate([50, 100, 200, 500]):
    boosted = calculate_path(
        monthly_investment + extra, RETURN_ASSUMPTIONS["optimised"],
        years, inflation_rate, current_savings
    )
    final_b  = boosted["Nominal Value"].iloc[-1]
    extra_g  = final_b - final3
    multiple = (extra_g / (extra * 12 * years)) if years > 0 else 0

    with boost_cols[i]:
        st.markdown(
            f"""
            <div style='background:{LINEN}; border-top:4px solid {PINK};
            border-radius:8px; padding:1rem; text-align:center;'>
                <p style='color:{PINK}; font-size:1rem; font-weight:900;
                margin:0;'>+£{extra}/mo</p>
                <p style='color:{OLIVE}; font-size:1.3rem; font-weight:900;
                margin:6px 0 2px 0;'>{format_currency(final_b)}</p>
                <p style='color:{DARK_TEXT}; font-size:11px; margin:0;'>
                final pot</p>
                <hr style='border:none; border-top:1px solid {BORDER};
                margin:8px 0;'>
                <p style='color:{GREEN_SIGNAL}; font-size:12px; font-weight:700;
                margin:0;'>+{format_currency(extra_g)} extra</p>
                <p style='color:{GOLD}; font-size:11px; margin:4px 0 0 0;'>
                {multiple:.1f}x return on extra contributions</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Smart money moves ──────────────────────────────────────────────────────────

section_header("The Smart Money Moves")

sm1, sm2 = st.columns(2)

def tip_card(col, title, body, colour):
    with col:
        st.markdown(
            f"""
            <div style='background:{LINEN}; border-top:4px solid {colour};
            border-radius:6px; padding:1.2rem; margin-bottom:1rem;'>
                <h4 style='color:{colour}; margin:0 0 8px 0; font-weight:700;'>
                {title}</h4>
                <p style='color:{DARK_TEXT}; font-size:13px; margin:0; line-height:1.6;'>
                {body}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

tip_card(sm1, "Step 1: Build your emergency fund",
         "Before investing a single pound, keep 3-6 months of essential expenses in an "
         "easy-access savings account. This stops you from selling investments at a loss "
         "when life happens.", PINK)

tip_card(sm1, "Step 2: Max your ISA allowance",
         "You can invest up to £20,000 per year in a Stocks and Shares ISA. All growth "
         "and withdrawals are completely tax-free. This is the single most powerful "
         "financial tool available to UK residents.", PINK)

tip_card(sm2, "Step 3: Invest in global index funds",
         "Rather than picking individual stocks, a global index fund gives you exposure "
         "to thousands of companies across 50+ countries. Low fees, high diversification, "
         "and historically the best long-term returns for most investors.", OLIVE)

tip_card(sm2, "Step 4: Stay invested when markets fall",
         "When markets drop, most people panic and sell — locking in losses. Investors who "
         "stayed invested through every market crash since 1900 dramatically outperformed "
         "those who tried to time the market. Stay consistent.", OLIVE)

st.divider()

# ── Disclaimer ─────────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <p style='color:{MID_TEXT}; font-size:11px; line-height:1.6;'>
    This tool is for educational and illustrative purposes only and does not constitute
    financial advice. Returns shown are based on historical averages and are not guaranteed.
    All investments carry risk and the value of your investments can go down as well as up.
    For personalised advice, consult a qualified financial adviser regulated by the FCA.
    Built by <a href='https://dorcasainaa-dotcom.github.io' style='color:{PINK};'>Dorcas Aina</a>.
    </p>
    """,
    unsafe_allow_html=True,
)
