import pandas as pd
import numpy as np
import streamlit as st
import io
import datetime
from docxtpl import DocxTemplate

# Page configuration
st.set_page_config(layout="wide")
st.title('ITR NEW TAX REGIME CALCULATION 2026-27')

# Initialize session state
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

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

# Create input form in columns for better layout
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Basic Details")
    year = st.selectbox('Select Year', ['2025-26', '2026-27'], key='year_select')
    assesment_year = st.selectbox('Select Assessment Year', ['2026-27', '2027-28'], key='assesment_year_select')
    pan = st.text_input('PAN', key='pan_input').upper()
    eid = st.text_input('Employee ID', key='eid_input')
    name = st.text_input('Name', key='name_input').upper()

with col2:
    st.subheader("Date & Place")
    dt = datetime.datetime.now().date()
    place = st.text_input('Place', key='place_input').upper()
    ahc = st.text_input('AHC', key='ahc_input').upper()
    district = st.text_input('District', key='district_input').upper()

with col3:
    st.subheader("Financial Details")
    gross_salary = st.number_input('GROSS SALARY (₹)', value=0, key='gross_salary_input', step=1000)
    other_salary = st.number_input('OTHER SALARY (₹)', value=0, key='other_salary_input', step=1000)
    st_deduction = st.number_input('STANDARD DEDUCTION (₹)', value=75000, key='std_deduction_input', step=1000)
    tax_paid = st.number_input('TAX PAID (TDS/TCS) (₹)', value=0, key='tax_paid_input', step=100)

# Calculate derived values
gross_total = gross_salary + other_salary
total_income = gross_total - st_deduction

def calculate_slab_wise_income(income):
    """Calculate income in each slab"""
    return {
        'slab1_income': min(400000, income),  # 0-4L
        'slab2_income': min(400000, max(0, income - 400000)),  # 4L-8L
        'slab3_income': min(400000, max(0, income - 800000)),  # 8L-12L
        'slab4_income': min(400000, max(0, income - 1200000)),  # 12L-16L
        'slab5_income': min(400000, max(0, income - 1600000)),  # 16L-20L
        'slab6_income': min(400000, max(0, income - 2000000)),  # 20L-24L
        'slab7_income': max(0, income - 2400000)  # Above 24L
    }

def calculate_tax_from_income(income):
    """Calculate tax based on income slabs"""
    slab_tax = {
        'slab1_tax': 0,  # 0-4L (0%)
        'slab2_tax': 0,  # 4L-8L (5%)
        'slab3_tax': 0,  # 8L-12L (10%)
        'slab4_tax': 0,  # 12L-16L (15%)
        'slab5_tax': 0,  # 16L-20L (20%)
        'slab6_tax': 0,  # 20L-24L (25%)
        'slab7_tax': 0,  # >24L (30%)
        'rebate': 0
    }
    
    # Calculate tax for each slab
    slab_tax['slab2_tax'] = round(min(400000, max(0, income - 400000)) * 0.05)
    slab_tax['slab3_tax'] = round(min(400000, max(0, income - 800000)) * 0.10)
    slab_tax['slab4_tax'] = round(min(400000, max(0, income - 1200000)) * 0.15)
    slab_tax['slab5_tax'] = round(min(400000, max(0, income - 1600000)) * 0.20)
    slab_tax['slab6_tax'] = round(min(400000, max(0, income - 2000000)) * 0.25)
    slab_tax['slab7_tax'] = round(max(0, income - 2400000) * 0.30)
    
    total_slab_tax = sum([
        slab_tax['slab2_tax'], slab_tax['slab3_tax'], slab_tax['slab4_tax'],
        slab_tax['slab5_tax'], slab_tax['slab6_tax'], slab_tax['slab7_tax']
    ])
    
    return slab_tax, total_slab_tax

def apply_marginal_benefit(income, tax_amount):
    """
    Apply marginal tax benefit condition:
    If tax calculated is greater than (income - 1200000), 
    then taxable income becomes min(income - 1200000, income)
    """
    marginal_benefit_applied = False
    adjusted_income = income
    adjusted_tax = tax_amount
    adjusted_slab_tax = None
    
    # Check if tax > (income - 1200000) and income > 1200000
    if tax_amount > (income - 1200000) and income > 1200000:
        marginal_benefit_applied = True
        adjusted_income = max(0, income - 1200000)  # Income reduces by 12L
        
        # Recalculate tax with adjusted income
        adjusted_slab_tax, adjusted_tax = calculate_tax_from_income(adjusted_income)
    
    return marginal_benefit_applied, adjusted_income, adjusted_tax, adjusted_slab_tax

