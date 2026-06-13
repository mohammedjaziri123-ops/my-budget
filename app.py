import os
import sqlite3
import calendar
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import openpyxl
import streamlit as st

# إعدادات الصفحة الأساسية وتصميم الواجهة باسم التطبيق My Budget
st.set_page_config(page_title="تطبيق My Budget - رفيقك المالي الدائم 12.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) وتنسيق الواجهة والتقويم والتنبيهات
st.markdown("""
    <style>
    .block-container { text-align: right; direction: rtl; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; height: 45px; }
    [data-testid="stSidebar"] { text-align: right; direction: rtl; background-color: #1A1A1A; }
    .login-box { background-color: #262626; padding: 30px; border-radius: 15px; border: 1px solid #404040; margin-top: 20px; }
    .stDataFrame { direction: rtl; text-align: right; }
    
    /* تنسيق مربعات أيام التقويم المالي الذكي */
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; direction: rtl; margin-bottom: 25px; }
    .cal-header { background-color: #1A1A1A; padding: 10px; text-align: center; font-weight: bold; border-radius: 5px; color: #4CAF50; }
    .cal-day { background-color: #262626; border: 1px solid #404040; border-radius: 8px; padding: 8px; min-height: 90px; display: flex; flex-direction: column; justify-content: space-between; }
    .cal-day-num { font-weight: bold; font-size: 14px; color: #888; border-bottom: 1px solid #333; padding-bottom: 2px; }
    .cal-inc { color: #4CAF50; font-size: 12px; font-weight: bold; text-align: center; margin-top: 4px; }
    .cal-exp { color: #F44336; font-size: 12px; font-weight: bold; text-align: center; margin-bottom: 4px; }
    .cal-empty { background-color: transparent; border: none; }
    </style>
    """, unsafe_allow_html=True)

# ربط التطبيق بتاريخ اليوم الفعلي لعام 2026
current_date = datetime.now()
current_year_str = str(current_date.year)
current_total_months = current_date.year * 12 + current_date.month

# --- إعداد وإنشاء قاعدة البيانات المحلية المدمجة بالسيرفر لحفظ البيانات للأبد ---
DB_FILE = "my_budget_storage.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS financial_data 
                 (email TEXT, category TEXT, name TEXT, amount REAL, remaining_months INTEGER, start_month_val INTEGER, year_month TEXT, PRIMARY KEY (email, category, name, year_month))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_income_records 
                 (email TEXT, date TEXT, source TEXT, amount REAL, PRIMARY KEY (email, date, source))''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_expense_records 
                 (email TEXT, date TEXT, item TEXT, amount REAL, PRIMARY KEY (email, date, item))''')
    
    # تحديث جدول الالتزامات المرنة ليدعم حقول التاريخ الجديدة والمشتريات بدقة
    c.execute('''CREATE TABLE IF NOT EXISTS flexible_goals_v2 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, type TEXT, name TEXT, amount REAL, target_date TEXT, is_done INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# دوال مساعدة لنسخة الالتزامات المرنة المحدثة
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

def get_user_data_monthly(email, category, ym_str):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, amount, remaining_months, start_month_val FROM financial_data WHERE email=? AND category=? AND year_month=?", conn, params=(email, category, ym_str))
    conn.close()
    return df.to_dict(orient='records')

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
    c.execute('''INSERT OR REPLACE INTO daily_income_records (email, date, source, amount) 
                 VALUES (?, ?, ?, ?)''', (email, date_str, source, amount))
    conn.commit()
    conn.close()

def save_daily_expense(email, date_str, item, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO daily_expense_records (email, date, item, amount) 
                 VALUES (?, ?, ?, ?)''', (email, date_str, item, amount))
    conn.commit()
    conn.close()

def get_daily_income_records(email):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT date, source, amount FROM daily_income_records WHERE email=?", conn, params=(email,))
    conn.close()
    return df

def get_daily_expense_records(email):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT date, item, amount FROM daily_expense_records WHERE email=?", conn, params=(email,))
    conn.close()
    return df

def get_all_fixed_data_for_user(email, category):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, amount, year_month FROM financial_data WHERE email=? AND category=?", conn, params=(email, category))
    conn.close()
    return df

def clear_user_data(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM financial_data WHERE email=?", (email,))
    c.execute("DELETE FROM daily_income_records WHERE email=?", (email,))
    c.execute("DELETE FROM daily_expense_records WHERE email=?", (email,))
    c.execute("DELETE FROM flexible_goals_v2 WHERE email=?", (email,))
    conn.commit()
    conn.close()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

this_month_ym = current_date.strftime('%Y-%m')

# ==============================================================================
# 🔐 شاشة الدخول الرئيسية
# ==============================================================================
if not st.session_state.logged_in:
    st.title("💰 مرحباً بك في تطبيق My Budget")
    st.subheader("الرجاء تسجيل الدخول أو إنشاء حساب جديد للوصول إلى ميزانيتك المحفوظة للأبد")
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    email_input = st.text_input("📧 بريد الجيميل الخاص بك (Gmail):", placeholder="example@gmail.com")
    password_input = st.text_input("🔑 كلمة المرور:", type="password", placeholder="أدخل كلمة المرور الخاصة بك")
    
    st.write("")
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
                else:
                    st.error("⚠️ كلمة المرور خاطئة")
            else:
                c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email_input, password_input))
                conn.commit()
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.success("🎉 تم إنشاء حسابك بنجاح!")
                st.rerun()
            conn.close()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 🔓 واجهة التطبيق بعد تسجيل الدخول
# ==============================================================================
user_key = st.session_state.user_email

st.sidebar.success(f"👤 متصل بـ: {st.session_state.user_email}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.rerun()

st.sidebar.write("---")

fixed_db = get_user_data_monthly(user_key, "fixed", this_month_ym)
installments_db = get_user_data_monthly(user_key, "installments", this_month_ym)

fixed_incomes = fixed_db if fixed_db else [{"name": "الراتب الأساسي", "amount": 10000.0}]
installments = installments_db if installments_db else []

st.sidebar.title("🎛️ My Budget - الأقسام")
menu_selection = st.sidebar.radio(
    "انتقل بين أقسام ميزانيتك المحفوظة:",
    ["🛒 المصروفات والدخل اليومي", "💳 الالتزامات والأقساط", "📌 الأهداف والالتزامات المرنة", "📊 لوحة التحليلات والاتجاهات"]
)

# --- 1. صفحة المصروفات والدخل اليومي الفعلي ---
if menu_selection == "🛒 المصروفات والدخل اليومي":
    st.header("🛒 قسم المصروفات والدخل اليومي الفعلي - My Budget")
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💵 إدخال الدخل اليومي الفعلي")
        inc_source = st.text_input("🚀 مصدر الدخل الفوري:", value="أوبر", key="inc_src_key")
        inc_amount = st.number_input("💰 المبلغ (ريال):", min_value=0.0, value=0.0, step=50.0, key="inc_amt_key")
        if st.button("💾 حفظ الدخل اليومي الفوري"):
            if inc_amount > 0:
                today_str = current_date.strftime('%Y-%m-%d')
                save_daily_income(user_key, today_str, inc_source, inc_amount)
                st.success(f"✅ تم حفظ {inc_amount} ريال لمصدر ({inc_source})!")
                st.rerun()

    with col2:
        st.subheader("🛍️ إدخال الصرف والمصروفات اليومية")
        exp_item = st.text_input("🛒 بند الصرف الفعلي:", value="مطعم", key="exp_item_key")
        exp_amount = st.number_input("💸 المبلغ المصروف (ريال):", min_value=0.0, value=0.0, step=10.0, key="exp_amt_key")
        if st.button("💾 حفظ المصروف اليومي الفوري"):
            if exp_amount > 0:
                today_str = current_date.strftime('%Y-%m-%d')
                save_daily_expense(user_key, today_str, exp_item, exp_amount)
                st.success(f"✅ تم حفظ بند صرف بقيمة {exp_amount} ريال لـ ({exp_item})!")
                st.rerun()

# --- 2. صفحة الالتزامات والأقساط الشهرية الحالية ---
elif menu_selection == "💳 الالتزامات والأقساط":
    st.header(f"💳 قسم الالتزامات لشهر {this_month_ym} الحالي")
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 الدخول الثابتة لهذا الشهر")
        for i, inc in enumerate(fixed_incomes):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input(f"اسم الدخل الثابت {i+1}", value=inc['name'], key=f"fix_n_{i}")
            amount = c2.number_input(f"المبلغ {i+1}", min_value=0.0, value=float(inc['amount']), key=f"fix_v_{i}")
            save_user_item_monthly(user_key, "fixed", name, amount, ym_str=this_month_ym)
        if st.button("➕ أضف دخل ثابت جديد لهذا الشهر"):
            save_user_item_monthly(user_key, "fixed", f"دخل ثابت {len(fixed_incomes)+1}", 0.0, ym_str=this_month_ym)
            st.rerun()

    with col2:
        st.subheader("📉 الأقساط والالتزامات المدفوعة هذا الشهر")
        for i, inst in enumerate(installments):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input(f"اسم الالتزام {i+1}", value=inst['name'], key=f"inst_n_{i}")
            amount = c2.number_input(f"القسط الشهري {i+1}", min_value=0.0, value=float(inst['amount']), key=f"inst_v_{i}")
            s_month = inst.get('start_month_val', current_total_months)
            months = c3.number_input(f"الأشهر الإجمالية {i+1}", min_value=1, value=int(inst.get('remaining_months', 1)), key=f"inst_m_{i}")
            save_user_item_monthly(user_key, "installments", name, amount, months, s_month, ym_str=this_month_ym)
        if st.button("➕ أضف قسط/التزام شهري جديد"):
            save_user_item_monthly(user_key, "installments", f"قسط جديد {len(installments)+1}", 0.0, 1, current_total_months, ym_str=this_month_ym)
            st.rerun()

# ==============================================================================
# 📌 3. قسم الأهداف والالتزامات المرنة (التحديث الشامل والمطلوب)
# ==============================================================================
elif menu_selection == "📌 الأهداف والالتزامات المرنة":
    st.header("📌 قسم الأهداف والالتزامات المرنة - My Budget")
    st.caption("🔒 هذا القسم جانبي بالكامل ولا يدخل في الحسب الشهرية المباشرة لضمان دقة أرقامك الحالية.")
    st.write("---")
    
    col_debts, col_wishes = st.columns(2)
    
    with col_debts:
        st.subheader("💸 سجل الالتزامات والديون الجانبية")
        d_name = st.text_input("اسم الالتزام / الدين:", placeholder="مثال: دين أبو فهد", key="debt_n_in")
        d_amount = st.number_input("المبلغ (ريال):", min_value=0.0, value=0.0, key="debt_a_in")
        
        # خيار السداد المتوقع الاختياري
        enable_debt_date = st.checkbox("📅 نود إضافة تاريخ متوقع لسداد هذا الالتزام")
        d_date_str = "---"
        if enable_debt_date:
            chosen_d_date = st.date_input("حدد تاريخ السداد المتوقع:", value=current_date)
            d_date_str = chosen_d_date.strftime('%Y-%m-%d')
            
        if st.button("💾 حفظ الالتزام الجانبي"):
            if d_name and d_amount > 0:
                add_flexible_item_v2(user_key, "debt", d_name, d_amount, d_date_str)
                st.success("✅ تم حفظ الالتزام الجانبي بنجاح!")
                st.rerun()
                
        st.write("---")
        my_debts = get_flexible_items_v2(user_key, "debt")
        if my_debts:
            for debt in my_debts:
                status = "✅ تم السداد" if debt['is_done'] == 1 else "⏳ معلق"
                st.markdown(f"• **{debt['name']}**: {debt['amount']:,.0f} ريال | تاريخ السداد المتوقع: `{debt['target_date']}` [*{status}*]")
                if debt['is_done'] == 0:
                    if st.button(f"أشر كـ تم السداد لـ {debt['name']}", key=f"b_d_{debt['id']}"):
                        update_flexible_status_v2(debt['id'], 1)
                        st.rerun()
        else:
            st.info("سجلك فارغ من الالتزامات الجانبية حالياً.")

    with col_wishes:
        st.subheader("🎯 قائمة المشتريات والرغبات المستقبلية")
        w_name = st.text_input("اسم المشتريات / السلعة المستهدفة:", placeholder="مثال: لابتوب جديد")
        w_amount = st.number_input("سعرها المتوقع (ريال):", min_value=0.0, value=0.0, key="w_a_in")
        
        # تاريخ الشراء المتوقع الإلزامي لتفعيل نظام التنبيه بعد 3 أشهر
        chosen_w_date = st.date_input("حدد تاريخ الشراء المتوقع للسلعة:", value=current_date)
        w_date_str = chosen_w_date.strftime('%Y-%m-%d')
        
        if st.button("💾 حفظ وإدراج تحت المراقبة الزمنية"):
            if w_name and w_amount > 0:
                add_flexible_item_v2(user_key, "wish", w_name, w_amount, w_date_str)
                st.success(f"✅ تم إدراج {w_name} تحت مراقبة نظام التنبيه الـ 3 أشهر!")
                st.rerun()
                
        st.write("---")
        my_wishes = get_flexible_items_v2(user_key, "wish")
        if my_wishes:
            for wish in my_wishes:
                status = "🎉 تم الشراء" if wish['is_done'] == 1 else "🔍 قيد الانتظار"
                st.markdown(f"• **{wish['name']}**: {wish['amount']:,.0f} ريال | تاريخ الشراء المتوقع: `{wish['target_date']}` [*{status}*]")
                if wish['is_done'] == 0:
                    if st.button(f"تأكيد إتمام الشراء لـ {wish['name']}", key=f"b_w_{wish['id']}"):
                        update_flexible_status_v2(wish['id'], 1)
                        st.rerun()
        else:
            st.info("لا توجد مستهدفات في قائمة مشترياتك حالياً.")

# ==============================================================================
# 📊 4. صفحة التحليلات المتقدمة + التقويم المالي + نظام تنبيه الـ 3 أشهر للمشتريات
# ==============================================================================
elif menu_selection == "📊 لوحة التحليلات والاتجاهات":
    st.header("📊 لوحة تحليلات My Budget وتتبع الاتجاهات")
    st.write("---")
    
    # 🔔 فحص نظام التنبيه الذكي للمشتريات (إذا مضى على تاريخ الشراء المتوقع 3 أشهر أو أكثر)
    my_wishes = get_flexible_items_v2(user_key, "wish")
    if my_wishes:
        for wish in my_wishes:
            if wish['is_done'] == 0 and wish['target_date'] != "---":
                try:
                    # تحويل نص التاريخ المخزن إلى كود زمني لمقارنته بدقة
                    t_date = datetime.strptime(wish['target_date'], '%Y-%m-%d')
                    # حساب الفارق بالأيام؛ 3 أشهر تعادل برمجياً حوالي 90 يوماً
                    days_passed = (current_date - t_date).days
                    
                    if days_passed >= 90:
                        st.warning(f"⏰ **تنبيه قائمة الرغبات:** يا محمد، لقد مضى أكثر من **3 أشهر** على تاريخ الشراء المتوقع الذي حددته لـ (**{wish['name']}**) بقيمة {wish['amount']:,.0f} ريال! يرجى مراجعة محفظتك بالأسفل لترى إن كان بإمكانك اقتناؤها الآن. 🛒")
                except:
                    pass

    df_daily_inc_records = get_daily_income_records(user_key)
    df_daily_exp_records = get_daily_expense_records(user_key)
    
    current_fixed_inc_total = sum(item['amount'] for item in fixed_incomes)
    current_inst_total = sum(item['amount'] for item in installments)
    
    month_daily_inc = df_daily_inc_records[(df_daily_inc_records['date'] >= f"{this_month_ym}-01") & (df_daily_inc_records['date'] <= f"{this_month_ym}-31")]['amount'].sum() if not df_daily_inc_records.empty else 0.0
    month_daily_exp = df_daily_exp_records[(df_daily_exp_records['date'] >= f"{this_month_ym}-01") & (df_daily_exp_records['date'] <= f"{this_month_ym}-31")]['amount'].sum() if not df_daily_exp_records.empty else 0.0
    
    global_month_income = current_fixed_inc_total + month_daily_inc
    global_month_expense = current_inst_total + month_daily_exp
    global_month_wallet = global_month_income - global_month_expense

    # ==============================================================================
    # 📅 قسم التقويم المالي التفاعلي لشهر يونيو 2026م
    # ==============================================================================
    st.subheader(f"📅 لوحة التقويم المالي التفاعلي لشهر: {current_date.strftime('%B %Y')}م")
    
    cal = calendar.Calendar(firstweekday=5)
    month_days = cal.monthdayscalendar(current_date.year, current_date.month)
    
    st.markdown('<div class="cal-grid">', unsafe_allow_html=True)
    for day_name in ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة"]:
        st.markdown(f'<div class="cal-header">{day_name}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="cal-grid">', unsafe_allow_html=True)
    for week in month_days:
        for day in week:
            if day == 0:
                st.markdown('<div class="cal-day cal-empty"></div>', unsafe_allow_html=True)
            else:
                target_date_str = f"{this_month_ym}-{day:02d}"
                day_inc_sum = df_daily_inc_records[df_daily_inc_records['date'] == target_date_str]['amount'].sum() if not df_daily_inc_records.empty else 0.0
                day_exp_sum = df_daily_exp_records[df_daily_exp_records['date'] == target_date_str]['amount'].sum() if not df_daily_exp_records.empty else 0.0
                
                inc_text = f"+{day_inc_sum:,.0f} ريال" if day_inc_sum > 0 else "---"
                exp_text = f"-{day_exp_sum:,.0f} ريال" if day_exp_sum > 0 else "---"
                
                st.markdown(f"""
                    <div class="cal-day">
                        <div class="cal-day-num">{day}</div>
                        <div class="cal-inc">{inc_text}</div>
                        <div class="cal-exp">{exp_text}</div>
                    </div>
                """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # الخلاصة التراكمية الصافية للشهر الحالي
    st.write("---")
    st.subheader("📊 الخلاصة التراكمية الصافية للشهر الحالي")
    c_box1, c_box2, c_box3 = st.columns(3)
    c_box1.info(f"💵 **إجمالي مدخول الشهر الفعلي:**\n\n {global_month_income:,.0f} ريال")
    c_box2.warning(f"💸 **إجمالي المصروفات والالتزامات:**\n\n {global_month_expense:,.0f} ريال")
    if global_month_wallet >= 0:
        c_box3.success(f"👛 **صافي المحفظة (المتبقي لك):**\n\n {global_month_wallet:,.0f} ريال")
    else:
        c_box3.error(f"🚨 **صافي المحفظة (عجز مالي):**\n\n {global_month_wallet:,.0f} ريال")
