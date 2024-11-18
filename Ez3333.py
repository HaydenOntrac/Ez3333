#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import io

# Define your CSV file paths here (use raw strings or double backslashes)
swl_csv = 'excavator_swl.csv'  # Ensure this file exists
bucket_csv = 'bucket_data.csv'  # Make sure this file exists
bhc_bucket_csv = 'bhc_bucket_data.csv'  # Make sure this file exists
dump_truck_csv = 'dump_trucks.csv'  # Path to dump truck CSV

# Function to generate Excel file
def generate_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Productivity Study')
    # Return the Excel content as bytes
    return output.getvalue()

# Load datasets
def load_bucket_data(bucket_csv):
    return pd.read_csv(bucket_csv)

def load_bhc_bucket_data(bhc_bucket_csv):
    return pd.read_csv(bhc_bucket_csv)

def load_dump_truck_data(dump_truck_csv):
    return pd.read_csv(dump_truck_csv)

def load_excavator_swl_data(swl_csv):
    swl_data = pd.read_csv(swl_csv)
    swl_data['boom_length'] = pd.to_numeric(swl_data['boom_length'], errors='coerce')
    swl_data['arm_length'] = pd.to_numeric(swl_data['arm_length'], errors='coerce')
    swl_data['CWT'] = pd.to_numeric(swl_data['CWT'], errors='coerce')
    swl_data['shoe_width'] = pd.to_numeric(swl_data['shoe_width'], errors='coerce')
    swl_data['reach'] = pd.to_numeric(swl_data['reach'], errors='coerce')
    swl_data['class'] = pd.to_numeric(swl_data['class'], errors='coerce')
    return swl_data

# Load the data
dump_truck_data = load_dump_truck_data(dump_truck_csv)
swl_data = load_excavator_swl_data(swl_csv)

#APP
# Main Streamlit App UI
def app():
    st.write("Copyright © ONTRAC Group Pty Ltd 2024.")

# Streamlit UI
st.title("ONTRAC XMOR® Bucket Solution\n\n")
st.title("Excavator Selection")

# Step 1: Select Excavator Make
excavator_make = st.selectbox("Select Excavator Make", swl_data['make'].unique())

# Step 2: Filter by selected make and select Excavator Model
filtered_data_make = swl_data[swl_data['make'] == excavator_make]
excavator_model = st.selectbox("Select Excavator Model", filtered_data_make['model'].unique())

# Step 3: Filter by selected model and select Boom Length
filtered_data_model = filtered_data_make[filtered_data_make['model'] == excavator_model]
boom_length = st.selectbox("Select Boom Length (m)", filtered_data_model['boom_length'].unique())

# Step 4: Filter further by selected boom length and select Arm Length
filtered_data_boom = filtered_data_model[filtered_data_model['boom_length'] == boom_length]
arm_length = st.selectbox("Select Arm Length (m)", filtered_data_boom['arm_length'].unique())

# Step 5: Filter further by selected arm length and select Counterweight
filtered_data_arm = filtered_data_boom[filtered_data_boom['arm_length'] == arm_length]
cwt = st.selectbox("Select Counterweight (CWT in kg)", filtered_data_arm['CWT'].unique())

# Step 6: Filter further by selected counterweight and select Shoe Width
filtered_data_cwt = filtered_data_arm[filtered_data_arm['CWT'] == cwt]
shoe_width = st.selectbox("Select Shoe Width (mm)", filtered_data_cwt['shoe_width'].unique())

# Step 7: Filter further by selected shoe width and select Reach
filtered_data_shoe = filtered_data_cwt[filtered_data_cwt['shoe_width'] == shoe_width]
reach = st.selectbox("Select Reach (m)", filtered_data_shoe['reach'].unique())

quick_hitch = st.checkbox("My Machine Uses a Quick Hitch")
quick_hitch_weight = st.number_input("Quick Hitch Weight (kg)", min_value=0.0) if quick_hitch else 0

