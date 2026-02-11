from docxtpl import DocxTemplate
import pandas as pd
import numpy as np
import streamlit as st
import io
import datetime

st.set_page_config(layout="wide")
st.title('ITR NEW TAX REGIME CALCULATION 2026-27')

# Tax slab constants for new regime FY 2025-26
TAX_SLABS = {
    "0-400000": 0,
    "400001-800000": 0.05,
    "800001-1200000": 0.10,
    "1200001-1600000": 0.15,
    "1600001-2000000": 0.20,
    "2000001-2400000": 0.25,
    "above_2400000": 0.30
}

year = st.selectbox('Select Year', ['2025-26', '2026-27'])
assesment_year = st.selectbox('Select Assessment Year', ['2026-27', '2027-28'])
pan = st.text_input('PAN')
eid = st.text_input('Employee ID')
name = st.text_input('Name', key='name')

dt = datetime.datetime.now().date()
place = st.text_input('Place', key='place')
ahc = st.text_input('AHC', key='ahc')
district = st.text_input('District', key='district')

gross_salary = st.number_input('GROSS SALARY', value=0)
other_salary = st.number_input('OTHER SALARY', value=0)
st_deduction = st.number_input('STANDARD DEDUCTION', value=75000)  # Updated as per new regime
tax_paid = st.number_input('TAX PAID', value=0)
income = gross_salary + other_salary
totalincome = income - st_deduction

def calc_tax_new_regime(totalincome):
    """Calculate tax under new regime for FY 2025-26 with slab-wise breakdown"""
    tax = 0
    remaining_income = totalincome
    
    slab_tax = {
        'slab1_tax': 0,  # 0-4L (Nil)
        'slab2_tax': 0,  # 4L-8L (5%)
        'slab3_tax': 0,  # 8L-12L (10%)
        'slab4_tax': 0,  # 12L-16L (15%)
        'slab5_tax': 0,  # 16L-20L (20%)
        'slab6_tax': 0,  # 20L-24L (25%)
        'slab7_tax': 0,  # >24L (30%)
        'rebate': 0
    }
    
    # Calculate tax from highest slab to lowest slab
    if remaining_income > 2400000:
        taxable_amount = remaining_income - 2400000
        slab_tax['slab7_tax'] = round(taxable_amount * 0.30)
        tax += slab_tax['slab7_tax']
        remaining_income = 2400000
    
    if remaining_income > 2000000:
        taxable_amount = remaining_income - 2000000
        slab_tax['slab6_tax'] = round(taxable_amount * 0.25)
        tax += slab_tax['slab6_tax']
        remaining_income = 2000000
    
    if remaining_income > 1600000:
        taxable_amount = remaining_income - 1600000
        slab_tax['slab5_tax'] = round(taxable_amount * 0.20)
        tax += slab_tax['slab5_tax']
        remaining_income = 1600000
    
    if remaining_income > 1200000:
        taxable_amount = remaining_income - 1200000
        slab_tax['slab4_tax'] = round(taxable_amount * 0.15)
        tax += slab_tax['slab4_tax']
        remaining_income = 1200000
    
    if remaining_income > 800000:
        taxable_amount = remaining_income - 800000
        slab_tax['slab3_tax'] = round(taxable_amount * 0.10)
        tax += slab_tax['slab3_tax']
        remaining_income = 800000
    
    if remaining_income > 400000:
        taxable_amount = remaining_income - 400000
        slab_tax['slab2_tax'] = round(taxable_amount * 0.05)
        tax += slab_tax['slab2_tax']
        remaining_income = 400000
    
    # Check for rebate under section 87A (if total income <= 700000 in new regime)
    if totalincome <= 700000:
        slab_tax['rebate'] = tax
        tax = 0
        # Reset all slab taxes since full rebate applies
        for key in slab_tax:
            if key != 'rebate':
                slab_tax[key] = 0
    
    return tax, slab_tax

data = {
    'year': str(year), 
    'assesment_year': str(assesment_year),
    'pan': str(pan),
    'eid': str(eid),
    'name': str(name),
    'tax_paid': float(tax_paid),
    'gross_salary': float(gross_salary),
    'other_salary': float(other_salary),
    'st_deduction': float(st_deduction),
    'income': float(income),
    'totalincome': float(totalincome),
    'dt': str(dt),
    'place': str(place),
    'ahc': str(ahc),
    'district': str(district)
}

df = pd.DataFrame(data, index=[0])