def calculate_final_tax(income):
    """
    Main function to calculate final tax with all conditions
    Condition: When taxable income after standard deduction is less than 12,00,000 then no tax
    """
    # Check if income is less than 12L (no tax condition)
    if income < 1200000:
        return {
            'tax': 0,
            'educess': 0,
            'total_tax': 0,
            'payable_tax': 0,
            'refundable_tax': tax_paid,  # Full refund if tax paid
            'marginal_benefit_applied': False,
            'original_income': income,
            'adjusted_income': income,
            'rebate_applied': True,
            'slab_tax': {
                'slab1_tax': 0, 'slab2_tax': 0, 'slab3_tax': 0,
                'slab4_tax': 0, 'slab5_tax': 0, 'slab6_tax': 0,
                'slab7_tax': 0, 'rebate': income
            }
        }
    
    # Calculate initial tax
    slab_tax, total_slab_tax = calculate_tax_from_income(income)
    
    # Apply marginal benefit if applicable
    marginal_benefit_applied, adjusted_income, adjusted_tax, adjusted_slab_tax = apply_marginal_benefit(income, total_slab_tax)
    
    # Use adjusted values if marginal benefit applied
    if marginal_benefit_applied:
        final_slab_tax = adjusted_slab_tax
        final_tax = adjusted_tax
    else:
        final_slab_tax = slab_tax
        final_tax = total_slab_tax
    
    # Calculate education cess (4%)
    educess = round(0.04 * final_tax)
    total_tax_with_cess = final_tax + educess
    
    # Calculate payable/refundable tax
    if tax_paid > total_tax_with_cess:
        payable_tax = 0
        refundable_tax = tax_paid - total_tax_with_cess
    else:
        payable_tax = total_tax_with_cess - tax_paid
        refundable_tax = 0
    
    return {
        'tax': final_tax,
        'educess': educess,
        'total_tax': total_tax_with_cess,
        'payable_tax': payable_tax,
        'refundable_tax': refundable_tax,
        'marginal_benefit_applied': marginal_benefit_applied,
        'original_income': income,
        'adjusted_income': adjusted_income if marginal_benefit_applied else income,
        'rebate_applied': income < 1200000,
        'slab_tax': final_slab_tax,
        'slab_income': calculate_slab_wise_income(income)
    }

# Display summary of inputs
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Gross Total:** ₹{gross_total:,.2f}")
with col2:
    st.info(f"**Standard Deduction:** ₹{st_deduction:,.2f}")
with col3:
    st.info(f"**Taxable Income:** ₹{total_income:,.2f}")

# Calculate button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    calculate_button = st.button('📊 CALCULATE TAX', key='calculate_button', use_container_width=True)

if calculate_button:
    st.session_state.calculation_done = True
    st.session_state.show_results = True

