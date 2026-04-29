import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Sales & Revenue Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f77b4;
        font-weight: 700;
    }
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("📊 Sales & Revenue Analysis Dashboard")
st.markdown("**Comprehensive business intelligence and analytics platform**")
st.markdown("---")

# Function to load data
@st.cache_data
def load_data(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format!")
            return None
        
        # Convert date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# Sidebar - Data Import
st.sidebar.header("📁 Data Import")
uploaded_file = st.sidebar.file_uploader(
    "Upload your sales data (CSV/Excel)", 
    type=['csv', 'xlsx', 'xls']
)

# Load data
df = None
if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        st.sidebar.success("✅ File uploaded successfully!")
        st.sidebar.markdown(f"**Records loaded:** {len(df):,}")
else:
    st.sidebar.warning("⚠️ Please upload a file to get started")

# Check if data is loaded
if df is not None:
    # Ensure Date column is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sidebar - Filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Category filter
    categories = ['All'] + sorted(df['Category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Select Category", categories)
    
    # Region filter
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Select Region", regions)
    
    # Product filter
    if selected_category != 'All':
        products = ['All'] + sorted(df[df['Category'] == selected_category]['Product'].unique().tolist())
    else:
        products = ['All'] + sorted(df['Product'].unique().tolist())
    selected_product = st.sidebar.selectbox("Select Product", products)
    
    # Apply filters
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['Date'].dt.date >= start_date) & 
            (filtered_df['Date'].dt.date <= end_date)
        ]
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['Region'] == selected_region]
    
    if selected_product != 'All':
        filtered_df = filtered_df[filtered_df['Product'] == selected_product]
    
    # Show warning if no data after filtering
    if len(filtered_df) == 0:
        st.warning("⚠️ No data matches the current filter criteria. Please adjust your filters.")
        st.stop()
    
    # Reset filters button
    if st.sidebar.button("🔄 Reset All Filters"):
        st.rerun()
    
    # Download filtered data
    st.sidebar.markdown("---")
    st.sidebar.header("💾 Export Data")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=csv,
        file_name=f'sales_data_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
    
    # Main Dashboard
    # KPIs
    st.header("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = filtered_df['Revenue'].sum()
    total_profit = filtered_df['Profit'].sum() if 'Profit' in filtered_df.columns else 0
    total_orders = len(filtered_df)
    avg_order_value = filtered_df['Revenue'].mean()
    
    # Calculate growth rates (comparing first half vs second half)
    filtered_df_sorted = filtered_df.sort_values('Date')
    mid_point = len(filtered_df_sorted) // 2
    
    if mid_point > 0:
        first_half = filtered_df_sorted.iloc[:mid_point]
        second_half = filtered_df_sorted.iloc[mid_point:]
        
        revenue_growth = ((second_half['Revenue'].sum() - first_half['Revenue'].sum()) / 
                         first_half['Revenue'].sum() * 100) if first_half['Revenue'].sum() > 0 else 0
    else:
        first_half = pd.DataFrame()
        second_half = pd.DataFrame()
        revenue_growth = 0
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"${total_revenue:,.2f}",
            delta=f"{revenue_growth:.1f}% growth"
        )
    
    with col2:
        st.metric(
            label="📊 Total Profit",
            value=f"${total_profit:,.2f}",
            delta=f"{(total_profit/total_revenue*100):.1f}% margin" if total_revenue > 0 else "0%"
        )
    
    with col3:
        st.metric(
            label="🛒 Total Orders",
            value=f"{total_orders:,}",
            delta=f"{len(second_half) - len(first_half)} vs prev period" if len(first_half) > 0 else "N/A"
        )
    
    with col4:
        st.metric(
            label="💳 Avg Order Value",
            value=f"${avg_order_value:,.2f}",
            delta=f"${avg_order_value - df['Revenue'].mean():.2f}"
        )
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Revenue Trend Over Time")
        
        # Group by date
        daily_revenue = filtered_df.groupby(filtered_df['Date'].dt.date)['Revenue'].sum().reset_index()
        daily_revenue.columns = ['Date', 'Revenue']
        
        if len(daily_revenue) > 0:
            fig_trend = px.line(
                daily_revenue,
                x='Date',
                y='Revenue',
                title='Daily Revenue Trend',
                markers=True
            )
            fig_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
                hovermode='x unified',
                plot_bgcolor='white'
            )
            fig_trend.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No data available for the selected filters")
    
    with col2:
        st.subheader("🏷️ Sales by Category")
        
        category_sales = filtered_df.groupby('Category')['Revenue'].sum().reset_index()
        category_sales = category_sales.sort_values('Revenue', ascending=False)
        
        if len(category_sales) > 0:
            fig_category = px.pie(
                category_sales,
                values='Revenue',
                names='Category',
                title='Revenue Distribution by Category',
                hole=0.4
            )
            fig_category.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_category, use_container_width=True)
        else:
            st.info("No data available for the selected filters")
    
    # Second row of charts
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏆 Top 10 Products by Revenue")
        
        top_products = filtered_df.groupby('Product')['Revenue'].sum().reset_index()
        top_products = top_products.sort_values('Revenue', ascending=False).head(10)
        
        if len(top_products) > 0:
            fig_products = px.bar(
                top_products,
                x='Revenue',
                y='Product',
                orientation='h',
                title='Top Performing Products',
                color='Revenue',
                color_continuous_scale='Blues'
            )
            fig_products.update_layout(
                xaxis_title="Revenue ($)",
                yaxis_title="Product",
                showlegend=False,
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_products, use_container_width=True)
        else:
            st.info("No data available for the selected filters")
    
    with col4:
        st.subheader("🗺️ Sales by Region")
        
        region_sales = filtered_df.groupby('Region')['Revenue'].sum().reset_index()
        
        if len(region_sales) > 0:
            fig_region = px.bar(
                region_sales,
                x='Region',
                y='Revenue',
                title='Revenue by Region',
                color='Revenue',
                color_continuous_scale='Viridis'
            )
            fig_region.update_layout(
                xaxis_title="Region",
                yaxis_title="Revenue ($)",
                showlegend=False,
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.info("No data available for the selected filters")
    
    st.markdown("---")
    
    # Additional Analytics
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("📊 Revenue vs Profit Analysis")
        
        if 'Profit' in filtered_df.columns and len(filtered_df) > 0:
            monthly_data = filtered_df.copy()
            monthly_data['Month'] = monthly_data['Date'].dt.to_period('M').astype(str)
            monthly_analysis = monthly_data.groupby('Month').agg({
                'Revenue': 'sum',
                'Profit': 'sum'
            }).reset_index()
            
            fig_rev_profit = go.Figure()
            fig_rev_profit.add_trace(go.Bar(
                x=monthly_analysis['Month'],
                y=monthly_analysis['Revenue'],
                name='Revenue',
                marker_color='lightblue'
            ))
            fig_rev_profit.add_trace(go.Bar(
                x=monthly_analysis['Month'],
                y=monthly_analysis['Profit'],
                name='Profit',
                marker_color='darkblue'
            ))
            
            fig_rev_profit.update_layout(
                title='Monthly Revenue vs Profit',
                xaxis_title='Month',
                yaxis_title='Amount ($)',
                barmode='group',
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_rev_profit, use_container_width=True)
        else:
            st.info("Profit data not available in the uploaded file")
    
    with col6:
        st.subheader("📦 Quantity Sold by Category")
        
        quantity_by_category = filtered_df.groupby('Category')['Quantity'].sum().reset_index()
        quantity_by_category = quantity_by_category.sort_values('Quantity', ascending=False)
        
        if len(quantity_by_category) > 0:
            fig_quantity = px.bar(
                quantity_by_category,
                x='Category',
                y='Quantity',
                title='Total Quantity Sold',
                color='Quantity',
                color_continuous_scale='Oranges'
            )
            fig_quantity.update_layout(
                xaxis_title="Category",
                yaxis_title="Quantity",
                showlegend=False,
                plot_bgcolor='white'
            )
            st.plotly_chart(fig_quantity, use_container_width=True)
        else:
            st.info("No data available for the selected filters")
    
    st.markdown("---")
    
    # Data Table
    st.header("📋 Detailed Sales Data")
    
    if len(filtered_df) > 0:
        # Display options
        col1, col2, col3 = st.columns(3)
        with col1:
            rows_to_show = st.selectbox("Rows to display", [10, 25, 50, 100, 'All'])
        with col2:
            sort_column = st.selectbox("Sort by", filtered_df.columns.tolist())
        with col3:
            sort_order = st.selectbox("Order", ['Descending', 'Ascending'])
        
        # Sort data
        display_df = filtered_df.sort_values(
            by=sort_column,
            ascending=(sort_order == 'Ascending')
        )
        
        # Show data
        if rows_to_show == 'All':
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.dataframe(display_df.head(rows_to_show), use_container_width=True, height=400)
    else:
        st.info("No data available to display")
    
    # Summary Statistics
    st.markdown("---")
    st.header("📊 Summary Statistics")
    
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Numerical Summary")
            numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
            st.dataframe(
                filtered_df[numeric_cols].describe(),
                use_container_width=True
            )
        
        with col2:
            st.subheader("Categorical Summary")
            summary_data = {
                'Metric': ['Unique Products', 'Unique Categories', 'Unique Regions', 'Date Range'],
                'Value': [
                    filtered_df['Product'].nunique(),
                    filtered_df['Category'].nunique(),
                    filtered_df['Region'].nunique(),
                    f"{filtered_df['Date'].min().date()} to {filtered_df['Date'].max().date()}"
                ]
            }
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
    else:
        st.info("No data available for statistics")
    
    # Insights Section
    st.markdown("---")
    st.header("💡 Key Insights")
    
    if len(filtered_df) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                category_revenue = filtered_df.groupby('Category')['Revenue'].sum()
                if len(category_revenue) > 0:
                    best_category = category_revenue.idxmax()
                    best_category_revenue = category_revenue.max()
                    st.info(f"**Best Performing Category:** {best_category}\n\n**Revenue:** ${best_category_revenue:,.2f}")
                else:
                    st.info("**Best Performing Category:** No data available")
            except Exception as e:
                st.info("**Best Performing Category:** No data available")
        
        with col2:
            try:
                product_revenue = filtered_df.groupby('Product')['Revenue'].sum()
                if len(product_revenue) > 0:
                    best_product = product_revenue.idxmax()
                    best_product_revenue = product_revenue.max()
                    st.success(f"**Top Product:** {best_product}\n\n**Revenue:** ${best_product_revenue:,.2f}")
                else:
                    st.success("**Top Product:** No data available")
            except Exception as e:
                st.success("**Top Product:** No data available")
        
        with col3:
            try:
                region_revenue = filtered_df.groupby('Region')['Revenue'].sum()
                if len(region_revenue) > 0:
                    best_region = region_revenue.idxmax()
                    best_region_revenue = region_revenue.max()
                    st.warning(f"**Leading Region:** {best_region}\n\n**Revenue:** ${best_region_revenue:,.2f}")
                else:
                    st.warning("**Leading Region:** No data available")
            except Exception as e:
                st.warning("**Leading Region:** No data available")
    else:
        st.warning("⚠️ No data available with the current filters. Please adjust your filter settings.")

else:
    # Welcome screen when no file is uploaded
    st.info("👋 **Welcome to the Sales & Revenue Analysis Dashboard!**")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 📁 Getting Started
        
        1. **Upload your data file** using the sidebar
        2. Supported formats: CSV, Excel (.xlsx, .xls)
        3. The dashboard will automatically analyze your data
        4. Use filters to drill down into specific segments
        
        ### ✨ Features
        
        - 📊 Interactive KPI cards
        - 📈 Revenue trend analysis
        - 🥧 Category distribution charts
        - 🏆 Top products ranking
        - 🗺️ Regional performance
        - 💾 Export filtered data
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Required Data Format
        
        Your CSV/Excel file should contain these columns:
        
        | Column   | Type     | Required |
        |----------|----------|----------|
        | Date     | Date     | ✅ Yes   |
        | Product  | Text     | ✅ Yes   |
        | Category | Text     | ✅ Yes   |
        | Region   | Text     | ✅ Yes   |
        | Quantity | Number   | ✅ Yes   |
        | Price    | Number   | ✅ Yes   |
        | Revenue  | Number   | ✅ Yes   |
        | Cost     | Number   | ⚪ Optional |
        | Profit   | Number   | ⚪ Optional |
        
        """)
    
    st.markdown("---")
    
    # Example data preview
    st.subheader("📝 Example Data Format")
    example_data = pd.DataFrame({
        'Date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'Product': ['Laptop', 'Smartphone', 'T-Shirt'],
        'Category': ['Electronics', 'Electronics', 'Clothing'],
        'Region': ['North', 'South', 'East'],
        'Quantity': [5, 8, 25],
        'Price': [899.99, 699.50, 29.99],
        'Revenue': [4499.95, 5596.00, 749.75],
        'Cost': [3149.97, 3917.20, 412.36],
        'Profit': [1349.98, 1678.80, 337.39]
    })
    st.dataframe(example_data, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📊 Sales & Revenue Analysis Dashboard | Built with Streamlit & Python</p>
        <p>Nagineni Rithika Computer Science and Engineering(AIML)</p>
    </div>
    """,
    unsafe_allow_html=True
)
