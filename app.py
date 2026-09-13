import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. สร้างการเชื่อมต่อไปยัง Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. ดึงข้อมูลจาก Sheets ขึ้นมาแสดงผล
# สมมติว่าใน Google Sheets ตั้งชื่อแผ่นงาน (Tab) ว่า "Transactions"
existing_data = conn.read(worksheet="Transactions", usecols=list(range(5)))
# ลบแถวที่ว่างทิ้งไป
existing_data = existing_data.dropna(how="all")

st.markdown("### 📊 ข้อมูลจาก Google Sheets")
st.dataframe(existing_data)

# 3. ตัวอย่างฟอร์มบันทึกข้อมูลใหม่ลง Sheets
with st.form("add_to_sheets_form"):
    st.markdown("เพิ่มรายการใหม่")
    date = st.date_input("วันที่")
    category = st.selectbox("หมวดหมู่", ["อาหาร", "เดินทาง", "ช้อปปิง"])
    amount = st.number_input("จำนวนเงิน", min_value=0.0)
    submitted = st.form_submit_button("บันทึกข้อมูล")

    if submitted:
        # สร้างชุดข้อมูลใหม่
        new_row = pd.DataFrame([{
            "วันที่": date.strftime("%Y-%m-%d"),
            "หมวดหมู่": category,
            "จำนวนเงิน": amount
        }])
        
        # นำข้อมูลใหม่ไปต่อท้ายข้อมูลเดิม
        updated_data = pd.concat([existing_data, new_row], ignore_index=True)
        
        # อัปเดตข้อมูลทั้งหมดกลับขึ้นไปทับบน Google Sheets
        conn.update(worksheet="Transactions", data=updated_data)
        
        st.success("บันทึกข้อมูลลงฐานข้อมูล Google Sheets สำเร็จ! ข้อมูลจะอยู่ถาวรแล้วครับ")
        st.rerun()