getdata = st.button('Calculate Tax')
if getdata:
    # Calculate tax with slab breakdown
    totalincome_value = df['totalincome'].iloc[0]
    tax, slab_tax = calc_tax_new_regime(totalincome_value)
    
    # Add education cess (4%)
    educess = round(0.04 * tax)
    total_tax = tax + educess
    
    # Calculate final payable/refundable tax
    tax_paid_value = df['tax_paid'].iloc[0]
    payable_tax = round(total_tax - tax_paid_value)
    refundable_tax = abs(payable_tax) if payable_tax < 0 else 0
    
    # Calculate income per slab
    income_per_slab = {
        'slab1_income': min(400000, totalincome_value),
        'slab2_income': max(0, min(400000, totalincome_value - 400000)) if totalincome_value > 400000 else 0,
        'slab3_income': max(0, min(400000, totalincome_value - 800000)) if totalincome_value > 800000 else 0,
        'slab4_income': max(0, min(400000, totalincome_value - 1200000)) if totalincome_value > 1200000 else 0,
        'slab5_income': max(0, min(400000, totalincome_value - 1600000)) if totalincome_value > 1600000 else 0,
        'slab6_income': max(0, min(400000, totalincome_value - 2000000)) if totalincome_value > 2000000 else 0,
        'slab7_income': max(0, totalincome_value - 2400000)
    }
    
    # Create tax data dictionary
    tax_data = {
        'tax': tax,
        'educess': educess,
        'total_tax': total_tax,
        'payable_tax': payable_tax if payable_tax > 0 else 0,
        'refundable_tax': refundable_tax,
        **income_per_slab,  # Add income per slab
        **slab_tax  # Add slab-wise tax amounts
    }
    
    # Convert to DataFrame and display
    result_dict = {**df.iloc[0].to_dict(), **tax_data}
    result_df = pd.DataFrame([result_dict])
    
    # Display results in a better format
    st.subheader("Tax Calculation Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Income", f"₹{totalincome_value:,.0f}")
        st.metric("Tax Calculated", f"₹{tax:,.0f}")
    
    with col2:
        st.metric("Education Cess (4%)", f"₹{educess:,.0f}")
        st.metric("Total Tax Liability", f"₹{total_tax:,.0f}")
    
    with col3:
        st.metric("Tax Already Paid", f"₹{tax_paid_value:,.0f}")
        st.metric("Tax Payable", f"₹{payable_tax:,.0f}")
        if refundable_tax > 0:
            st.metric("Refund Amount", f"₹{refundable_tax:,.0f}")
    
    # Display slab-wise breakdown
    st.subheader("Slab-wise Tax Breakdown")
    slab_data = []
    slabs = [
        ("0 - 4,00,000", "Nil", f"₹{income_per_slab['slab1_income']:,.0f}", f"₹{slab_tax['slab1_tax']:,.0f}"),
        ("4,00,001 - 8,00,000", "5%", f"₹{income_per_slab['slab2_income']:,.0f}", f"₹{slab_tax['slab2_tax']:,.0f}"),
        ("8,00,001 - 12,00,000", "10%", f"₹{income_per_slab['slab3_income']:,.0f}", f"₹{slab_tax['slab3_tax']:,.0f}"),
        ("12,00,001 - 16,00,000", "15%", f"₹{income_per_slab['slab4_income']:,.0f}", f"₹{slab_tax['slab4_tax']:,.0f}"),
        ("16,00,001 - 20,00,000", "20%", f"₹{income_per_slab['slab5_income']:,.0f}", f"₹{slab_tax['slab5_tax']:,.0f}"),
        ("20,00,001 - 24,00,000", "25%", f"₹{income_per_slab['slab6_income']:,.0f}", f"₹{slab_tax['slab6_tax']:,.0f}"),
        ("Above 24,00,000", "30%", f"₹{income_per_slab['slab7_income']:,.0f}", f"₹{slab_tax['slab7_tax']:,.0f}")
    ]
    
    slab_df = pd.DataFrame(slabs, columns=["Income Range", "Tax Rate", "Taxable Amount", "Tax Amount"])
    st.table(slab_df)
    
    if slab_tax['rebate'] > 0:
        st.info(f"Rebate under Section 87A applied: ₹{slab_tax['rebate']:,.0f}")
    
    # Generate document
    doc_data = result_dict
    doc = DocxTemplate("taxnew.docx")
    doc.render(doc_data)
    
    # Download button
    bio = io.BytesIO()
    doc.save(bio)
    st.download_button(
        label="Download ITR Form",
        data=bio.getvalue(),
        file_name=f"{name}_new_itrform.docx",
        mime="docx"
    )
