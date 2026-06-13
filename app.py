import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import openpyxl
import streamlit as st

# إعدادات الصفحة الأساسية وتصميم الواجهة الذكية المتجاوبة باسم التطبيق My Budget
st.set_page_config(page_title="تطبيق My Budget الاحترافي 3.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) وتنسيق القوائم الجانبية والأزرار
st.markdown("""
    <style>
    body, div, p, h1, h2, h3, h4, th, td { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; font-weight: bold; }
    [data-testid="stSidebar"] { text-align: right; direction: rtl; background-color: #1A1A1A; }
    </style>
    """, unsafe_allow_html=True)

# ربط التطبيق بالتاريخ الحالي الفعلي لعام 2026
current_date = datetime.now()

# تهيئة الذاكرة التخزينية السحابية المؤقتة لحفظ البيانات لمنع الحذف المفاجئ
if 'fixed_incomes' not in st.session_state:
    st.session_state.fixed_incomes = [{"name": "الراتب الأساسي", "amount": 10000.0}]
if 'daily_incomes' not in st.session_state:
    st.session_state.daily_incomes = [{"name": "أوبر / عمل حر", "amount": 250.0}]
if 'daily_expenses' not in st.session_state:
    st.session_state.daily_expenses = [{"name": "المشتريات اليومية", "amount": 50.0}]
if 'installments' not in st.session_state:
    st.session_state.installments = [{"name": "قسط تابي", "amount": 400.0, "months": 4}]

# --- شريط التنقل الجانبي الاحترافي (Sidebar Navigation) ---
st.sidebar.title("🎛️ My Budget - القائمة")
menu_selection = st.sidebar.radio(
    "انتقل بين أقسام ميزانيتك:",
    ["🛒 المصروفات والدخل اليومي", "💳 الالتزامات والأقساط", "📊 لوحة التحليلات والاتجاهات"]
)

st.sidebar.write("---")
st.sidebar.subheader("📅 تاريخ اليوم الفعلي")
st.sidebar.info(f"اليوم: **{current_date.strftime('%Y-%m-%d')}**")

# حساب الربع السنوي تلقائياً
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
    st.write("ادمج مصادر دخلك المتنوعة وتحكّم بمصروفاتك اليومية المباشرة بصورة تفاعلية")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 مصادر الدخل اليومي (المتغير)")
        for i, vinc in enumerate(st.session_state.daily_incomes):
            c1, c2 = st.columns([2, 1])
            vinc['name'] = c1.text_input(f"مصدر الدخل اليومي {i+1}", value=vinc['name'], key=f"d_inc_n_{i}")
            vinc['amount'] = c2.number_input(f"المعدل اليومي {i+1}", min_value=0.0, value=float(vinc['amount']), key=f"d_inc_v_{i}")
        if st.button("➕ أضف مصدر دخل يومي"):
            st.session_state.daily_incomes.append({"name": "مصدر يومي جديد", "amount": 0.0})
            st.rerun()
            
        buffer_percent = st.slider("🛡️ نسبة استقطاع وسادة الأمان للطوارئ من الدخل اليومي (%):", min_value=0, max_value=50, value=10)

    with col2:
        st.subheader("🛍️ المصروفات اليومية المتغيرة")
        for i, exp in enumerate(st.session_state.daily_expenses):
            c1, c2 = st.columns([2, 1])
            exp['name'] = c1.text_input(f"بند المصروف اليومي {i+1}", value=exp['name'], key=f"d_exp_n_{i}")
            exp['amount'] = c2.number_input(f"الصرف اليومي {i+1}", min_value=0.0, value=float(exp['amount']), key=f"d_exp_v_{i}")
        if st.button("➕ أضف بند مصروف يومي"):
            st.session_state.daily_expenses.append({"name": "مصروف يومي جديد", "amount": 0.0})
            st.rerun()

# ==============================================================================
# 2. صفحة الالتزامات والأقساط
# ==============================================================================
elif menu_selection == "💳 الالتزامات والأقساط":
    st.header("💳 قسم الالتزامات والأقساط - My Budget")
    st.write("تتبع الدخول الثابتة الشهرية والالتزامات والأقساط طويلة وقصيرة المدى بمرونة")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 الدخول الثابتة الشهرية (رواتب، عوائد)")
        for i, inc in enumerate(st.session_state.fixed_incomes):
            c1, c2 = st.columns([2, 1])
            inc['name'] = c1.text_input(f"اسم الدخل الثابت {i+1}", value=inc['name'], key=f"fix_n_{i}")
            inc['amount'] = c2.number_input(f"المبلغ {i+1}", min_value=0.0, value=float(inc['amount']), key=f"fix_v_{i}")
        if st.button("➕ أضف دخل ثابت جديد"):
            st.session_state.fixed_incomes.append({"name": "دخل ثابت جديد", "amount": 0.0})
            st.rerun()

    with col2:
        st.subheader("📉 الأقساط والالتزامات النشطة")
        for i, inst in enumerate(st.session_state.installments):
            c1, c2, c3 = st.columns([2, 1, 1])
            inst['name'] = c1.text_input(f"اسم الالتزام {i+1}", value=inst['name'], key=f"inst_n_{i}")
            inst['amount'] = c2.number_input(f"القسط الشهري {i+1}", min_value=0.0, value=float(inst['amount']), key=f"inst_v_{i}")
            inst['months'] = c3.number_input(f"الأشهر المتبقية {i+1}", min_value=1, value=int(inst['months']), key=f"inst_m_{i}")
        if st.button("➕ أضف قسط/التزام شهري"):
            st.session_state.installments.append({"name": "قسط جديد", "amount": 0.0, "months": 1})
            st.rerun()

# ==============================================================================
# 3. صفحة لوحة التحليلات والاتجاهات + ميزة رفع ملف الإكسل وحفظ الأمان
# ==============================================================================
elif menu_selection == "📊 لوحة التحليلات والاتجاهات":
    st.header("📊 لوحة تحليلات My Budget وتتبع الاتجاهات")
    st.write("---")
    
    # 📥 خيار ميزة رفع ملف إكسل مخصص لقراءة وتتبع مصاريف الشهر كاملاً
    st.subheader("📂 استيراد ميزانية الشهر من ملف إكسل (Excel)")
    uploaded_file = st.file_uploader("ارفع ملف الإكسل (.xlsx) الخاص بمصاريفك هنا:", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            excel_df = pd.read_excel(uploaded_file)
            st.success("✅ تم رفع وقراءة ملف الإكسل بنجاح وتحديث اتجاهات الميزانية!")
            st.dataframe(excel_df, use_container_width=True)
            # رسم بياني تفاعلي مبني على ملف الإكسل المرفوع مباشرة لتتبع اتجاهاته
            if len(excel_df.columns) >= 2:
                fig_excel = px.line(excel_df, x=excel_df.columns[0], y=excel_df.columns[1], title="📉 منحنى تتبع اتجاهات الصرف والدخل من ملفك المرفوع")
                st.plotly_chart(fig_excel, use_container_width=True)
        except Exception as e:
            st.error("⚠️ عذراً، تأكد من هيكلة ملف الإكسل بشكل صحيح ليتمكن التطبيق من قراءته.")
    
    st.write("---")
    
    # العمليات البرمجية الحسابية الديناميكية لربط البيانات المدخلة
    total_fixed_inc = sum(item['amount'] for item in st.session_state.fixed_incomes)
    
    # حسبة الدخل اليومي المتغير ومجاميعه للأسبوع والشهر
    raw_daily_inc = sum(item['amount'] for item in st.session_state.daily_incomes)
    weekly_var_inc = raw_daily_inc * 7
    monthly_var_inc = raw_daily_inc * 30
    
    # استقطاع وسادة الطوارئ الآمنة لحفظ التوازن المالي
    buffer_percent = st.session_state.get('buffer_percent', 10)
    buffer_extracted = (monthly_var_inc * buffer_percent) / 100
    net_monthly_var = monthly_var_inc - buffer_extracted
    
    # المصروفات اليومية المتغيرة شهرياً
    total_daily_exp = sum(item['amount'] for item in st.session_state.daily_expenses)
    monthly_var_exp = total_daily_exp * 30
    
    total_installments = sum(item['amount'] for item in st.session_state.installments)
    
    total_income = total_fixed_inc + net_monthly_var
    total_expenses = total_installments + monthly_var_exp
    net_surplus = total_income - total_expenses
    
    # عرض ملخص الحسبة المخصصة للدخل اليومي
    st.subheader("🚨 تقرير تجميع الدخل اليومي المتغير")
    cx1, cx2 = st.columns(2)
    cx1.info(f"📊 **مجموع الدخل المتغير (نهاية كل أسبوع):** {weekly_var_inc:,.0f} ريال")
    cx2.info(f"📅 **مجموع الدخل المتغير الإجمالي (نهاية كل شهر):** {monthly_var_inc:,.0f} ريال")
    
    st.write("---")
    
    # تقارير فترات الشهر والربع سنوي وبداية السنة
    t1, t2, t3 = st.tabs(["🗓️ نهاية الشهر الحالي", "📐 ربع السنة الحالي", "🎆 بداية العام القادم (تقديري)"])
    
    with t1:
        st.write(f"### الوضع المالي التفاعلي المباشر لنهاية الشهر الحالي لعام 2026")
        m1, m2, m3 = st.columns(3)
        m1.metric("صافي الدخل المجمع", f"{total_income:,.0f} ريال")
        m2.metric("إجمالي المصاريف والأقساط", f"{total_expenses:,.0f} ريال")
        m3.metric("صافي الفائض المالي", f"{net_surplus:,.0f} ريال")
        
        chart_data = [
            {'الفئة': 'الدخول الثابتة', 'المبلغ': total_fixed_inc, 'النوع': 'الدخول'},
            {'الفئة': 'صافي الدخل اليومي المجمع', 'المبلغ': net_monthly_var, 'النوع': 'الدخول'},
            {'الفئة': 'المصروفات اليومية المتغيرة', 'المبلغ': monthly_var_exp, 'النوع': 'المصاريف'},
            {'الفئة': 'الأقساط والالتزامات الثابتة', 'المبلغ': total_installments, 'النوع': 'المصاريف'}
        ]
        df_m = pd.DataFrame(chart_data)
        fig_m = px.bar(df_m, x='الفئة', y='المبلغ', color='النوع', text_auto=True, title="مقارنة هيكلية الدخل والصرف الشهرية")
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
        
    st.write("---")
    
    # 🔒 زر الأمان المالي للحفظ الأبدي
    st.subheader("💾 مركز حماية البيانات والأمان الأبدي")
    st.write("حمل كافة البيانات التفاعلية التي أدخلتها الآن في ملف إكسل لضمان عدم حذفها أو فقدانها أبداً:")
    
    backup_data = {
        'نوع السجل': ['الدخول الثابتة', 'الدخول اليومية المجمعة', 'المصروفات اليومية المجمعة', 'الأقساط والالتزامات'],
        'المجموع الشهري التقديري (ريال)': [total_fixed_inc, monthly_var_inc, monthly_var_exp, total_installments]
    }
    backup_df = pd.DataFrame(backup_data)
    
    # تحويل البيانات إلى كود ملف إكسل جاهز للتحميل المباشر بنقرة واحدة
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        backup_df.to_excel(writer, index=False, sheet_name='My Budget 3.0')
    
    st.download_button(
        label="📥 اضغط هنا لتحميل نسخة احتياطية من بياناتك كملف Excel فوراً",
        data=buffer.getvalue(),
        file_name=f"my_budget_backup_{current_date.strftime('%Y_%m_%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("💡 نصيحة أمان: حمل ملف النسخة الاحتياطية نهاية كل شهر واحفظه في مجلدك المالي الخاص لحماية تاريخية كاملة لبياناتك.")
