import pandas as pd
import numpy as np
import streamlit as st
import io
import datetime

from docxtpl import DocxTemplate


st.set_page_config(layout="wide")
st.title('ITR NEW TAX REGIME CALCULATION 2026-27')


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
    slab_tax = {
        'slab1_tax': 0,  # 0-4L
        'slab2_tax': 0,  # 4L-8L
        'slab3_tax': 0,  # 8L-12L
        'slab4_tax': 0,  # 12L-16L
        'slab5_tax': 0,  # 16L-20L
        'slab6_tax': 0,  # 20L-24L
        'slab7_tax': 0,  # >24L
        'rebate': 0
    }
    
    # Store original income for marginal benefit calculation
    original_income = totalincome
    
    # 5% slab (4L-8L)
    taxable_amount = min(400000, max(0, totalincome - 400000))
    slab_tax['slab2_tax'] = round(taxable_amount * 0.05)
    tax += slab_tax['slab2_tax']
    
    # 10% slab (8L-12L)
    taxable_amount = min(400000, max(0, totalincome - 800000))
    slab_tax['slab3_tax'] = round(taxable_amount * 0.10)
    tax += slab_tax['slab3_tax']
    
    # 15% slab (12L-16L)
    taxable_amount = min(400000, max(0, totalincome - 1200000))
    slab_tax['slab4_tax'] = round(taxable_amount * 0.15)
    tax += slab_tax['slab4_tax']
    
    # 20% slab (16L-20L)
    taxable_amount = min(400000, max(0, totalincome - 1600000))
    slab_tax['slab5_tax'] = round(taxable_amount * 0.20)
    tax += slab_tax['slab5_tax']
    
    # 25% slab (20L-24L)
    taxable_amount = min(400000, max(0, totalincome - 2000000))
    slab_tax['slab6_tax'] = round(taxable_amount * 0.25)
    tax += slab_tax['slab6_tax']
    
    # 30% slab (above 24L)
    taxable_amount = max(0, totalincome - 2400000)
    slab_tax['slab7_tax'] = round(taxable_amount * 0.30)
    tax += slab_tax['slab7_tax']
    
    total_slab_tax = slab_tax['slab2_tax'] + slab_tax['slab3_tax'] + slab_tax['slab4_tax'] + slab_tax['slab5_tax'] + slab_tax['slab6_tax'] + slab_tax['slab7_tax']
    
    # Marginal tax benefit condition
    marginal_benefit_applied = False
    adjusted_income = original_income
    
    # Check if tax calculated is greater than (taxable income - 1200000)
    if total_slab_tax > (original_income - 1200000) and original_income > 1200000:
        marginal_benefit_applied = True
        # Taxable income becomes the minimum of (original_income - 1200000) and original_income
        adjusted_income = min(original_income - 1200000, original_income)
        # Ensure adjusted income is not negative
        adjusted_income = max(0, adjusted_income)
        
        # Recalculate tax with adjusted income
        tax, slab_tax, total_slab_tax = recalc_tax_with_adjusted_income(adjusted_income)
    
    return tax, slab_tax, total_slab_tax, marginal_benefit_applied, adjusted_income