material_density = st.number_input("Material Density (kg/m³)     e.g. 1500", min_value=0.0)

# Checkbox for BHC buckets
select_bhc = st.checkbox("Select from BHC buckets only (Heavy Duty)")

# Function to calculate SWL match
def find_matching_swl(user_data):
    matching_excavator = swl_data[
        (swl_data['make'] == user_data['make']) &
        (swl_data['model'] == user_data['model']) &
        (swl_data['CWT'] == user_data['cwt']) &
        (swl_data['shoe_width'] == user_data['shoe_width']) &
        (swl_data['reach'] == user_data['reach']) &
        (swl_data['boom_length'] == user_data['boom_length']) &
        (swl_data['arm_length'] == user_data['arm_length'])
    ]
    if matching_excavator.empty:
        return None
    swl = matching_excavator.iloc[0]['swl']
    return swl

# Function to calculate bucket load
def calculate_bucket_load(bucket_size, material_density):
    return bucket_size * material_density

def select_optimal_bucket(user_data, bucket_data, swl):
    optimal_bucket = None
    highest_bucket_size = 0

    selected_model = user_data['model']
    excavator_class = swl_data[swl_data['model'] == selected_model]['class'].iloc[0]

    for index, bucket in bucket_data.iterrows():
        if bucket['class'] > excavator_class + 10:
            continue

        bucket_load = calculate_bucket_load(bucket['bucket_size'], user_data['material_density'])
        total_bucket_weight = user_data['quick_hitch_weight'] + bucket_load + bucket['bucket_weight']

        if total_bucket_weight <= swl and bucket['bucket_size'] > highest_bucket_size:
            highest_bucket_size = bucket['bucket_size']
            optimal_bucket = {
                'bucket_name': bucket['bucket_name'],
                'bucket_size': highest_bucket_size,
                'bucket_weight': bucket['bucket_weight'],
                'total_bucket_weight': total_bucket_weight
            }

    return optimal_bucket

    # Get user input data
user_data = {
    'make': excavator_make,
    'model': excavator_model,
    'boom_length': boom_length,
    'arm_length': arm_length,
    'cwt': cwt,
    'shoe_width': shoe_width,
    'reach': reach,
    'material_density': material_density,
    'quick_hitch_weight': quick_hitch_weight,
}

# Find matching SWL and optimal bucket
# Add a "Calculate" button
calculate_button = st.button("Calculate")

# Run calculations only when the button is pressed
if calculate_button:

    swl = find_matching_swl(user_data)
    if swl:
        # Load selected bucket data
        selected_bucket_csv = bhc_bucket_csv if select_bhc else bucket_csv
        bucket_data = load_bucket_data(selected_bucket_csv)
    
        optimal_bucket = select_optimal_bucket(user_data, bucket_data, swl)
    
        if optimal_bucket:
            st.success(f"Good News! Your machine can upgrade to an XMOR® bucket!
            st.success(f"Your ONTRAC XMOR® Bucket Solution is the: {optimal_bucket['bucket_name']} ({optimal_bucket['bucket_size']} m³)")
            st.write(f"Total Suspended Load: {optimal_bucket['total_bucket_weight']} kg")
            st.write(f"{user_data['make']} {user_data['model']} Safe Working Load at {user_data['reach']}m: {swl} kg")

            # Show table
            new_capacity = optimal_bucket['bucket_size']
            new_payload = calculate_bucket_load(new_capacity, user_data['material_density'])
    
            # Total suspended load
            new_total_load = optimal_bucket['total_bucket_weight']  # Corrected variable

        else:
            st.write("No suitable bucket found within SWL limits.")
    else:
        st.write("No matching excavator configuration found!")
else:
    st.write("Please select options and press 'Calculate' to proceed.")
    

# Run the Streamlit app
if __name__ == '__main__':
    app()
