import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
import io


def calculate_time_intervals(df):
    """Calculates the time intervals and total working hours for each user.

    Args:
        df (pandas.DataFrame): The input DataFrame containing user data.

    Returns:
        pandas.DataFrame: The DataFrame with added columns:
            - 'Interval': Time difference between scans in seconds.
            - 'Total Working Hours': Calculated working hours based on assumptions.
    """
    df['Time'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df.sort_values(by=['EMPLOYEE ID', 'Time'], inplace=True)
    df['Interval'] = df.groupby('EMPLOYEE ID')['Time'].diff().dt.total_seconds()

    # Assuming first and last entries represent work start and end times
    if len(df) >= 2:
       df['Total Working Hours'] = (df.iloc[-1]['Time'] - df.iloc[0]['Time']).total_seconds() / 3600
    else:
        df['Total Working Hours'] = 0

    return df.reset_index(drop=True)


def generate_excel_download_link(df):
    """Generates a downloadable Excel link for the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame to download.
    """
    output_name = 'data_download.xlsx'

    with pd.ExcelWriter(output_name, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=True)

    with open(output_name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{output_name}">Download Excel file</a>'
    st.markdown(href, unsafe_allow_html=True)


def generate_html_download_link(fig):
    """Generates a downloadable HTML link for the Plotly figure.

    Args:
        fig (plotly.graph_objects.Figure): The Plotly figure to download.
    """
    towrite = io.BytesIO()
    fig.write_html(towrite, include_plotlyjs='cdn')
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="plot.html">Download plot as HTML</a>'
    st.markdown(href, unsafe_allow_html=True)


# Streamlit app setup and file processing
uploaded_file = st.file_uploader('Choose a XLSX or XLSM file', type=['xlsx', 'xlsm'])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Error reading the file: {e}")
        st.stop()

    df = calculate_time_intervals(df.copy())

    # Display data
    st.subheader('Employee Time Spent in Cafeteria')
    st.dataframe(df)

    df['Interval_in_minutes'] = df['Interval'] / 60

    # Histogram for time spent in cafeteria
    fig_hist = px.histogram(
        df, x='Interval', title='Distribution of Time Spent in Cafeteria (seconds)',
        color='EMPLOYEE ID', nbins=20,  # Adjust the number of bins as needed
    )
    fig_hist.update_layout(xaxis_title='Time Spent in Cafeteria (seconds)')
    st.plotly_chart(fig_hist)

    # Line plot for time spent in cafeteria over time
    fig_line = px.line(
        df, x='Time', y='Interval_in_minutes', title='Time Spent in Cafeteria Over Time (minutes)'
    )
    st.plotly_chart(fig_line)

    # Bar plot for average time spent in cafeteria by employee
    fig_bar = px.bar(
        df.groupby('EMPLOYEE ID')['Interval_in_minutes'].mean().reset_index(),
        x='EMPLOYEE ID', y='Interval_in_minutes', title='Average Time Spent in Cafeteria by Employee (minutes)'
    )
    st.plotly_chart(fig_bar)

    # Additional calculations (assuming 8-hour workday)
    assumed_working_hours = 8 * 60 * 60  # 8 hours in seconds

    # Filter entries with total working hours
    df_filtered = df[df['Total Working Hours'] > 0]

    

    if len(df_filtered) > 0:
        average_cafetaria_time = df_filtered['Interval'].mean()
        percentage_time_in_cafetaria = (average_cafetaria_time / assumed_working_hours) * 100

        st.subheader('Additional Statistics:')
        st.write('Average Time Spent in Cafeteria:', average_cafetaria_time, 'seconds')
        st.write('Percentage of Time Spent in Cafeteria:', percentage_time_in_cafetaria, '%')

        # Download links
        generate_excel_download_link(df)
       
