import os
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import openpyxl
import streamlit as st

# إعدادات الصفحة الأساسية وتصميم الواجهة باسم التطبيق My Budget
st.set_page_config(page_title="تطبيق My Budget الاحترافي 5.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) وتنسيق القوائم الجانبية والأزرار
st.markdown("""
    <style>
    .block-container { text-align: right; direction: rtl; }
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; }
    [data-testid="stSidebar"] { text-align: right; direction: rtl; background-color: #1A1A1A; }
    </style>
    """, unsafe_allow_html=True)

# ربط التطبيق بالتاريخ الحالي الفعلي لعام 2026
current_date = datetime.now()

# --- إعداد وإنشاء قاعدة البيانات المحلية المدمجة بالسيرفر لحفظ البيانات للأبد ---
DB_FILE = "my_budget_storage.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # إنشاء جدول الحسابات
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
    # إنشاء جدول البيانات المالية الموحد
    c.execute('''CREATE TABLE IF NOT EXISTS financial_data 
                 (email TEXT, category TEXT, name TEXT, amount REAL, remaining_months INTEGER, PRIMARY KEY (email, category, name))''')
    conn.commit()
    conn.close()

init_db()

# مساعدة برمجية لإدارة جلب وحفظ البيانات من السيرفر
def get_user_data(email, category):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, amount, remaining_months FROM financial_data WHERE email=? AND category=?", conn, params=(email, category))
    conn.close()
    return df.to_dict(orient='records')

def save_user_item(email, category, name, amount, remaining_months=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO financial_data (email, category, name, amount, remaining_months) 
                 VALUES (?, ?, ?, ?, ?)''', (email, category, name, amount, remaining_months))
    conn.commit()
    conn.close()

def clear_user_data(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM financial_data WHERE email=?", (email,))
    conn.commit()
    conn.close()

# --- نظام التحكم بتسجيل الدخول الحقيقي ---
st.sidebar.title("🔐 حسابك المالي الآمن")
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    email_input = st.sidebar.text_input("أدخل بريد الجيميل الخاص بك (Gmail):", placeholder="example@gmail.com")
    password_input = st.sidebar.text_input("أدخل كلمة المرور الخاصة بك:", type="password")
    
    col_login, col_signup = st.sidebar.columns(2)
    
    if col_login.button("🔑 دخول / تسجيل"):
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
                    st.sidebar.error("كلمة المرور خاطئة")
            else:
                # إنشاء حساب جديد تلقائياً للمستخدم إذا لم يكن مسجلاً
                c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email_input, password_input))
                conn.commit()
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.rerun()
            conn.close()
        else:
            st.sidebar.error("الرجاء تعبئة البيانات")
    st.stop()

else:
    st.sidebar.success(f"👤 متصل بـ: {st.session_state.user_email}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

# تحميل البيانات الحية من قاعدة البيانات السحابية الدائمة الخاصة بالمستخدم الحالي
user_key = st.session_state.user_email

fixed_db = get_user_data(user_key, "fixed")
daily_inc_db = get_user_data(user_key, "daily_income")
daily_exp_db = get_user_data(user_key, "daily_expense")
installments_db = get_user_data(user_key, "installments")

# تعبئة القيم الافتراضية التفاعلية للمرة الأولى فقط
fixed_incomes = fixed_db if fixed_db else [{"name": "الراتب الأساسي", "amount": 10000.0}]
daily_incomes = daily_inc_db if daily_inc_db else [{"name": "أوبر / عمل حر", "amount": 250.0}]
daily_expenses = daily_exp_db if daily_exp_db else [{"name": "المشتريات اليومية", "amount": 50.0}]
installments = installments_db if installments_db else [{"name": "قسط تابي", "amount": 400.0, "remaining_months": 4}]

# --- شريط التنقل الجانبي الاحترافي ---
st.sidebar.title("🎛️ My Budget - القائمة")
menu_selection = st.sidebar.radio(
    "انتقل بين أقسام ميزانيتك المحفوظة تلقائياً:",
    ["🛒 المصروفات والدخل اليومي", "💳 الالتزامات والأقساط", "📊 لوحة التحليلات والاتجاهات"]
)

# حساب الربع السنوي التلقائي لعام 2026 الحالي
if current_date.month in [1, 2, 3]: q = "الربع الأول (Q1)"
elif current_date.month in [4, 5, 6]: q = "الربع الثاني (Q2)"
elif current_date.month in [7, 8, 9]: q = "الربع الثالث (Q3)"
else: q = "الربع الرابع (Q4)"
st.sidebar.caption(f"تتبع مالي مستمر لـ: **{q}**")

# ==============================================================================
# 1. صفحة المصروفات والدخل اليومي
# ==============================================================================
if menu_selection == "🛒 المصروفات والدخل اليومي":
    st.header("🛒 قسم المصروفات والدخل اليومي - My Budget")
    st.caption("🔒 أي رقم يتم تعديله أو إضافته هنا يُحفظ في حسابك على السيرفر فوراً وللأبد.")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 مصادر الدخل اليومي (المتغير)")
        updated_daily_incomes = []
        for i, vinc in enumerate(daily_incomes):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input(f"مصدر الدخل اليومي {i+1}", value=vinc['name'], key=f"d_inc_n_{i}")
            amount = c2.number_input(f"المعدل اليومي {i+1}", min_value=0.0, value=float(vinc['amount']), key=f"d_inc_v_{i}")
            save_user_item(user_key, "daily_income", name, amount)
            updated_daily_incomes.append({"name": name, "amount": amount})
            
        if st.button("➕ أضف مصدر دخل يومي جديد"):
            save_user_item(user_key, "daily_income", f"مصدر جديد {len(daily_incomes)+1}", 0.0)
            st.rerun()
            
        buffer_percent = st.slider("🛡️ نسبة استقطاع وسادة الأمان للطوارئ من الدخل اليومي (%):", min_value=0, max_value=50, value=10)

    with col2:
        st.subheader("🛍️ المصروفات اليومية المتغيرة")
        updated_daily_expenses = []
        for i, exp in enumerate(daily_expenses):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input(f"بند المصروف اليومي {i+1}", value=exp['name'], key=f"d_exp_n_{i}")
            amount = c2.number_input(f"الصرف اليومي {i+1}", min_value=0.0, value=float(exp['amount']), key=f"d_exp_v_{i}")
            save_user_item(user_key, "daily_expense", name, amount)
            updated_daily_expenses.append({"name": name, "amount": amount})
            
        if st.button("➕ أضف بند مصروف يومي جديد"):
            save_user_item(user_key, "daily_expense", f"مصروف جديد {len(daily_expenses)+1}", 0.0)
            st.rerun()

# ==============================================================================
# 2. صفحة الالتزامات والأقساط
# ==============================================================================
elif menu_selection == "💳 الالتزامات والأقساط":
    st.header("💳 قسم الالتزامات والأقساط - My Budget")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 الدخول الثابتة الشهرية (رواتب، عوائد)")
        for i, inc in enumerate(fixed_incomes):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input(f"اسم الدخل الثابت {i+1}", value=inc['name'], key=f"fix_n_{i}")
            amount = c2.number_input(f"المبلغ {i+1}", min_value=0.0, value=float(inc['amount']), key=f"fix_v_{i}")
            save_user_item(user_key, "fixed", name, amount)
            
        if st.button("➕ أضف دخل ثابت جديد"):
            save_user_item(user_key, "fixed", f"دخل ثابت {len(fixed_incomes)+1}", 0.0)
            st.rerun()

    with col2:
        st.subheader("📉 الأقساط والالتزامات النشطة")
        for i, inst in enumerate(installments):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input(f"اسم الالتزام {i+1}", value=inst['name'], key=f"inst_n_{i}")
            amount = c2.number_input(f"القسط الشهري {i+1}", min_value=0.0, value=float(inst['amount']), key=f"inst_v_{i}")
            months = c3.number_input(f"الأشهر المتبقية {i+1}", min_value=1, value=int(inst.get('remaining_months', inst.get('months', 1))), key=f"inst_m_{i}")
            save_user_item(user_key, "installments", name, amount, months)
            
        if st.button("➕ أضف قسط/التزام شهري جديد"):
            save_user_item(user_key, "installments", f"قسط جديد {len(installments)+1}", 0.0, 1)
            st.rerun()
            
    st.write("---")
    if st.button("🔄 تصفير البيانات والبدء من جديد"):
        clear_user_data(user_key)
        st.success("تم مسح بيانات الحساب الحالي بنجاح لإعادة الضبط!")
        st.rerun()

# ==============================================================================
# 3. صفحة لوحة التحليلات والاتجاهات (تحديث الصيغة المطلوبة في التقرير)
# ==============================================================================
elif menu_selection == "📊 لوحة التحليلات والاتجاهات":
    st.header("📊 لوحة تحليلات My Budget وتتبع الاتجاهات")
    st.write("---")
    
    # حساب العمليات المالية الحسابية
    total_fixed_inc = sum(item['amount'] for item in fixed_incomes)
    raw_daily_inc = sum(item['amount'] for item in daily_incomes)
    
    # تعديل الصيغة المطلوبة لتكون واضحة واحترافية للتقرير البصري لجمع الدخل المتغير
    weekly_var_inc = raw_daily_inc * 7
    monthly_var_inc = raw_daily_inc * 30
    
    buffer_percent = 10
    buffer_extracted = (monthly_var_inc * buffer_percent) / 100
    net_monthly_var = monthly_var_inc - buffer_extracted
    
    total_daily_exp = sum(item['amount'] for item in daily_expenses)
    monthly_var_exp = total_daily_exp * 30
    total_installments = sum(item['amount'] for item in installments)
    
    total_income = total_fixed_inc + net_monthly_var
    total_expenses = total_installments + monthly_var_exp
    net_surplus = total_income - total_expenses
    
    # الواجهة البصرية المعدلة حسب الطلب للتجميع الأسبوعي والشهري
    st.subheader("🚨 تقرير تجميع الدخل المتغير")
    col_box1, col_box2 = st.columns(2)
    col_box1.info(f"📊 **مجموع الدخل المتغير الأسبوعي:** {weekly_var_inc:,.0f} ريال")
    col_box2.info(f"📅 **مجموع الدخل المتغير الشهري:** {monthly_var_inc:,.0f} ريال")
    st.write("---")
    
    t1, t2, t3 = st.tabs(["🗓️ نهاية الشهر الحالي", "📐 ربع السنة الحالي", "🎆 بداية العام القادم (تقديري)"])
    
    with t1:
        st.write(f"### الوضع المالي التفاعلي المباشر لنهاية الشهر الحالي لعام {current_date.year}")
        m1, m2, m3 = st.columns(3)
        m1.metric("صافي الدخل المجمع", f"{total_income:,.0f} ريال")
        m2.metric("إجمالي المصاريف والأقساط", f"{total_expenses:,.0f} ريال")
        m3.metric("صافي الفائض المالي", f"{net_surplus:,.0f} ريال")
        
        chart_data = [
            {'الفئة': 'الدخول الثابتة', 'المبلغ': total_fixed_inc, 'النوع': 'الدخول'},
            {'الفئة': 'صافي الدخل اليومي مجمع', 'المبلغ': net_monthly_var, 'النوع': 'الدخول'},
            {'الفئة': 'المصروفات اليومية مجمعة', 'المبلغ': monthly_var_exp, 'النوع': 'المصاريف'},
            {'الفئة': 'الأقساط والالتزامات', 'المبلغ': total_installments, 'النوع': 'المصاريف'}
        ]
        df_m = pd.DataFrame(chart_data)
        fig_m = px.bar(df_m, x='الفئة', y='المبلغ', color='النوع', text_auto=True)
        st.plotly_chart(fig_m, use_container_width=True)
        
    with t2:
        st.write(f"### التحليلات التراكمية الربع سنوية لـ {q}")
        q1, q2, q3 = st.columns(3)
        q1.metric("الدخل الربعي التقديري", f"{(total_income * 3):,.0f} ريال")
        q2.metric("المصاريف الربعية التقديرية", f"{(total_expenses * 3):,.0f} ريال")
        q3.metric("الفائض الربعي المتوقع", f"{(net_surplus * 3):,.0f} ريال")
        
    with t3:
        st.write(f"### التحليل السنوي الاستباقي لبداية العام القادم {current_date.year + 1}م")
        y1, y2, y3 = st.columns(3)
        y1.metric("الدخل السنوي المتوقع", f"{(total_income * 12):,.0f} ريال")
        y2.metric("المصاريف السنوية التقديرية", f"{(total_expenses * 12):,.0f} ريال")
        y3.metric("الفائض السنوي المستهدف", f"{(net_surplus * 12):,.0f} ريال")
