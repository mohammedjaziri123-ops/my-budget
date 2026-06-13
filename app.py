import os
import subprocess
import sys

# التثبيت التلقائي للمكتبات الناقصة بالسيرفر لضمان عدم ظهور الشاشة الحمراء
try:
    import pandas as pd
    import plotly.express as px
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "plotly"])
    import pandas as pd
    import plotly.express as px

import streamlit as st

# إعدادات الصفحة الأساسية ودعم الهاتف والوضع الداكن
st.set_page_config(page_title="تطبيق ميزانيتي التفاعلي 2.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) وتنسيق الأزرار الكبيرة لسرعة الإدخال
st.markdown("""
    <style>
    body, div, p, h1, h2, h3, h4, th, td { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1E88E5; color: white; font-weight: bold; }
    .delete-btn>button { background-color: #e53935 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 تطبيق ميزانيتي التفاعلي 2.0")
st.subheader("تحويل البيانات من جداول صامتة إلى واجهات تفاعلية تدعم اتخاذ القرار وتتنبأ بالمستقبل المالي")
st.write("---")

# استخدام الذاكرة المؤقتة لـ Streamlit لحفظ البيانات أثناء التنقل والتعديل
if 'fixed_incomes' not in st.session_state:
    st.session_state.fixed_incomes = [{"name": "الراتب الأساسي", "amount": 10000.0}]

if 'var_incomes' not in st.session_state:
    st.session_state.var_incomes = [{"name": "أوبر", "amount": 1500.0}]

if 'installments' not in st.session_state:
    st.session_state.installments = [{"name": "قسط تابي", "amount": 400.0, "months": 4}]

# تقسيم الواجهة إلى قسمين: المدخلات التفاعلية ولوحة التحليلات
col1, col2 = st.columns([1, 1.5])

with col1:
    st.header("📥 لوحة الإدخال والتحكم")
    
    # --- قسم الدخول الثابتة ---
    st.subheader("💵 الدخول الثابتة (رواتب، عوائد...)")
    for i, inc in enumerate(st.session_state.fixed_incomes):
        c1, c2 = st.columns([2, 1])
        inc['name'] = c1.text_input(f"اسم الدخل الثابت {i+1}", value=inc['name'], key=f"fix_name_{i}")
        inc['amount'] = c2.number_input(f"المبلغ {i+1}", min_value=0.0, value=float(inc['amount']), key=f"fix_val_{i}")
    
    if st.button("➕ أضف دخل ثابت جديد"):
        st.session_state.fixed_incomes.append({"name": "دخل جديد", "amount": 0.0})
        st.rerun()
        
    st.write("---")
    
    # --- قسم الدخول المتغيرة ---
    st.subheader("🚗 الدخول المتغيرة (أوبر، بولت، متجر...)")
    for i, vinc in enumerate(st.session_state.var_incomes):
        c1, c2 = st.columns([2, 1])
        vinc['name'] = c1.text_input(f"مصدر الدخل المتغير {i+1}", value=vinc['name'], key=f"var_name_{i}")
        vinc['amount'] = c2.number_input(f"المبلغ اليومي/الشهري {i+1}", min_value=0.0, value=float(vinc['amount']), key=f"var_val_{i}")
        
    if st.button("➕ أضف دخل متغير جديد"):
        st.session_state.var_incomes.append({"name": "مصدر متغير جديد", "amount": 0.0})
        st.rerun()
        
    # ميزة وسادة الأمان المالي
    buffer_percent = st.slider("🛡️ نسبة استقطاع وسادة الأمان المالي للطوارئ من الدخل المتغير (%):", min_value=0, max_value=50, value=10)
    
    st.write("---")
    
    # --- قسم الأقساط والالتزامات ---
    st.subheader("💳 الأقساط والالتزامات النشطة")
    for i, inst in enumerate(st.session_state.installments):
        c1, c2, c3 = st.columns([2, 1, 1])
        inst['name'] = c1.text_input(f"اسم الالتزام/القسط {i+1}", value=inst['name'], key=f"inst_name_{i}")
        inst['amount'] = c2.number_input(f"القسط الشهري {i+1}", min_value=0.0, value=float(inst['amount']), key=f"inst_val_{i}")
        inst['months'] = c3.number_input(f"أشهر متبقية {i+1}", min_value=1, value=int(inst['months']), key=f"inst_months_{i}")
        
    if st.button("➕ أضف قسط أو التزام جديد"):
        st.session_state.installments.append({"name": "قسط جديد", "amount": 0.0, "months": 1})
        st.rerun()
        
    # خانة للمصاريف العامة الأخرى
    st.write("---")
    other_expenses = st.number_input("💸 المصاريف الشهرية العامة الأخرى (تقديري):", min_value=0.0, value=4500.0, step=500.0)

    # زر مخصص لتصفير الميزانية للبدء من جديد
    if st.button("🔄 إعادة ضبط وتصفير القوائم"):
        st.session_state.fixed_incomes = [{"name": "الراتب الأساسي", "amount": 0.0}]
        st.session_state.var_incomes = [{"name": "أوبر", "amount": 0.0}]
        st.session_state.installments = []
        st.rerun()

with col2:
    st.header("📊 لوحة التحليلات المتقدمة والتنبؤات")
    
    # العمليات البرمجية الحسابية الديناميكية لمجموع القوائم
    total_fixed = sum(item['amount'] for item in st.session_state.fixed_incomes)
    raw_variable = sum(item['amount'] for item in st.session_state.var_incomes)
    
    # حساب مخصص الطوارئ المستقطع من الدخول المتغيرة
    buffer_extracted = (raw_variable * buffer_percent) / 100
    net_variable = raw_variable - buffer_extracted
    
    total_income = total_fixed + net_variable
    total_installments = sum(item['amount'] for item in st.session_state.installments)
    total_expenses = total_installments + other_expenses
    net_surplus = total_income - total_expenses
    
    # عرض البطاقات الرقمية الكبيرة سريعة القراءة وفهم الوضع المالي بلمحة
    c1, c2, c3 = st.columns(3)
    c1.metric(label="💵 إجمالي الدخل الصافي", value=f"{total_income:,.0f} ريال")
    c2.metric(label="📉 إجمالي المصاريف والالتزامات", value=f"{total_expenses:,.0f} ريال")
    
    if net_surplus >= 0:
        c3.metric(label="🟢 صافي الفائض المتوقع", value=f"{net_surplus:,.0f} ريال")
    else:
        c3.metric(label="🔴 العجز المالي المكتشف", value=f"{net_surplus:,.0f} ريال")
        
    st.write("---")
    
    # عرض معلومات وسادة الطوارئ الآمنة
    if buffer_extracted > 0:
        st.info(f"🛡️ **رصيد الأمان المالي الحالي (وسادة الطوارئ):** تم تأمين **{buffer_extracted:,.0f} ريال** تلقائياً من دخل العمل الحر لحمايتك من تقلبات السوق.")
    
    # توليد التنبؤات والاشعارات الذكية ديناميكياً لكل قسط مضاف
    st.subheader("📢 التنبؤات والاشعارات الذكية")
    if len(st.session_state.installments) > 0:
        for inst in st.session_state.installments:
            if inst['amount'] > 0:
                st.success(f"💡 **بشرى سارة:** متبقي لك **{inst['months']} أشهر** فقط وتنتهي تماماً من (**{inst['name']}**) بقيمة {inst['amount']:,.0f} ريال شهرياً!")
    else:
        st.success("🎉 ميزانيتك حرة تماماً من أي أقساط مجدولة حالياً!")
        
    st.write("---")
    
    # بناء الرسم البياني التفاعلي المتحرك الذي يعكس التحديثات فوراً
    st.subheader("📈 مقارنة أداء الصرف والدخل التفاعلية")
    
    chart_data = []
    for item in st.session_state.fixed_incomes:
        if item['amount'] > 0: chart_data.append({'الفئة': item['name'], 'المبلغ (ريال)': item['amount'], 'النوع': 'الدخول'})
    if net_variable > 0: 
        chart_data.append({'الفئة': 'صافي الدخول المتغيرة', 'المبلغ (ريال)': net_variable, 'النوع': 'الدخول'})
    for item in st.session_state.installments:
        if item['amount'] > 0: chart_data.append({'الفئة': item['name'], 'المبلغ (ريال)': item['amount'], 'النوع': 'المصاريف'})
    chart_data.append({'الفئة': 'المصاريف العامة الأخرى', 'المبلغ (ريال)': other_expenses, 'النوع': 'المصاريف'})
    if net_surplus > 0:
        chart_data.append({'الفئة': 'صافي الفائض المالي الشهرى', 'المبلغ (ريال)': net_surplus, 'النوع': 'الفائض'})
        
    df = pd.DataFrame(chart_data)
    
    if not df.empty:
        fig = px.bar(df, x='الفئة', y='المبلغ (ريال)', color='النوع', text_auto=True,
                     title="تحليل شامل وتفاعلي لمصادر الدخل وأوجه الصرف الحالية")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("الرجاء إدخال بيانات مالية لاستعراض المخطط البياني التفاعلي.")
