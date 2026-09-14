import time
from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==========================================
# ⚙️ ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(
    page_title="FinSight AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 🔐 ระบบยืนยันตัวตน (Authentication State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- หน้าจอ Login ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h2 style='text-align: center; color: #176b87;'>🔐 เข้าสู่ระบบ FinSight AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #60758a;'>กรุณากรอกชื่อผู้ใช้งานเพื่อเข้าสู่พื้นที่จัดการการเงินส่วนตัวของคุณ</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("ชื่อผู้ใช้งาน (Username)", placeholder="เช่น naphasarit")
            password_input = st.text_input("รหัสผ่าน (Password)", type="password", placeholder="สำหรับเวอร์ชัน Prototype กรอกอะไรก็ได้ครับ")
            submit_login = st.form_submit_button("เข้าสู่ระบบ / สมัครใช้งาน", width="stretch")

            if submit_login:
                if user_input and password_input:
                    st.session_state.logged_in = True
                    st.session_state.username = user_input.strip()
                    st.rerun()
                else:
                    st.warning("⚠️ กรุณากรอกชื่อผู้ใช้งานและรหัสผ่านให้ครบถ้วน")

    # หยุดการเรนเดอร์หน้าเว็บส่วนอื่นๆ หากยังไม่ Login
    st.stop() 


# ==========================================
# 🗄️ ฟังก์ชันจัดการ Google Sheets (แยกตาม User)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_transactions_from_gsheets():
    """อ่านข้อมูลทั้งหมด แล้วกรองเอาเฉพาะข้อมูลของ User ที่ Login อยู่"""
    try:
        # อ่านข้อมูล 6 คอลัมน์ (รวมถึง Username)
        df = conn.read(worksheet="Transactions", usecols=list(range(6)), ttl=0).dropna(how="all")

        # ตรวจสอบว่าแผ่นงานว่างหรือไม่มีคอลัมน์ Username
        if df.empty or "Username" not in df.columns:
            return []

        # 🔑 กรองเอาเฉพาะข้อมูลที่ Username ตรงกับคนที่ Login
        user_df = df[df["Username"] == st.session_state.username]

        transactions = []
        for _, row in user_df.iterrows():
            try:
                dt = pd.to_datetime(row["วันที่"]).date()
            except:
                dt = date.today()

            transactions.append({
                "วันที่": dt,
                "ประเภท": str(row.get("ประเภท", "")),
                "หมวดหมู่": str(row.get("หมวดหมู่", "")),
                "จำนวนเงิน (บาท)": float(row.get("จำนวนเงิน", 0.0)),
                "รายละเอียด": str(row.get("รายละเอียด", "")),
            })
        return transactions
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return []

def save_transactions_to_gsheets(user_transactions):
    """โหลดข้อมูลทั้งหมด เอาข้อมูลเก่าของ User นี้ออก แล้วต่อท้ายด้วยข้อมูลอัปเดตใหม่"""
    try:
        all_data = conn.read(worksheet="Transactions", usecols=list(range(6)), ttl=0).dropna(how="all")
    except:
        all_data = pd.DataFrame(columns=["วันที่", "ประเภท", "หมวดหมู่", "จำนวนเงิน", "รายละเอียด", "Username"])

    # 1. เอาข้อมูลของคนอื่นเก็บไว้ แต่ลบข้อมูลเดิมของ "ผู้ใช้ปัจจุบัน" ทิ้งไปก่อน
    if not all_data.empty and "Username" in all_data.columns:
        all_data = all_data[all_data["Username"] != st.session_state.username]
    else:
        all_data = pd.DataFrame(columns=["วันที่", "ประเภท", "หมวดหมู่", "จำนวนเงิน", "รายละเอียด", "Username"])

    # 2. นำข้อมูลใหม่ที่ผู้ใช้อัปเดตล่าสุด มาประกอบร่าง (มีใส่ Username ต่อท้าย)
    if user_transactions:
        new_df = pd.DataFrame([{
            "วันที่": t["วันที่"].strftime("%Y-%m-%d"),
            "ประเภท": t["ประเภท"],
            "หมวดหมู่": t["หมวดหมู่"],
            "จำนวนเงิน": t["จำนวนเงิน (บาท)"],
            "รายละเอียด": t["รายละเอียด"],
            "Username": st.session_state.username  # 🔑 ใส่รหัสคนเขียนกำกับไว้
        } for t in user_transactions])

        # 3. นำข้อมูลคนอื่นมารวมกับข้อมูลใหม่ของผู้ใช้ปัจจุบัน
        all_data = pd.concat([all_data, new_df], ignore_index=True)

    # 4. อัปเดตทับลงไปใน Google Sheets ครั้งเดียว
    conn.update(worksheet="Transactions", data=all_data)
    st.cache_data.clear()

