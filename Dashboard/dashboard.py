import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import geopandas as gpd
from shapely.geometry import Point
import os


# Load main_data for dashboard
current_dir = os.path.dirname(__file__)
csv_path = os.path.join(current_dir, 'main_data.csv')

main_df = pd.read_csv(csv_path)
main_df.drop(columns=['seller_id', 
                      'shipping_limit_date', 
                      'product_name_lenght', 
                      'product_description_lenght',
                      'product_photos_qty',
                      ], axis=1, inplace=True
                      )
main_df.rename(columns={'order_purchase_timestamp' : 'order_date'}, inplace=True)
main_df['order_date'] = pd.to_datetime(main_df['order_date']).dt.tz_localize('Asia/Jakarta')


# Membuat filter data dengan rentang waktu
min_date = main_df['order_date'].min()      # = 2016-09-04
max_date = main_df['order_date'].max()      # = 2018-10-17

with st.sidebar :
    # Menambahkan logo ecommerce
    current_dir_logo = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir_logo, "sample_logo.jpg")
    st.image(logo_path)

    # Menambahkan filter range date dengan input date
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )
    
    # Menambahkan pesan singkat
    st.metric(label='HELLO', value="Welcome", width='content')

# Membuat filter data applied pada main_df
main_df = main_df[(main_df['order_date'] >= str(start_date)) &
                 (main_df['order_date'] <= str(end_date))
                 ]

# Dashboard Utama
st.header('Brazilian E-commerce Analysis Dashboard :shopping_cart:')

# 5-Stars Review
st.subheader('1. Top 10 Product with most 5 Stars Review :star:')
top5_stars_df = main_df[main_df['review_score'] == 5]
top5_stars_df = top5_stars_df.groupby(['product_category_name']).size().reset_index(name='count_5stars').sort_values('count_5stars', ascending=False)

fig, ax = plt.subplots(figsize=(36,18))
sns.barplot(
    data=top5_stars_df.head(10),
    x='count_5stars',
    y='product_category_name',
    ax=ax,
    color='#C1E1C1'
)
ax.set_title('Top 10 Products with Highest number of 5-Stars Review', fontsize=45, loc='center')
ax.set_ylabel(None)
ax.set_xlabel('5-Stars received', fontsize=37)
ax.tick_params(axis='x', labelsize=30)
ax.tick_params(axis='y', labelsize=35)
for container in ax.containers:
    ax.bar_label(container, fmt='%.0f', fontsize=22, padding=0)
st.pyplot(fig)


st.write('')
st.write('')
st.write('')

# Faktor korelasi harga pengiriman
st.subheader('2. Faktor Korelasi Harga Pengiriman (freight_value)')

correlation_data = main_df[['freight_value', 'volume', 'product_weight_g']]

fig, ax = plt.subplots(figsize=(20,20))
sns.heatmap(
    data=correlation_data.corr(),
    annot=True,
    cmap='Greens',
    square=True,
    annot_kws={'size' : 16},
    ax=ax)
ax.set_title('Heatmap Korelasi Harga Pengiriman Barang', loc='center', fontsize=35)
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)
st.pyplot(fig)

col1, col2 = st.columns(2, border=True)
with col1 :
    st.metric(label='Volume -> Freight Value', 
              value=round(correlation_data['volume'].corr(correlation_data['freight_value']), ndigits=4),
        )

with col2 :
    st.metric(label='product_weight_g -> freight_value',
              value=round(correlation_data['product_weight_g'].corr(correlation_data['freight_value']), ndigits=4),
              )

st.write('')
st.write('')
st.write('')


# Geospatial Analysis
st.subheader('3. Lokasi Geografis dengan Angka Pembelian Tertinggi')

geolocation_df = main_df.groupby('customer_zip_code_prefix', as_index=False).agg({
    'geolocation_lat' : 'mean',
    'geolocation_lng' : 'mean',
    'payment_value' : 'sum',
    'geolocation_city' : 'first',
    'geolocation_state' : 'first'    
})

