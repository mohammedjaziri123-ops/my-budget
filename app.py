import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة الأساسية والدعم المالي واللغة العربية
st.set_page_config(page_title="تطبيق ميزانيتي 2.0", page_icon="💰", layout="wide")

# تطبيق نمط الاتجاه من اليمين لليسار (RTL) والوضع الداكن المقترح
st.markdown("""
    <style>
    body, div, p, h1, h2, h3, h4, th, td { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 تطبيق ميزانيتي 2.0")
st.subheader("تحويل البيانات إلى واجهات تفاعلية تدعم اتخاذ القرار وتتنبأ بالمستقبل المالي")
st.write("---")

# تقسيم الشاشة إلى قسمين: المدخلات واللوحة التحليلية
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📥 إدخال البيانات المالي")
    
    # 1. هيكلة الدخول المتعددة
    st.subheader("💵 الدخول الثابتة والمتغيرة")
    fixed_income = st.number_input("الدخل الثابت (راتب، عوائد استثمارية):", min_value=0, value=10000, step=500)
    
    variable_source = st.text_input("مصدر الدخل المتغير (أوبر، بولت، متجر...):", value="أوبر")
    variable_amount = st.number_input(f"مبلغ الدخل المتغير من ({variable_source}):", min_value=0, value=1500, step=100)
    
    # ميزة مخصص الطوارئ (الوسادة المالية للعمل الحر)
    buffer_percent = st.slider("نسبة استقطاع وسادة الأمان المالي للطوارئ (%):", min_value=0, max_value=50, value=10)
    
    st.write("---")
    
    # 2. إدارة الديون والأقساط
    st.subheader("💳 الأقساط والالتزامات")
    tabby_installment = st.number_input("قسط تابي الشهري:", min_value=0, value=400, step=50)
    tabby_months = st.number_input("عدد الأشهر المتبقية لقسط تابي:", min_value=1, value=4, step=1)
    other_expenses = st.number_input("المصاريف الشهرية الأخرى (تقديري):", min_value=0, value=4500, step=500)

with col2:
    st.header("📊 لوحة التحليلات المتقدمة والتنبؤات")
    
    # الحسابات البرمجية خلف الكواليس
    buffer_extracted = (variable_amount * buffer_percent) / 100
    net_variable_income = variable_amount - buffer_extracted
    total_income = fixed_income + net_variable_income
    total_expenses = tabby_installment + other_expenses
    net_surplus = total_income - total_expenses
    
    # عرض البطاقات الرقمية الكبيرة سريعة القراءة
    c1, c2, c3 = st.columns(3)
    c1.metric(label="💰 إجمالي الدخل الصافي", value=f"{total_income:,.0f} ريال")
    c2.metric(label="📉 إجمالي المصاريف", value=f"{total_expenses:,.0f} ريال")
    
    # تلوين الفائض المالي تبعا للنتيجة
    if net_surplus >= 0:
        c3.metric(label="🟢 صافي الفائض المتوقع", value=f"{net_surplus:,.0f} ريال")
    else:
        c3.metric(label="🔴 العجز المالي", value=f"{net_surplus:,.0f} ريال")
        
    st.write("---")
    
    # ميزة وسادة الأمان المستقطعة بصرياً
    st.info(f"🛡️ **رصيد الأمان المالي الحالي (وسادة الطوارئ):** تم تأمين **{buffer_extracted:,.0f} ريال** من دخلك المتغير لضمان استقرارك.")
    
    # 3. تنبؤات الفائض المالي الذكية
    st.success(f"📢 **بشرى سارة:** متبقي لك **{tabby_months} أشهر** فقط وتنتهي من قسط تابي! هذا هو الفائض المتوقع في ميزانيتك القادمة.")
    
    st.write("---")
    
    # 4. الرسوم البيانية التفاعلية (مقارنة الدخل والمصارف والصافي)
    st.subheader("📈 مقارنة أداء الصرف والدخل")
    data = {
        'الفئة': ['الدخل الثابت', 'الدخل المتغير (الصافي)', 'المصاريف والالتزامات', 'صافي الفائض الشهرى'],
        'المبلغ (ريال)': [fixed_income, net_variable_income, total_expenses, max(0, net_surplus)]
    }
    df = pd.DataFrame(data)
    
    fig = px.bar(df, x='الفئة', y='المبلغ (ريال)', color='الفئة', text_auto=True, title="الوضع المالي التقديري للشهر الحالي")
    st.plotly_chart(fig, use_container_width=True)
