import os
import sqlite3
import calendar
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# إعدادات الصفحة الأساسية وتصميم الواجهة باسم التطبيق My Budget
st.set_page_config(page_title="تطبيق My Budget - رفيقك المالي الأبدي 21.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) وتنسيق شبكة التقويم الاحترافي وجدول التراجع
st.markdown("""
    <style>
    .block-container { text-align: right; direction: rtl; padding-top: 1rem !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; height: 45px; }
    [data-testid="stSidebar"] { text-align: right; direction: rtl; background-color: #1A1A1A; }
    .login-box { background-color: #262626; padding: 30px; border-radius: 15px; border: 1px solid #404040; margin-top: 20px; }
    
    /* هندسة شبكة التقويم المالي الذكي المستوحى بالكامل من صورتك المقترحة */
    .grid-container {
        display: grid !important;
        grid-template-columns: repeat(7, 1fr) !important;
        gap: 8px !important;
        direction: rtl !important;
        margin-top: 10px !important;
        margin-bottom: 20px !important;
    }
    .grid-header {
        background-color: #1A1A1A;
        padding: 10px 2px;
        text-align: center;
        font-weight: bold;
        border-radius: 6px;
        color: #4CAF50;
        font-size: 14px;
        border: 1px solid #333;
    }
    .grid-day-card {
        background-color: #262626;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 8px;
        min-height: 120px;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    }
    .day-number {
        font-weight: bold;
        font-size: 15px;
        color: #FFFFFF;
        text-align: right;
        font-family: 'Arial', sans-serif;
        margin-bottom: 4px;
    }
    .inner-box-inc {
        background-color: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 5px;
        padding: 4px 2px;
        color: #4CAF50;
        font-size: 11px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 4px;
    }
    .inner-box-exp {
        background-color: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 5px;
        padding: 4px 2px;
        color: #F44336;
        font-size: 11px;
        text-align: center;
        font-weight: bold;
    }
    .grid-empty-card { background-color: transparent !important; border: none !important; box-shadow: none !important; }
    
    /* تصميم جدول الكروت الأسبوعي */
    .week-row-grid { display: grid; grid-template-columns: 1.5fr 2fr 2fr 2fr; gap: 8px; direction: rtl; margin-bottom: 6px; align-items: center; }
    .week-header-cell { background-color: #1A1A1A; padding: 10px; text-align: center; font-weight: bold; border-radius: 6px; color: #4CAF50; border: 1px solid #333; font-size: 13px; }
    .week-cell-day { background-color: #262626; padding: 10px; text-align: center; font-weight: bold; border: 1px solid #444; border-radius: 8px; color: #BBBBBB; font-size: 13px; }
    .week-cell-inc { background-color: #262626; padding: 10px; text-align: center; border: 1px solid #444; border-radius: 8px; color: #4CAF50; font-weight: bold; font-size: 13px; }
    .week-cell-exp { background-color: #262626; padding: 10px; text-align: center; border: 1px solid #444; border-radius: 8px; color: #F44336; font-weight: bold; font-size: 13px; }
    .week-cell-rem { background-color: #262626; padding: 10px; text-align: center; border: 1px solid #444; border-radius: 8px; font-weight: bold; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# ربط التطبيق بتاريخ اليوم الفعلي لعام 2026م
current_date = datetime.now()
current_year_str = str(current_date.year)
current_total_months = current_date.year * 12 + current_date.month

DB_FILE = "my_budget_storage.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS financial_data 
                 (email TEXT, category TEXT, name TEXT, amount REAL, remaining_months INTEGER, start_month_val INTEGER, year_month TEXT, PRIMARY KEY (email, category, name, year_month))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_income_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, date TEXT, source TEXT, amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_expense_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, date TEXT, item TEXT, amount REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flexible_goals_v2 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, type TEXT, name TEXT, amount REAL, target_date TEXT, is_done INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def delete_daily_record(record_id, table_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def get_recent_daily_records(email, table_name, date_str):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT id, date, {'source' if table_name=='daily_income_records' else 'item'} AS label, amount FROM {table_name} WHERE email=? AND date=? ORDER BY id DESC LIMIT 5", conn, params=(email, date_str))
    conn.close()
    return df.to_dict(orient='records')

def get_flexible_items_v2(email, type_str):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, name, amount, target_date, is_done FROM flexible_goals_v2 WHERE email=? AND type=?", conn, params=(email, type_str))
    conn.close()
    return df.to_dict(orient='records')

def add_flexible_item_v2(email, type_str, name, amount, target_date_str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO flexible_goals_v2 (email, type, name, amount, target_date, is_done) VALUES (?, ?, ?, ?, ?, 0)", (email, type_str, name, amount, target_date_str))
    conn.commit()
    conn.close()

def update_flexible_status_v2(item_id, is_done_val):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE flexible_goals_v2 SET is_done=? WHERE id=?", (is_done_val, item_id))
    conn.commit()
    conn.close()

def get_all_fixed_data_for_user(email, category):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, amount, remaining_months, start_month_val, year_month FROM financial_data WHERE email=? AND category=?", conn, params=(email, category))
    conn.close()
    return df

def save_user_item_monthly(email, category, name, amount, remaining_months=0, start_month_val=0, ym_str=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO financial_data (email, category, name, amount, remaining_months, start_month_val, year_month) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (email, category, name, amount, remaining_months, start_month_val, ym_str))
    conn.commit()
    conn.close()

def save_daily_income(email, date_str, source, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO daily_income_records (email, date, source, amount) VALUES (?, ?, ?, ?)", (email, date_str, source, amount))
    conn.commit()
    conn.close()

def save_daily_expense(email, date_str, item, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO daily_expense_records (email, date, item, amount) VALUES (?, ?, ?, ?)", (email, date_str, item, amount))
    conn.commit()
    conn.close()

def get_daily_income_records(email):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, date, source, amount FROM daily_income_records WHERE email=?", conn, params=(email,))
    conn.close()
    return df

def get_daily_expense_records(email):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, date, item, amount FROM daily_expense_records WHERE email=?", conn, params=(email,))
    conn.close()
    return df

def get_user_data_monthly(email, category, ym_str):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, amount, remaining_months, start_month_val FROM financial_data WHERE email=? AND category=? AND year_month=?", conn, params=(email, category, ym_str))
    conn.close()
    return df.to_dict(orient='records')

def clear_user_data(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM financial_data WHERE email=?", (email,))
    c.execute("DELETE FROM daily_income_records WHERE email=?", (email,))
    c.execute("DELETE FROM daily_expense_records WHERE email=?", (email,))
    c.execute("DELETE FROM flexible_goals_v2 WHERE email=?", (email,))
    conn.commit()
    conn.close()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""

this_month_ym = current_date.strftime('%Y-%m')

# ==============================================================================
# 🔐 شاشة الدخول الرئيسية
# ==============================================================================
if not st.session_state.logged_in:
    st.title("💰 تطبيق My Budget")
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    email_input = st.text_input("📧 بريد الجيميل (Gmail):", placeholder="example@gmail.com")
    password_input = st.text_input("🔑 كلمة المرور:", type="password")
    if st.button("🚀 دخول / تسجيل حساب جديد"):
        if email_input and password_input:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE email=?", (email_input,))
            user = c.fetchone()
            if user:
                if user[0] == password_input:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else: st.error("⚠️ كلمة المرور خاطئة")
            else:
                c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email_input, password_input))
                conn.commit()
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.rerun()
            conn.close()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user_key = st.session_state.user_email

st.sidebar.success(f"👤 متصل بـ: {st.session_state.user_email}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.rerun()

st.sidebar.write("---")

menu_selection = st.sidebar.radio(
    "انتقل بين الأقسام واللوحات الحية:",
    ["🛒 المصروفات والدخل اليومي", "💳 الالتزامات والأقساط", "🗓️ التقويم والحصيلة الشهرية", "📌 الأهداف والالتزامات المرنة", "📊 لوحة التحليلات والاتجاهات"]
)

df_daily_inc_records = get_daily_income_records(user_key)
df_daily_exp_records = get_daily_expense_records(user_key)
all_fixed_data_df = get_all_fixed_data_for_user(user_key, "fixed")
all_installments_df = get_all_fixed_data_for_user(user_key, "installments")

fixed_incomes = all_fixed_data_df.to_dict(orient='records') if not all_fixed_data_df.empty else [{"name": "الراتب الأساسي", "amount": 10000.0, "year_month": this_month_ym}]

if current_date.month in [1, 2, 3]: q_name, q_months = "الربع الأول (Q1)", [f"{current_year_str}-01", f"{current_year_str}-02", f"{current_year_str}-03"]
elif current_date.month in [4, 5, 6]: q_name, q_months = "الربع الثاني (Q2)", [f"{current_year_str}-04", f"{current_year_str}-05", f"{current_year_str}-06"]
elif current_date.month in [7, 8, 9]: q_name, q_months = "الربع الثالث (Q3)", [f"{current_year_str}-07", f"{current_year_str}-08", f"{current_year_str}-09"]
else: q_name, q_months = "الربع الرابع (Q4)", [f"{current_year_str}-10", f"{current_year_str}-11", f"{current_year_str}-12"]

# --- 1. المصروفات والدخل اليومي ---
if menu_selection == "🛒 المصروفات والدخل اليومي":
    st.header("🛒 قسم المصروفات والدخل اليومي الفعلي")
    col1, col2 = st.columns(2)
    today_stamp = current_date.strftime('%Y-%m-%d')
    
    if 'inc_amount_val' not in st.session_state: st.session_state.inc_amount_val = 0.0
    if 'exp_amount_val' not in st.session_state: st.session_state.exp_amount_val = 0.0
    if 'inc_src_val' not in st.session_state: st.session_state.inc_src_val = "عمل حر"
    if 'exp_itm_val' not in st.session_state: st.session_state.exp_itm_val = "مشتريات"

    with col1:
        st.subheader("💵 إدخال الدخل اليومي الفعلي")
        inc_source = st.text_input("🚀 مصدر الدخل:", value=st.session_state.inc_src_val, key="i_src_widget")
        inc_amount = st.number_input("💰 المبلغ (ريال):", min_value=0.0, value=st.session_state.inc_amount_val, key="i_amt_widget")
        
        if st.button("💾 حفظ الدخل اليومي"):
            if inc_amount > 0:
                save_daily_income(user_key, today_stamp, inc_source, inc_amount)
                st.success("✅ تم حفظ العملية بنجاح!")
                st.session_state.inc_amount_val = 0.0
                st.session_state.inc_src_val = "عمل حر"
                st.rerun()
                
        st.write("")
        recent_inc = get_recent_daily_records(user_key, "daily_income_records", today_stamp)
        if recent_inc:
            st.caption("↩️ عمليات الدخل المحفوظة اليوم (يمكنك حذف أي خطأ فوراً):")
            for rec in recent_inc:
                col_t1, col_t2 = st.columns([3, 1])
                col_t1.text(f"• {rec['label']}: {rec['amount']:,.0f} ريال")
                if col_t2.button("🗑️ حذف", key=f"del_inc_{rec['id']}"):
                    delete_daily_record(rec['id'], "daily_income_records")
                    st.rerun()

    with col2:
        st.subheader("🛍️ إدخال المصروف اليومي الفعلي")
        exp_item = st.text_input("🛒 بند الصرف:", value=st.session_state.exp_itm_val, key="e_itm_widget")
        exp_amount = st.number_input("💸 المبلغ (ريال):", min_value=0.0, value=st.session_state.exp_amount_val, key="e_amt_widget")
        
        if st.button("💾 حفظ المصروف اليومي"):
            if exp_amount > 0:
                save_daily_expense(user_key, today_stamp, exp_item, exp_amount)
                st.success("✅ تم حفظ العملية بنجاح!")
                st.session_state.exp_amount_val = 0.0
                st.session_state.exp_itm_val = "مشتريات"
                st.rerun()
                
        st.write("")
        recent_exp = get_recent_daily_records(user_key, "daily_expense_records", today_stamp)
        if recent_exp:
            st.caption("↩️ عمليات الصرف المحفوظة اليوم (يمكنك حذف أي خطأ فوراً):")
            for rec in recent_exp:
                col_t1, col_t2 = st.columns([3, 1])
                col_t1.text(f"• {rec['label']}: {rec['amount']:,.0f} ريال")
                if col_t2.button("🗑️ حذف", key=f"del_exp_{rec['id']}"):
                    delete_daily_record(rec['id'], "daily_expense_records")
                    st.rerun()

# --- 2. الالتزامات والأقساط ---
elif menu_selection == "💳 الالتزامات والأقساط":
    st.header(f"💳 الالتزامات الثابتة النشطة")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 الدخول الثابتة (مستمرة طوال العام)")
        fixed_db = get_user_data_monthly(user_key, "fixed", this_month_ym)
        fixed_incomes = fixed_db if fixed_db else [{"name": "الراتب الأساسي", "amount": 10000.0}]
        for i, inc in enumerate(fixed_incomes):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input(f"الاسم {i+1}", value=inc['name'], key=f"f_n_{i}")
            amount = c2.number_input(f"المبلغ {i+1}", min_value=0.0, value=float(inc['amount']), key=f"f_v_{i}")
            save_user_item_monthly(user_key, "fixed", name, amount, ym_str=this_month_ym)
        if st.button("➕ أضف دخل ثابت جديد"):
            save_user_item_monthly(user_key, "fixed", f"دخل جديد {len(fixed_incomes)+1}", 0.0, ym_str=this_month_ym)
            st.rerun()
            
    with col2:
        st.subheader("📉 الأقساط والالتزامات المؤتمتة زمنياً")
        current_installments = all_installments_df.to_dict(orient='records') if not all_installments_df.empty else []
        for i, inst in enumerate(current_installments):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input(f"اسم الالتزام {i+1}", value=inst['name'], key=f"in_n_{i}")
            amount = c2.number_input(f"القسط {i+1}", min_value=0.0, value=float(inst['amount']), key=f"in_v_{i}")
            months = c3.number_input(f"الأشهر الإجمالية {i+1}", min_value=1, value=int(inst.get('remaining_months', 1)), key=f"in_m_{i}")
            save_user_item_monthly(user_key, "installments", name, amount, months, inst.get('start_month_val', current_total_months), ym_str=inst['year_month'])
        if st.button("➕ أضف قسط/التزام شهري جديد"):
            save_user_item_monthly(user_key, "installments", f"قسط جديد {len(current_installments)+1}", 0.0, 1, current_total_months, ym_str=this_month_ym)
            st.rerun()

# --- 3. التقويم والحصيلة الشهرية ---
elif menu_selection == "🗓️ التقويم والحصيلة الشهرية":
    st.header("🗓️ لوحة التقويم والحصيلة الشهرية المخصصة")
    st.write("---")
    months_arabic_names = {"01": "يناير", "02": "فبراير", "03": "مارس", "04": "أبريل", "05": "مايو", "06": "يونيو", "07": "يوليو", "08": "أغسطس", "09": "سبتمبر", "10": "أكتوبر", "11": "نوفمبر", "12": "ديسمبر"}
    selected_month_code = st.selectbox("📅 اختر الشهر لاستعراض تقويمه المالي وحصيلته بدقة:", options=list(months_arabic_names.keys()), index=int(current_date.month) - 1, format_func=lambda x: months_arabic_names[x])
    selected_ym_str = f"{current_year_str}-{selected_month_code}"
    selected_month_val = int(current_year_str) * 12 + int(selected_month_code)
    
    sel_fixed_inc_total = all_fixed_data_df['amount'].sum() if not all_fixed_data_df.empty else 0.0
    
    sel_inst_total = 0.0
    if not all_installments_df.empty:
        for idx, inst_row in all_installments_df.iterrows():
            s_m = inst_row['start_month_val']
            duration = inst_row['remaining_months']
            if s_m <= selected_month_val < (s_m + duration):
                sel_inst_total += inst_row['amount']
                
    cal = calendar.Calendar(firstweekday=5)
    month_days = cal.monthdayscalendar(int(current_year_str), int(selected_month_code))
    
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    for day_name in ["السبت", "الأحد", "الإثنين", "الثلاثاء", "أربعاء", "الخميس", "الجمعة"]: st.markdown(f'<div class="grid-header">{day_name}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    for week in month_days:
        for day in week:
            if day == 0: st.markdown('<div class="grid-day-card grid-empty-card"></div>', unsafe_allow_html=True)
            else:
                target_date_str = f"{selected_ym_str}-{day:02d}"
                
                # 🌟 الجمع التراكمي الذكي لجميع إدخالات الدخل والصرف في نهاية اليوم تلقائياً
                day_inc = df_daily_inc_records[df_daily_inc_records['date'] == target_date_str]['amount'].sum() if not df_daily_inc_records.empty else 0.0
                day_exp = df_daily_exp_records[df_daily_exp_records['date'] == target_date_str]['amount'].sum() if not df_daily_exp_records.empty else 0.0
                
                inc_t = f"المدخول: {day_inc:,.0f} ريال"
                exp_t = f"المصروف: {day_exp:,.0f} ريال"
                st.markdown(f'<div class="grid-day-card"><div class="day-number">{day}</div><div class="inner-box-inc">{inc_t}</div><div class="inner-box-exp">{exp_t}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    sel_daily_inc = df_daily_inc_records[(df_daily_inc_records['date'] >= f"{selected_ym_str}-01") & (df_daily_inc_records['date'] <= f"{selected_ym_str}-31")]['amount'].sum() if not df_daily_inc_records.empty else 0.0
    sel_daily_exp = df_daily_exp_records[(df_daily_exp_records['date'] >= f"{selected_ym_str}-01") & (df_daily_exp_records['date'] <= f"{selected_ym_str}-31")]['amount'].sum() if not df_daily_exp_records.empty else 0.0
    
    tot_inc = sel_fixed_inc_total + sel_daily_inc
    tot_exp = sel_inst_total + sel_daily_exp
    tot_wallet = tot_inc - tot_exp
    
    st.write("---")
    st.subheader(f"📊 الخلاصة والتحليلات الصافية لشهر: {months_arabic_names[selected_month_code]}")
    cb1, cb2, cb3 = st.columns(3)
    cb1.info(f"💵 **إجمالي مدخول الشهر الفعلي:**\n\n {tot_inc:,.0f} ريال")
    cb2.warning(f"💸 **إجمالي المصروفات والالتزامات (المفلترة زمنياً):**\n\n {tot_exp:,.0f} ريال")
    if tot_wallet >= 0: cb3.success(f"👛 **صافي المحفظة (المتبقي لك):**\n\n {tot_wallet:,.0f} ريال")
    else: cb3.error(f"🚨 **صافي المحفظة (عجز مالي):**\n\n {tot_wallet:,.0f} ريال")

# --- 4. الأهداف والالتزامات المرنة ---
elif menu_selection == "📌 الأهداف والالتزامات المرنة":
    st.header("📌 قسم الأهداف والالتزامات المرنة")
    col_debts, col_wishes = st.columns(2)
    with col_debts:
        st.subheader("💸 سجل الالتزامات والديون الجانبية")
        d_name = st.text_input("اسم الالتزام / الدين:", placeholder="دين أبو فهد")
        d_amount = st.number_input("المبلغ (ريال):", min_value=0.0, key="d_amt_flx")
        d_date_str = "---"
        if st.checkbox("📅 إضافة تاريخ متوقع لسداد هذا الالتزام"): d_date_str = st.date_input("تاريخ السداد المتوقع:", value=current_date).strftime('%Y-%m-%d')
        if st.button("💾 حفظ الالتزام الجانبي"):
            if d_name and d_amount > 0:
                add_flexible_item_v2(user_key, "debt", d_name, d_amount, d_date_str)
                st.success("✅ تم حفظ الالتزام الجانبي بنجاح!")
                st.rerun()
    with col_wishes:
        st.subheader("🎯 قائمة المشتريات والرغبات المستقبلية")
        w_name = st.text_input("اسم السلعة المستهدفة:", placeholder="لابتوب جديد")
        w_amount = st.number_input("السعر المتوقع (ريال):", min_value=0.0, key="w_amt_flx")
        w_date_str = st.date_input("تاريخ الشراء المتوقع:", value=current_date).strftime('%Y-%m-%d')
        if st.button("💾 حفظ وإدراج تحت المراقبة الزمنية"):
            if w_name and w_amount > 0:
                add_flexible_item_v2(user_key, "wish", w_name, w_amount, w_date_str)
                st.success("✅ تم التوثيق تحت المراقبة الذكية!")
                st.rerun()

# --- 5. لوحة التحليلات والاتجاهات ---
elif menu_selection == "📊 لوحة التحليلات والاتجاهات":
    st.header("📊 لوحة تحليلات الفترات الزمنية والاتجاهات الفعليّة")
    st.write("---")
    
    st.subheader("📅 جدول ومراقبة الأداء المالي الأسبوعي الفعلي (آخر 7 أيام)")
    st.markdown("""
        <div class="week-row-grid">
            <div class="week-header-cell">اليوم (DAY)</div>
            <div class="week-header-cell">الدخل (INCOME)</div>
            <div class="week-header-cell">الصرف (EXPENSE)</div>
            <div class="week-header-cell">المتبقي (REMAINING)</div>
        </div>
        """, unsafe_allow_html=True)
        
    arabic_days = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    total_weekly_inc_sum = 0.0
    total_weekly_exp_sum = 0.0
    
    for d in range(7):
        t_date = current_date - timedelta(days=d)
        t_date_str = t_date.strftime('%Y-%m-%d')
        day_ar = arabic_days.get(t_date.strftime('%A'), t_date.strftime('%A'))
        
        # 🌟 الجمع التراكمي لآخر 7 أيام ليعرض المجموع الصافي بنهاية اليوم
        day_inc = df_daily_inc_records[df_daily_inc_records['date'] == t_date_str]['amount'].sum() if not df_daily_inc_records.empty else 0.0
        day_exp = df_daily_exp_records[df_daily_exp_records['date'] == t_date_str]['amount'].sum() if not df_daily_exp_records.empty else 0.0
        
        total_weekly_inc_sum += day_inc
        total_weekly_exp_sum += day_exp
        day_rem = day_inc - day_exp
        rem_style = "color: #4CAF50;" if day_rem >= 0 else "color: #F44336;"
        
        st.markdown(f"""
            <div class="week-row-grid">
                <div class="week-cell-day">{day_ar}</div>
                <div class="week-cell-inc">+{day_inc:,.0f} ريال</div>
                <div class="week-cell-exp">-{day_exp:,.0f} ريال</div>
                <div class="week-cell-rem" style="{rem_style}">{day_rem:,.0f} ريال</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.write("---")
    st.subheader("📊 إجمالي الحصاد المالي الفعلي لهذا الأسبوع")
    col_w1, col_w2, col_w3 = st.columns(3)
    col_w1.info(f"💵 **إجمالي الدخل لهذا الأسبوع:**\n\n {total_weekly_inc_sum:,.0f} ريال")
    col_w2.warning(f"💸 **إجمالي الصرف لهذا الأسبوع:**\n\n {total_weekly_exp_sum:,.0f} ريال")
    weekly_net_rem = total_weekly_inc_sum - total_weekly_exp_sum
    if weekly_net_rem >= 0: col_w3.success(f"👛 **صافي المتبقي لك هذا الأسبوع:**\n\n {weekly_net_rem:,.0f} ريال")
    else: col_w3.error(f"🚨 **صافي العجز المالي هذا الأسبوع:**\n\n {weekly_net_rem:,.0f} ريال")
        
    st.write("---")
    t_q, t_y = st.tabs(["📐 الحصيلة التراكمية لربع السنة الحالي", "🎆 السجل التاريخي للسنة كاملة"])
    with t_q:
        st.write(f"### 📐 الحصيلة التراكمية الفعلية لـ {q_name}")
        q_f_inc = all_fixed_data_df['amount'].sum() * len(q_months) if not all_fixed_data_df.empty else 0.0
        q_f_exp = 0.0
        if not all_installments_df.empty:
            for q_m in q_months:
                q_m_val = int(q_m.split('-')[0]) * 12 + int(q_m.split('-')[1])
                for idx, r_i in all_installments_df.iterrows():
                    if r_i['start_month_val'] <= q_m_val < (r_i['start_month_val'] + r_i['remaining_months']):
                        q_f_exp += r_i['amount']
        q_d_inc = df_daily_inc_records[df_daily_inc_records['date'].str[:7].isin(q_months)]['amount'].sum() if not df_daily_inc_records.empty else 0.0
        q_d_exp = df_daily_exp_records[df_daily_exp_records['date'].str[:7].isin(q_months)]['amount'].sum() if not df_daily_exp_records.empty else 0.0
        q_tot_income = q_f_inc + q_d_inc
        q_tot_expense = q_f_exp + q_d_exp
        col_q1, col_q2, col_q3 = st.columns(3)
        col_q1.metric("دخل الربع الفعلي المحقق", f"{q_tot_income:,.0f} ريال")
        col_q2.metric("مصروفات الربع الفعلية المدفوعة", f"{q_tot_expense:,.0f} ريال")
        col_q3.metric("صافي الفائض للربع", f"{(q_tot_income - q_tot_expense):,.0f} ريال")
    with t_y:
        st.write(f"### 🎆 السجل التاريخي الفعلي لعام {current_year_str} م")
        y_f_inc = all_fixed_data_df['amount'].sum() * 12 if not all_fixed_data_df.empty else 0.0
        y_f_exp = 0.0
        if not all_installments_df.empty:
            for m_i in range(1, 13):
                m_val = int(current_year_str) * 12 + m_i
                for idx, r_i in all_installments_df.iterrows():
                    if r_i['start_month_val'] <= m_val < (r_i['start_month_val'] + r_i['remaining_months']):
                        y_f_exp += r_i['amount']
        y_d_inc = df_daily_inc_records[df_daily_inc_records['date'].str.startswith(current_year_str)]['amount'].sum() if not df_daily_inc_records.empty else 0.0
        y_d_exp = df_daily_exp_records[df_daily_exp_records['date'].str.startswith(current_year_str)]['amount'].sum() if not df_daily_exp_records.empty else 0.0
        y_tot_income = y_f_inc + y_d_inc
        y_tot_expense = y_f_exp + y_d_exp
        col_y1, col_y2, col_y3 = st.columns(3)
        col_y1.metric("إجمالي دخل السنة الفعلي", f"{y_tot_income:,.0f} ريال")
        col_y2.metric("إجمالي مصروفات السنة الفعلية", f"{y_tot_expense:,.0f} ريال")
        col_y3.metric("صافي مدخرات السنة المحفوظة", f"{(y_tot_income - y_tot_expense):,.0f} ريال")