geometry = [Point(xy) for xy in zip(geolocation_df['geolocation_lng'], geolocation_df['geolocation_lat'])]
geo_df = gpd.GeoDataFrame(data=geolocation_df.sort_values(by='payment_value', ascending=True), geometry=geometry)

world = gpd.read_file('ne_110m_admin_0_countries.zip')
brazil = world[world['NAME'] == 'Brazil'].to_crs(epsg=4326)

fig, ax = plt.subplots(figsize=(10, 10))
brazil.plot(figsize=(8, 8), color='#F2F2F2', edgecolor='black', ax=ax)
geo_df.plot(column='payment_value', ax=ax, cmap='Reds')
st.pyplot(fig)

st.write('')
st.write('')
st.write('')



# RFM Analysis
st.subheader('4. Best Customer Based on RFM Parameters')

rfm_df = main_df.groupby(by='customer_unique_id', as_index=False).agg({
    'order_date' : 'max',
    'order_id' : 'count',
    'price' : 'sum'
    })
rfm_df.rename(columns={
    'order_date' : 'max_order_timestamp',
    'order_id' : 'frequency',
    'price' : 'monetary'
},inplace=True)
rfm_df['max_order_timestamp'] = rfm_df['max_order_timestamp'].dt.date
recent_date = rfm_df['max_order_timestamp'].max()
rfm_df['recency'] = rfm_df['max_order_timestamp'].apply(lambda x : (recent_date - x).days)
rfm_df.drop('max_order_timestamp', axis=1, inplace=True)

col3, col4, col5 = st.columns(3, border=True)

with col3 :
    avg_recency = round(rfm_df['recency'].mean(), ndigits=1)

    st.metric(label='Average of Recency (Days)',
              value=avg_recency)

with col4 :
    avg_frequency = round(rfm_df['frequency'].mean(), ndigits=2)

    st.metric(label='Average of Frequency',
              value=avg_frequency)

with col5 :
    avg_monetary = format_currency(number=rfm_df['monetary'].mean(), currency='BRL', locale='pt_BR')

    st.metric(label='Average of Monetary',
              value=avg_monetary)

fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(35,35))
sns.barplot(
    data=rfm_df.sort_values(by='recency', ascending=True).head(5),
    x='recency',
    y='customer_unique_id',
    palette=['#1565c0', '#1e88e5', '#42a5f5', '#90caf9', '#e3f2fd'],
    ax=ax[0]
)
ax[0].set_title('By Recency (days)',loc='center', fontsize=70)
ax[0].set_xlabel(None)
ax[0].set_ylabel('Customer Unique ID', fontsize=30)
ax[0].tick_params(axis='x', labelsize=30)
ax[0].tick_params(axis='y', labelsize=25)
st.write('')

sns.barplot(
    data=rfm_df.sort_values(by='frequency', ascending=False).head(5),
    x='frequency',
    y='customer_unique_id',
    palette=['#1565c0', '#1e88e5', '#42a5f5', '#90caf9', '#e3f2fd'],
    ax=ax[1]
)
ax[1].set_title('By frequency',loc='center', fontsize=70)
ax[1].set_xlabel(None)
ax[1].set_ylabel('Customer Unique ID', fontsize=30)
ax[1].tick_params(axis='x', labelsize=30)
ax[1].tick_params(axis='y', labelsize=25)
st.write('')

sns.barplot(
    data=rfm_df.sort_values(by='monetary', ascending=False).head(5),
    x='monetary',
    y='customer_unique_id',
    palette=['#1565c0', '#1e88e5', '#42a5f5', '#90caf9', '#e3f2fd'],
    ax=ax[2]
)
ax[2].set_title('By monetary',loc='center', fontsize=70)
ax[2].set_xlabel(None)
ax[2].set_ylabel('Customer Unique ID', fontsize=30)
ax[2].tick_params(axis='x', labelsize=30)
ax[2].tick_params(axis='y', labelsize=25)

st.pyplot(fig)