
from datetime import date

import streamlit as st


st.set_page_config(
    page_title="FinSight AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    :root {
        --ink: #12263a;
        --muted: #60758a;
        --brand: #176b87;
        --brand-dark: #0e4f66;
        --surface: #ffffff;
        --line: #dce8ed;
    }

    .stApp {
        background: #f5f8fa;
    }

    .block-container {
        max-width: 1240px;
        padding-top: 3.25rem;
        padding-bottom: 3rem;
    }

    .hero {
        margin-bottom: 2rem;
    }

    .eyebrow {
        color: var(--brand);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        margin-bottom: 0.55rem;
        text-transform: uppercase;
    }

    .hero h1 {
        color: var(--ink);
        font-size: clamp(2.25rem, 4vw, 3.7rem);
        letter-spacing: -0.055em;
        line-height: 1;
        margin: 0 0 0.8rem;
    }

    .hero p {
        color: var(--muted);
        font-size: 1.04rem;
        margin: 0;
    }

    [data-testid="stForm"],
    [data-testid="stDataFrame"],
    .summary-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(20, 58, 76, 0.05);
    }

    [data-testid="stForm"] {
        padding: 1.45rem;
    }

    .section-heading {
        color: var(--ink);
        font-size: 1.18rem;
        font-weight: 700;
        margin: 0 0 1rem;
    }

    .section-caption {
        color: var(--muted);
        font-size: 0.9rem;
        margin: -0.55rem 0 1.25rem;
    }

    .summary-card {
        display: flex;
        gap: 1rem;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding: 1rem 1.15rem;
    }

    .summary-label {
        color: var(--muted);
        font-size: 0.78rem;
        margin-bottom: 0.2rem;
    }

    .summary-value {
        color: var(--ink);
        font-size: 1.35rem;
        font-weight: 700;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] button {
        background: var(--brand);
        border: 0;
        border-radius: 10px;
        color: white;
        font-weight: 700;
        min-height: 2.85rem;
        transition: background 120ms ease, transform 120ms ease;
        width: 100%;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: var(--brand-dark);
        color: white;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Personal finance workspace</div>
        <h1>FinSight AI</h1>
        <p>บันทึกทุกความเคลื่อนไหวทางการเงินให้เป็นระเบียบในที่เดียว</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if "transactions" not in st.session_state:
    st.session_state.transactions = []


categories = [
    "เงินเดือน",
    "รายได้เสริม",
    "อาหาร",
    "เดินทาง",
    "ช้อปปิง",
    "ที่พักอาศัย",
    "หนี้สิน",
    "อื่นๆ",
]


left_column, right_column = st.columns([0.9, 1.45], gap="large")

with left_column:
    st.markdown(
        '<div class="section-heading">เพิ่มรายการใหม่</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">กรอกรายละเอียดรายรับหรือรายจ่ายของคุณ</div>',
        unsafe_allow_html=True,
    )

    with st.form("transaction_form", clear_on_submit=True):
        transaction_date = st.date_input(
            "วันที่",
            value=date.today(),
        )

        transaction_type = st.selectbox(
            "ประเภท",
            ["รายรับ", "รายจ่าย"],
        )

        category = st.selectbox(
            "หมวดหมู่",
            categories,
        )

        amount = st.number_input(
            "จำนวนเงิน",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
        )

        details = st.text_input(
            "รายละเอียด",
            placeholder="เช่น ค่าอาหารกลางวัน",
        )

        submitted = st.form_submit_button(
            "บันทึกข้อมูล",
            width="stretch",
        )

    if submitted:
        if amount <= 0:
            st.warning("กรุณาระบุจำนวนเงินที่มากกว่า 0 บาท")
        else:
            st.session_state.transactions.append(
                {
                    "วันที่": transaction_date,
                    "ประเภท": transaction_type,
                    "หมวดหมู่": category,
                    "จำนวนเงิน (บาท)": amount,
                    "รายละเอียด": details.strip() or "-",
                }
            )

            st.success("บันทึกข้อมูลเรียบร้อยแล้ว")


with right_column:
    transaction_count = len(st.session_state.transactions)

    total_income = sum(
        item["จำนวนเงิน (บาท)"]
        for item in st.session_state.transactions
        if item["ประเภท"] == "รายรับ"
    )

    total_expense = sum(
        item["จำนวนเงิน (บาท)"]
        for item in st.session_state.transactions
        if item["ประเภท"] == "รายจ่าย"
    )

    balance = total_income - total_expense

    st.markdown(
        f"""
        <div class="summary-card">
            <div>
                <div class="summary-label">รายการทั้งหมด</div>
                <div class="summary-value">{transaction_count}</div>
            </div>
            <div>
                <div class="summary-label">คงเหลือ</div>
                <div class="summary-value">{balance:,.2f} บาท</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-heading">รายการทางการเงิน</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.transactions:
        st.dataframe(
            st.session_state.transactions,
            width="stretch",
            hide_index=True,
            column_config={
                "วันที่": st.column_config.DateColumn(
                    "วันที่",
                    format="DD/MM/YYYY",
                ),
                "จำนวนเงิน (บาท)": st.column_config.NumberColumn(
                    "จำนวนเงิน (บาท)",
                    format="฿%.2f",
                ),
            },
        )
    else:
        st.info(
            "ยังไม่มีรายการ เริ่มต้นด้วยการบันทึกข้อมูลจากแบบฟอร์มด้านซ้าย"
        )