def recalc_tax_with_adjusted_income(adjusted_income):
    """Helper function to recalculate tax with adjusted income"""
    tax = 0
    slab_tax = {
        'slab1_tax': 0, 'slab2_tax': 0, 'slab3_tax': 0,
        'slab4_tax': 0, 'slab5_tax': 0, 'slab6_tax': 0,
        'slab7_tax': 0, 'rebate': 0
    }
    
    # Recalculate all slabs with adjusted income
    taxable_amount = min(400000, max(0, adjusted_income - 400000))
    slab_tax['slab2_tax'] = round(taxable_amount * 0.05)
    tax += slab_tax['slab2_tax']
    
    taxable_amount = min(400000, max(0, adjusted_income - 800000))
    slab_tax['slab3_tax'] = round(taxable_amount * 0.10)
    tax += slab_tax['slab3_tax']
    
    taxable_amount = min(400000, max(0, adjusted_income - 1200000))
    slab_tax['slab4_tax'] = round(taxable_amount * 0.15)
    tax += slab_tax['slab4_tax']
    
    taxable_amount = min(400000, max(0, adjusted_income - 1600000))
    slab_tax['slab5_tax'] = round(taxable_amount * 0.20)
    tax += slab_tax['slab5_tax']
    
    taxable_amount = min(400000, max(0, adjusted_income - 2000000))
    slab_tax['slab6_tax'] = round(taxable_amount * 0.25)
    tax += slab_tax['slab6_tax']
    
    taxable_amount = max(0, adjusted_income - 2400000)
    slab_tax['slab7_tax'] = round(taxable_amount * 0.30)
    tax += slab_tax['slab7_tax']
    
    total_slab_tax = slab_tax['slab2_tax'] + slab_tax['slab3_tax'] + slab_tax['slab4_tax'] + slab_tax['slab5_tax'] + slab_tax['slab6_tax'] + slab_tax['slab7_tax']
    
    return tax, slab_tax, total_slab_tax

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
    # Calculate tax with slab breakdown and marginal benefit
    tax, slab_tax, total_slab_tax, marginal_benefit_applied, adjusted_income = calc_tax_new_regime(df['totalincome'].iloc[0])
    
    # Add education cess (4%)
    educess = round(0.04 * total_slab_tax)
    total_tax = total_slab_tax + educess
    
    # Calculate final payable/refundable tax
    payable_tax = round(total_tax - df['tax_paid'].iloc[0])
    refundable_tax = abs(payable_tax) if payable_tax < 0 else 0
    
    # Create a new dictionary with proper type conversion
    tax_data = pd.Series({
        'tax': total_slab_tax,
        'educess': educess,
        'total_tax': total_tax,
        'payable_tax': payable_tax if payable_tax > 0 else 0,
        'refundable_tax': refundable_tax,
        'marginal_benefit_applied': marginal_benefit_applied,
        'original_income': df['totalincome'].iloc[0],
        'adjusted_income': adjusted_income,
        'slab1_income': min(400000, df['totalincome'].iloc[0]),
        'slab2_income': min(400000, max(0, df['totalincome'].iloc[0] - 400000)),
        'slab3_income': min(400000, max(0, df['totalincome'].iloc[0] - 800000)),
        'slab4_income': min(400000, max(0, df['totalincome'].iloc[0] - 1200000)),
        'slab5_income': min(400000, max(0, df['totalincome'].iloc[0] - 1600000)),
        'slab6_income': min(400000, max(0, df['totalincome'].iloc[0] - 2000000)),
        'slab7_income': max(0, df['totalincome'].iloc[0] - 2400000)
    }, dtype='float64')

    # Apply rebate for income less than 12L
    if float(totalincome) < 1200000:
        tax_data['tax'] = 0
        tax_data['educess'] = 0
        tax_data['total_tax'] = 0
        tax_data['payable_tax'] = 0
        tax_data['refundable_tax'] = abs(df['tax_paid'].iloc[0])
        tax_data['marginal_benefit_applied'] = False
    else:
        # Tax values are already calculated with marginal benefit if applicable
        tax_data['tax'] = total_slab_tax
        tax_data['educess'] = round(0.04 * total_slab_tax)
        tax_data['total_tax'] = total_slab_tax + tax_data['educess']
        tax_data['payable_tax'] = max(0, tax_data['total_tax'] - df['tax_paid'].iloc[0])
        tax_data['refundable_tax'] = abs(min(0, tax_data['total_tax'] - df['tax_paid'].iloc[0]))

    # Add slab tax values
    for key, value in slab_tax.items():
        tax_data[key] = value
    
    # Convert to DataFrame and display with better formatting
    result_df = pd.concat([df.iloc[0], tax_data])
    
    # Display results in a more organized way
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Income Details")
        st.write(f"**Gross Salary:** ₹{gross_salary:,.2f}")
        st.write(f"**Other Salary:** ₹{other_salary:,.2f}")
        st.write(f"**Standard Deduction:** ₹{st_deduction:,.2f}")
        st.write(f"**Total Income:** ₹{totalincome:,.2f}")
        
        if marginal_benefit_applied:
            st.write(f"**Adjusted Income (after marginal benefit):** ₹{adjusted_income:,.2f}")
    
    with col2:
        st.subheader("Tax Calculation")
        st.write(f"**Tax before cess:** ₹{total_slab_tax:,.2f}")
        st.write(f"**Education Cess (4%):** ₹{educess:,.2f}")
        st.write(f"**Total Tax:** ₹{total_tax:,.2f}")
        st.write(f"**Tax Paid:** ₹{tax_paid:,.2f}")
        
        if payable_tax > 0:
            st.write(f"**Tax Payable:** ₹{payable_tax:,.2f}")
        if refundable_tax > 0:
            st.write(f"**Refundable Tax:** ₹{refundable_tax:,.2f}")
        
        if marginal_benefit_applied:
            st.success("✅ Marginal Tax Benefit Applied")
            savings = df['totalincome'].iloc[0] - adjusted_income
            st.write(f"**Tax Savings:** ₹{savings:,.2f}")
    
    # Display detailed slab breakdown
    st.subheader("Tax Slab Breakdown")
    slab_data = {
        'Slab': ['0-4L (0%)', '4L-8L (5%)', '8L-12L (10%)', '12L-16L (15%)', '16L-20L (20%)', '20L-24L (25%)', 'Above 24L (30%)'],
        'Taxable Amount': [
            f"₹{tax_data['slab1_income']:,.2f}",
            f"₹{tax_data['slab2_income']:,.2f}",
            f"₹{tax_data['slab3_income']:,.2f}",
            f"₹{tax_data['slab4_income']:,.2f}",
            f"₹{tax_data['slab5_income']:,.2f}",
            f"₹{tax_data['slab6_income']:,.2f}",
            f"₹{tax_data['slab7_income']:,.2f}"
        ],
        'Tax': [
            f"₹{tax_data['slab1_tax']:,.2f}",
            f"₹{tax_data['slab2_tax']:,.2f}",
            f"₹{tax_data['slab3_tax']:,.2f}",
            f"₹{tax_data['slab4_tax']:,.2f}",
            f"₹{tax_data['slab5_tax']:,.2f}",
            f"₹{tax_data['slab6_tax']:,.2f}",
            f"₹{tax_data['slab7_tax']:,.2f}"
        ]
    }
    st.table(pd.DataFrame(slab_data))
    
    # Generate document
    doc_data = result_df.to_dict()
    
    # Convert boolean to string for document template
    doc_data['marginal_benefit_applied'] = 'Yes' if marginal_benefit_applied else 'No'
    
    try:
        doc = DocxTemplate("taxnew.docx")
        doc.render(doc_data)
        
        # Download button
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.download_button(
            label="Download ITR Form",
            data=bio.getvalue(),
            file_name=f"{name}_new_itrform.docx",
            mime="docx",
            key='download_button'
        )
    except Exception as e:
        st.error(f"Error generating document: {str(e)}")
        st.info("Please ensure 'taxnew.docx' template file exists in the same directory.")

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
    slab_tax = {
        'slab1_tax': 0,  # 0-4L
        'slab2_tax': 0,  # 4L-8L
        'slab3_tax': 0,  # 8L-12L
        'slab4_tax': 0,  # 12L-16L
        'slab5_tax': 0,  # 16L-20L
        'slab6_tax': 0,  # 20L-24L
        'slab7_tax': 0,  # >24L
        'rebate': 0
    }
    
    # 5% slab (4L-8L)
    taxable_amount = min(400000, max(0, totalincome - 400000))
    slab_tax['slab2_tax'] = round(taxable_amount * 0.05)
    tax += slab_tax['slab2_tax']
    
    # 10% slab (8L-12L)
    taxable_amount = min(400000, max(0, totalincome - 800000))
    slab_tax['slab3_tax'] = round(taxable_amount * 0.10)
    tax += slab_tax['slab3_tax']
    
    # 15% slab (12L-16L)
    taxable_amount = min(400000, max(0, totalincome - 1200000))
    slab_tax['slab4_tax'] = round(taxable_amount * 0.15)
    tax += slab_tax['slab4_tax']
    
    # 20% slab (16L-20L)
    taxable_amount = min(400000, max(0, totalincome - 1600000))
    slab_tax['slab5_tax'] = round(taxable_amount * 0.20)
    tax += slab_tax['slab5_tax']
    
    # 25% slab (20L-24L)
    taxable_amount = min(400000, max(0, totalincome - 2000000))
    slab_tax['slab6_tax'] = round(taxable_amount * 0.25)
    tax += slab_tax['slab6_tax']
    
    # 30% slab (above 24L)
    taxable_amount = max(0, totalincome - 2400000)
    slab_tax['slab7_tax'] = round(taxable_amount * 0.30)
    tax += slab_tax['slab7_tax']
    total_slab_tax = slab_tax['slab2_tax'] + slab_tax['slab3_tax'] + slab_tax['slab4_tax'] +slab_tax['slab5_tax'] + slab_tax['slab6_tax'] + slab_tax['slab7_tax']
    
    return tax, slab_tax , total_slab_tax

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
    tax, slab_tax , total_slab_tax = calc_tax_new_regime(df['totalincome'].iloc[0])
    
    #st.write(total_slab_tax)
    # Add education cess (4%)
    educess = round(0.04 * total_slab_tax)
    total_tax = total_slab_tax + educess
    
    # Calculate final payable/refundable tax
    payable_tax = round(total_tax - df['tax_paid'].iloc[0])
    refundable_tax = abs(payable_tax) if payable_tax < 0 else 0
    
    # Create a new dictionary with proper type conversion
    tax_data = pd.Series({
        'tax': total_slab_tax,
        'educess': educess,
        'total_tax': total_tax,
        'payable_tax': payable_tax,
        'refundable_tax': refundable_tax,
        'slab1_income': min(400000, df['totalincome'].iloc[0]),
        'slab2_income': min(400000, max(0, df['totalincome'].iloc[0] - 400000)),
        'slab3_income': min(400000, max(0, df['totalincome'].iloc[0] - 800000)),
        'slab4_income': min(400000, max(0, df['totalincome'].iloc[0] - 1200000)),
        'slab5_income': min(400000, max(0, df['totalincome'].iloc[0] - 1600000)),
        'slab6_income': min(400000, max(0, df['totalincome'].iloc[0] - 2000000)),
        'slab7_income': max(0, df['totalincome'].iloc[0] - 2400000)
    }, dtype='float64')

    if float(totalincome) < 1200000 :
        tax_data['tax'] = 0
        tax_data['educess'] = 0
        tax_data['total_tax'] = 0
        tax_data['payable_tax'] = 0
        tax_data['refundable_tax'] = abs(df['tax_paid'].iloc[0])
    else :
        
        tax_data['tax'] = total_slab_tax
        tax_data['educess'] = round(0.04 * total_slab_tax)
        tax_data['total_tax'] = total_slab_tax + tax_data['educess']
        tax_data['payable_tax'] = tax_data['total_tax'] - df['tax_paid'].iloc[0]
        tax_data['refundable_tax'] = abs(tax_data['payable_tax']) if tax_data['payable_tax'] < 0 else 0
    



    # Add slab tax values
    for key, value in slab_tax.items():
        tax_data[key] = value
    
    # Convert to DataFrame and display
    result_df = pd.concat([df.iloc[0], tax_data])
    st.write(result_df.to_frame().T)
    
    # Generate document
    doc_data = result_df.to_dict()
    doc = DocxTemplate("taxnew.docx")
    doc.render(doc_data)
    
    # Download button
    bio = io.BytesIO()
    doc.save(bio)
    if doc:
        st.download_button(
            label="Download ITR Form",
            data=bio.getvalue(),
            file_name=f"{name}_new_itrform.docx",
            mime="docx"
        )