# Display results if calculation is done
if st.session_state.show_results:
    # Validate inputs
    if not name or not pan:
        st.error("⚠️ Please fill in all required fields (Name and PAN)")
    else:
        # Calculate tax
        result = calculate_final_tax(total_income)
        
        st.divider()
        st.header("📋 TAX CALCULATION REPORT")
        
        # Display main results in metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if result['rebate_applied']:
                st.metric("Taxable Income", f"₹{total_income:,.2f}", 
                         delta="Below 12L → No Tax", delta_color="off")
            else:
                st.metric("Taxable Income", f"₹{total_income:,.2f}")
        
        with col2:
            st.metric("Tax Before Cess", f"₹{result['tax']:,.2f}")
        
        with col3:
            st.metric("Education Cess (4%)", f"₹{result['educess']:,.2f}")
        
        with col4:
            st.metric("Total Tax", f"₹{result['total_tax']:,.2f}")
        
        # Display tax status
        if result['rebate_applied']:
            st.success("✅ **REBATE APPLIED:** Income is below ₹12,00,000 - NO TAX PAYABLE")
        
        if result['marginal_benefit_applied']:
            st.info(f"ℹ️ **MARGINAL TAX BENEFIT APPLIED:** Income reduced from ₹{result['original_income']:,.2f} to ₹{result['adjusted_income']:,.2f}")
            st.write(f"**Tax Savings:** ₹{result['original_income'] - result['adjusted_income']:,.2f}")
        
        st.divider()
        
        # Display tax payment summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Tax Payment Summary")
            tax_summary_data = {
                'Description': ['Tax Paid (TDS/TCS)', 'Total Tax Payable', 'Status'],
                'Amount': [
                    f"₹{tax_paid:,.2f}",
                    f"₹{result['total_tax']:,.2f}",
                    'TAX PAYABLE' if result['payable_tax'] > 0 else 'TAX REFUNDABLE' if result['refundable_tax'] > 0 else 'TAX BALANCED'
                ]
            }
            st.dataframe(pd.DataFrame(tax_summary_data), use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("💵 Final Amount")
            if result['payable_tax'] > 0:
                st.error(f"**TAX PAYABLE:** ₹{result['payable_tax']:,.2f}")
            elif result['refundable_tax'] > 0:
                st.success(f"**TAX REFUNDABLE:** ₹{result['refundable_tax']:,.2f}")
            else:
                st.info("**TAX BALANCED:** No payment or refund")
        
        st.divider()
        
        # Display slab-wise breakdown
        st.subheader("📊 Tax Slab-wise Breakdown")
        
        slab_data = []
        slabs = [
            ('0 - ₹4,00,000', '0%', result['slab_income']['slab1_income'], result['slab_tax']['slab1_tax']),
            ('₹4,00,001 - ₹8,00,000', '5%', result['slab_income']['slab2_income'], result['slab_tax']['slab2_tax']),
            ('₹8,00,001 - ₹12,00,000', '10%', result['slab_income']['slab3_income'], result['slab_tax']['slab3_tax']),
            ('₹12,00,001 - ₹16,00,000', '15%', result['slab_income']['slab4_income'], result['slab_tax']['slab4_tax']),
            ('₹16,00,001 - ₹20,00,000', '20%', result['slab_income']['slab5_income'], result['slab_tax']['slab5_tax']),
            ('₹20,00,001 - ₹24,00,000', '25%', result['slab_income']['slab6_income'], result['slab_tax']['slab6_tax']),
            ('Above ₹24,00,000', '30%', result['slab_income']['slab7_income'], result['slab_tax']['slab7_tax'])
        ]
        
        for slab, rate, amount, tax in slabs:
            if amount > 0 or tax > 0:
                slab_data.append({
                    'Income Slab': slab,
                    'Rate': rate,
                    'Taxable Amount': f"₹{amount:,.2f}",
                    'Tax': f"₹{tax:,.2f}"
                })
        
        if slab_data:
            st.table(pd.DataFrame(slab_data))
        
        # Prepare data for document generation
        doc_data = {
            'year': str(year),
            'assesment_year': str(assesment_year),
            'pan': str(pan),
            'eid': str(eid),
            'name': str(name),
            'tax_paid': float(tax_paid),
            'gross_salary': float(gross_salary),
            'other_salary': float(other_salary),
            'st_deduction': float(st_deduction),
            'gross_total': float(gross_total),
            'totalincome': float(total_income),
            'tax': float(result['tax']),
            'educess': float(result['educess']),
            'total_tax': float(result['total_tax']),
            'payable_tax': float(result['payable_tax']),
            'refundable_tax': float(result['refundable_tax']),
            'dt': str(dt),
            'place': str(place),
            'ahc': str(ahc),
            'district': str(district),
            'marginal_benefit_applied': 'Yes' if result['marginal_benefit_applied'] else 'No',
            'rebate_applied': 'Yes' if result['rebate_applied'] else 'No',
            'slab1_income': result['slab_income']['slab1_income'],
            'slab2_income': result['slab_income']['slab2_income'],
            'slab3_income': result['slab_income']['slab3_income'],
            'slab4_income': result['slab_income']['slab4_income'],
            'slab5_income': result['slab_income']['slab5_income'],
            'slab6_income': result['slab_income']['slab6_income'],
            'slab7_income': result['slab_income']['slab7_income'],
            'slab1_tax': result['slab_tax']['slab1_tax'],
            'slab2_tax': result['slab_tax']['slab2_tax'],
            'slab3_tax': result['slab_tax']['slab3_tax'],
            'slab4_tax': result['slab_tax']['slab4_tax'],
            'slab5_tax': result['slab_tax']['slab5_tax'],
            'slab6_tax': result['slab_tax']['slab6_tax'],
            'slab7_tax': result['slab_tax']['slab7_tax']
        }
        
        st.divider()
        
        # Document download section
        st.subheader("📄 Generate ITR Document")
        
        try:
            doc = DocxTemplate("taxnew.docx")
            doc.render(doc_data)
            
            # Download button
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="📥 DOWNLOAD ITR FORM",
                    data=bio.getvalue(),
                    file_name=f"{name}_ITR_NewRegime_{year}.docx",
                    mime="docx",
                    key='download_button',
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"⚠️ Error generating document: {str(e)}")
            st.info("Please ensure 'taxnew.docx' template file exists in the same directory.")
        
        # Reset button
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button('🔄 NEW CALCULATION', key='reset_button', use_container_width=True):
                st.session_state.calculation_done = False
                st.session_state.show_results = False
                st.rerun()