# ==========================================
# 🎨 ตกแต่ง CSS
# ==========================================
st.markdown(
    """
    <style>
    :root { --ink: #12263a; --muted: #60758a; --brand: #176b87; --brand-dark: #0e4f66; --surface: #ffffff; --line: #dce8ed; }
    .stApp { background: #f5f8fa; }
    .block-container { max-width: 1240px; padding-top: 3.25rem; padding-bottom: 3rem; }
    .hero { margin-bottom: 2rem; }
    .eyebrow { color: var(--brand); font-size: 0.78rem; font-weight: 700; letter-spacing: 0.16em; margin-bottom: 0.55rem; text-transform: uppercase; }
    .hero h1 { color: var(--ink); font-size: clamp(2.25rem, 4vw, 3.7rem); letter-spacing: -0.055em; line-height: 1; margin: 0 0 0.8rem; }
    .hero p { color: var(--muted); font-size: 1.04rem; margin: 0; }
    [data-testid="stForm"], [data-testid="stDataFrame"], .summary-card { background: var(--surface); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 10px 30px rgba(20, 58, 76, 0.05); }
    [data-testid="stForm"] { padding: 1.45rem; }
    .section-heading { color: var(--ink); font-size: 1.18rem; font-weight: 700; margin: 0 0 1rem; }
    .section-caption { color: var(--muted); font-size: 0.9rem; margin: -0.55rem 0 1.25rem; }
    .summary-card { display: flex; gap: 1rem; justify-content: space-between; margin-bottom: 1rem; padding: 1rem 1.15rem; }
    .summary-label { color: var(--muted); font-size: 0.78rem; margin-bottom: 0.2rem; }
    .summary-value { color: var(--ink); font-size: 1.35rem; font-weight: 700; }
    div.stButton > button, div[data-testid="stFormSubmitButton"] button { background: var(--brand); border: 0; border-radius: 10px; color: white; font-weight: 700; min-height: 2.85rem; transition: background 120ms ease, transform 120ms ease; width: 100%; }
    div[data-testid="stFormSubmitButton"] button:hover { background: var(--brand-dark); color: white; transform: translateY(-1px); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 🏠 โครงสร้างหน้าเว็บหลัก
# ==========================================

# โหลดข้อมูลเฉพาะของคน Login
if "transactions" not in st.session_state:
    st.session_state.transactions = load_transactions_from_gsheets()

col_hero, col_user = st.columns([3, 1])
with col_hero:
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
with col_user:
    st.write(f"👤 ยินดีต้อนรับคุณ **{st.session_state.username}**")
    if st.button("🚪 ออกจากระบบ", key="logout"):
        st.session_state.clear()
        st.rerun()

categories = [
    "เงินเดือน", "รายได้เสริม", "อาหาร", "เดินทาง", 
    "ช้อปปิง", "ค่าสาธารณูปโภค", "ที่พักอาศัย", "หนี้สิน", "อื่นๆ"
]

left_column, right_column = st.columns([0.9, 1.45], gap="large")

# ==========================================
# 📋 ฝั่งซ้าย: ฟอร์มบันทึกข้อมูล
# ==========================================
with left_column:
    st.markdown('<div class="section-heading">เพิ่มรายการใหม่</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">กรอกรายละเอียดรายรับหรือรายจ่ายของคุณ</div>', unsafe_allow_html=True)

    with st.form("transaction_form", clear_on_submit=True):
        transaction_date = st.date_input("วันที่", value=date.today())
        transaction_type = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย"])
        category = st.selectbox("หมวดหมู่", categories)
        amount = st.number_input("จำนวนเงิน", min_value=0.0, value=0.0, step=100.0, format="%.2f")
        details = st.text_input("รายละเอียด", placeholder="เช่น ค่าอาหารกลางวัน")
        submitted = st.form_submit_button("บันทึกข้อมูล", width="stretch")

    if submitted:
        if amount <= 0:
            st.warning("กรุณาระบุจำนวนเงินที่มากกว่า 0 บาท")
        else:
            st.session_state.transactions.append({
                "วันที่": transaction_date,
                "ประเภท": transaction_type,
                "หมวดหมู่": category,
                "จำนวนเงิน (บาท)": amount,
                "รายละเอียด": details.strip() or "-",
            })
            save_transactions_to_gsheets(st.session_state.transactions)
            st.success("บันทึกข้อมูลสำเร็จ!")
            st.rerun()

# ==========================================
# 📊 ฝั่งขวา: แดชบอร์ดแสดงผล
# ==========================================
with right_column:
    transaction_count = len(st.session_state.transactions)
    total_income = sum(item["จำนวนเงิน (บาท)"] for item in st.session_state.transactions if item["ประเภท"] == "รายรับ")
    total_expense = sum(item["จำนวนเงิน (บาท)"] for item in st.session_state.transactions if item["ประเภท"] == "รายจ่าย")
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

    st.markdown('<div class="section-heading">รายการทางการเงิน</div>', unsafe_allow_html=True)

    if st.session_state.transactions:
        st.dataframe(
            st.session_state.transactions,
            width="stretch",
            hide_index=True,
            column_config={
                "วันที่": st.column_config.DateColumn("วันที่", format="DD/MM/YYYY"),
                "จำนวนเงิน (บาท)": st.column_config.NumberColumn("จำนวนเงิน (บาท)", format="฿%.2f"),
            },
        )

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🗑️ ลบรายการทางการเงิน (คลิกที่นี่)"):
            if len(st.session_state.transactions) > 0:
                delete_options = {
                    i: f"[{t['ประเภท']}] {t['วันที่']} - {t['หมวดหมู่']} : {t['จำนวนเงิน (บาท)']:,.2f} บาท ({t['รายละเอียด']})"
                    for i, t in enumerate(st.session_state.transactions)
                }

                selected_idx = st.selectbox(
                    "เลือกรายการที่ต้องการลบ:", 
                    options=list(delete_options.keys()), 
                    format_func=lambda x: delete_options[x]
                )

                if st.button("❌ ยืนยันการลบรายการนี้"):
                    st.session_state.transactions.pop(selected_idx)
                    save_transactions_to_gsheets(st.session_state.transactions)
                    st.rerun() 
            else:
                st.info("ไม่มีรายการให้ลบ")

        expense_rows = [t for t in st.session_state.transactions if t["ประเภท"] == "รายจ่าย"]

        if expense_rows:
            expenses_by_category = {}
            for transaction in expense_rows:
                category_name = transaction["หมวดหมู่"]
                expenses_by_category[category_name] = expenses_by_category.get(category_name, 0) + transaction["จำนวนเงิน (บาท)"]

            chart_data = pd.DataFrame([
                {"category": cat, "amount": amt} 
                for cat, amt in expenses_by_category.items()
            ])

            st.markdown('<div class="section-heading" style="margin-top:2rem;">สัดส่วนรายจ่ายตามหมวดหมู่</div>', unsafe_allow_html=True)

            pie_chart = (
                alt.Chart(chart_data)
                .mark_arc(innerRadius=58, outerRadius=120)
                .encode(
                    theta=alt.Theta("amount:Q", aggregate="sum", title="จำนวนเงิน"),
                    color=alt.Color("category:N", title="หมวดหมู่", legend=alt.Legend(orient="right")),
                    tooltip=[
                        alt.Tooltip("category:N", title="หมวดหมู่"),
                        alt.Tooltip("amount:Q", title="รายจ่าย", format=",.2f"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(pie_chart, use_container_width=True)

            # --- AI Financial Advisor ---
            st.markdown('<div class="section-heading" style="margin-top:2.5rem;">🤖 AI Financial Advisor & พยากรณ์แนวโน้ม</div>', unsafe_allow_html=True)

            if st.button("✨ วิเคราะห์พฤติกรรมการเงินด้วย AI", type="primary", use_container_width=True):
                with st.spinner("AI กำลังวิเคราะห์ข้อมูลของคุณ..."):
                    time.sleep(1.5)

                    highest_cat = max(expenses_by_category, key=expenses_by_category.get)
                    highest_amt = expenses_by_category[highest_cat]

                    savings_rate = (balance / total_income * 100) if total_income > 0 else 0
                    emergency_fund = total_expense * 6

                    unique_days = len(set(t["วันที่"] for t in expense_rows))
                    forecast_30_days = (total_expense / unique_days * 30) if unique_days > 0 else 0

                    st.success(f"✅ วิเคราะห์เสร็จสิ้น! นี่คือคำแนะนำสำหรับคุณ {st.session_state.username}:")

                    st.info(f"💡 **วิเคราะห์รายจ่าย:** พบว่าหมวด **'{highest_cat}'** มีค่าใช้จ่ายสูงสุด ({highest_amt:,.2f} บาท) แนะนำให้ทบทวนงบส่วนนี้")

                    if savings_rate >= 20:
                        st.info(f"💰 **เป้าหมายการออม:** ยอดเยี่ยม! อัตราการออมของคุณคือ **{savings_rate:.1f}%** (ผ่านเกณฑ์ ≥ 20%)")
                    elif savings_rate > 0:
                        st.warning(f"💰 **เป้าหมายการออม:** ปัจจุบันออมได้ **{savings_rate:.1f}%** แนะนำให้ลดรายจ่ายเพื่อเพิ่มเงินออมให้ถึง 20%")
                    else:
                        st.error(f"💰 **เป้าหมายการออม:** คุณไม่มีเงินออมในระบบ AI แนะนำให้ลดรายจ่ายหมวด '{highest_cat}' ด่วน")

                    st.info(f"🛡️ **ความมั่นคง:** แนะนำให้สร้างกองทุนฉุกเฉินครอบคลุม 6 เดือน (เป้าหมาย: **{emergency_fund:,.2f} บาท**)")

                    if forecast_30_days > 0:
                        st.info(f"📈 **พยากรณ์ล่วงหน้า:** จากพฤติกรรม {unique_days} วันที่ผ่านมา คาดการณ์ว่ารายจ่าย 30 วันข้างหน้าจะอยู่ที่ **{forecast_30_days:,.2f} บาท**")
    else:
        st.info("ยังไม่มีรายการ เริ่มต้นด้วยการบันทึกข้อมูลจากแบบฟอร์มด้านซ้าย")
