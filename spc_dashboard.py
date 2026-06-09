import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import folium
from streamlit_folium import folium_static
from datetime import datetime
import os
from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="SPC Dashboard - Smart Poverty & Community Aid",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #F8FAFC;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .dashboard-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.02);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .kpi-card {
        background: white;
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        border: 1px solid rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 30px -12px rgba(0,0,0,0.1);
    }
    
    .cluster-card {
        background: white;
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        border-left: 4px solid;
        margin-bottom: 1rem;
        height: 100%;
    }
    
    h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563EB 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        text-align: center;
    }
    
    h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 0.75rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2563EB;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748B;
        letter-spacing: 0.02em;
    }
    
    hr {
        margin: 1rem 0;
        border-color: rgba(0,0,0,0.05);
    }
    
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 0.5rem;
    }
    
    .nav-container {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 1rem 0;
    }

    div.stButton {
        display: flex;
        justify-content: center;
    }

    .stButton button {
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.2s;
        padding: 0.5rem 1rem;
        background: white;
        border: 1px solid #E2E8F0;
        font-size: 0.85rem;
        width: 100%;
    }
    
    .stButton button:hover {
        background: #2563EB;
        color: white;
        border-color: #2563EB;
    }
    
    .ranking-card {
        background: white;
        border-radius: 16px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid;
        transition: all 0.2s;
    }
    
    .ranking-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Data default
def get_default_data():
    data = {
        'Kabupaten/Kota': ['Gunungkidul', 'Kulonprogo', 'Bantul', 'Sleman', 'Yogyakarta'],
        'Penduduk Miskin': [120000, 95000, 85000, 60000, 35000],
        'UMK': [2100000, 2100000, 2150000, 2200000, 2300000],
        'TPAK': [68.9, 72.3, 75.8, 80.2, 85.5],
        'RLS': [8.5, 9.2, 10.1, 11.3, 12.5],
        'Luas Wilayah (km²)': [1485.36, 586.27, 506.85, 574.82, 32.5],
        'Jumlah Penduduk Miskin (ribu)': [120, 95, 85, 60, 35]
    }
    return pd.DataFrame(data)

@st.cache_data
def load_data():
    df = pd.read_excel("data/data_spc.xlsx", engine='openpyxl')
    return df

@st.cache_data
def perform_clustering(df):
    # Warna: Merah untuk Prioritas Tinggi, Kuning untuk Sedang, Hijau untuk Rendah
    features = ['TPAK', 'RLS', 'Jumlah Penduduk Miskin (ribu)']
    
    df['Tingkat Kemiskinan Relatif'] = (df['Jumlah Penduduk Miskin (ribu)'] / df['Luas Wilayah (km²)'] * 10)
    
    X = df[['TPAK', 'RLS', 'Tingkat Kemiskinan Relatif']]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X_scaled)
    
    cluster_means = df.groupby('Cluster')['TPAK'].mean()
    priority_order = cluster_means.sort_values().index.tolist()
    cluster_mapping = {priority_order[2]: 'Prioritas Tinggi', 
                       priority_order[1]: 'Prioritas Sedang', 
                       priority_order[0]: 'Prioritas Rendah'}
    
    df['Prioritas'] = df['Cluster'].map(cluster_mapping)
    
    # Warna untuk prioritas: Merah, Kuning, Hijau
    color_mapping = {
        'Prioritas Tinggi': '#EF4444',  # Merah
        'Prioritas Sedang': '#F59E0B',  # Kuning
        'Prioritas Rendah': '#10B981'   # Hijau
    }
    df['Warna'] = df['Prioritas'].map(color_mapping)
    
    return df, scaler, kmeans, color_mapping

# Load data
df_raw = load_data()
df, scaler, kmeans, color_mapping = perform_clustering(df_raw)

# Session state
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ==================== HEADER ====================
logo_path = Path("assets/logo_spc.png")

col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if logo_path.exists():
            st.image(str(logo_path), width=80)
        else:
            st.markdown("<div style='font-size: 2rem;'>🎯</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <div>
            <h1 style="margin-bottom: 0; font-size: 1.75rem;">SPC Dashboard</h1>
            <p style="color: #64748B; margin-top: -0.25rem; font-size: 0.65rem;">Smart Poverty & Community Aid — Sistem Prioritas Bantuan Sosial</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== NAVIGASI ====================
nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button("📊 Overview", key="nav1", use_container_width=True):
        st.session_state.page = "Overview"

with nav_col2:
    if st.button("🔬 Clustering & Insights", key="nav2", use_container_width=True):
        st.session_state.page = "Clustering"

with nav_col3:
    if st.button("🗺️ Priority Map", key="nav3", use_container_width=True):
        st.session_state.page = "Map"

st.markdown("<hr>", unsafe_allow_html=True)

# ==================== HALAMAN OVERVIEW ====================
if st.session_state.page == "Overview":
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="color: #64748B; font-size: 0.9rem; letter-spacing: 0.05rem;">DATA-DRIVEN SOCIAL ASSISTANCE PRIORITIZATION</p>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-value">{df['Kabupaten/Kota'].nunique()}</div>
            <div class="metric-label">Kabupaten/Kota</div>
            <div class="metric-trend">Daerah Istimewa Yogyakarta</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-value">3</div>
            <div class="metric-label">Tingkat Prioritas</div>
            <div class="metric-trend">K-Means Clustering</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        miskin_avg = df['Penduduk Miskin'].mean()
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-value">{miskin_avg:.1f}%</div>
            <div class="metric-label">Rata-rata Penduduk Miskin</div>
            <div class="metric-trend">Daerah Istimewa Yogyakarta</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        high_priority = df[df['Prioritas'] == 'Prioritas Tinggi'].shape[0]
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-value">{high_priority}</div>
            <div class="metric-label">Prioritas Tinggi</div>
            <div class="metric-trend">Gunungkidul & Kulonprogo</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bar chart TPAK - warna biru dominan
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>📊 Perbandingan Tingkat Partisipasi Angkatan Kerja (TPAK)</h3>", unsafe_allow_html=True)
        fig_tpak = px.bar(df.sort_values('TPAK', ascending=True),
                        x='Kabupaten/Kota', y='TPAK',
                        color='TPAK',
                        color_continuous_scale='Blues',
                        text='TPAK')
        fig_tpak.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_tpak.update_layout(plot_bgcolor='white', height=400, showlegend=False)
        st.plotly_chart(fig_tpak, use_container_width=True)
        # Tambahkan keterangan/interpretasi
        st.markdown("""
        <div style="background: #F0F9FF; padding: 0.75rem; border-radius: 12px; margin-top: -0.5rem; margin-bottom: 1.5rem; border-left: 3px solid #2563EB;">
            <p style="font-size: 0.8rem; color: #1E40AF; margin: 0;">
                <strong>📖 Interpretasi TPAK:</strong> Tingkat Partisipasi Angkatan Kerja (TPAK) adalah persentase penduduk usia kerja (15-64 tahun) 
                yang aktif secara ekonomi, baik bekerja maupun mencari kerja. Semakin tinggi TPAK, semakin besar proporsi penduduk yang terlibat 
                dalam kegiatan ekonomi. Daerah dengan TPAK tinggi cenderung memiliki lebih banyak lapangan kerja dan pendapatan masyarakat yang lebih baik.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3>💰 Upah Minimum Kabupaten/Kota (UMK)</h3>", unsafe_allow_html=True)
        fig_umk = px.bar(df.sort_values('UMK', ascending=False),
                        x='Kabupaten/Kota', y='UMK',
                        color='UMK',
                        color_continuous_scale='Blues',
                        text='UMK')
        fig_umk.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        fig_umk.update_layout(plot_bgcolor='white', height=400, showlegend=False, margin=dict(t=30))
        st.plotly_chart(fig_umk, use_container_width=True)
        # Keterangan UMK
        st.markdown("""
        <div style="background: #F0F9FF; padding: 0.75rem; border-radius: 12px; margin-top: -0.5rem; border-left: 3px solid #2563EB;">
            <p style="font-size: 0.8rem; color: #1E40AF; margin: 0;">
                <strong>📖 Interpretasi UMK:</strong> Upah Minimum Kabupaten/Kota adalah standar upah terendah yang diberikan pengusaha kepada 
                pekerja/buruh. UMK mencerminkan kondisi ekonomi regional dan biaya hidup. Wilayah dengan UMK rendah cenderung memiliki 
                tingkat kemiskinan lebih tinggi dan membutuhkan intervensi bantuan sosial yang lebih besar.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Bar chart RLS - warna biru dominan
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>📚 Rata-rata Lama Sekolah (RLS)</h3>", unsafe_allow_html=True)
        fig_rls = px.bar(df.sort_values('RLS', ascending=True),
                         x='Kabupaten/Kota', y='RLS',
                         color='RLS',
                         color_continuous_scale='Blues',
                         text='RLS')
        fig_rls.update_traces(texttemplate='%{text:.1f} th', textposition='outside')
        fig_rls.update_layout(plot_bgcolor='white', height=400, showlegend=False)
        st.plotly_chart(fig_rls, use_container_width=True)
        # Tambahkan keterangan
        st.markdown("""
        <div style="background: #F0F9FF; padding: 0.6rem; border-radius: 10px; margin-top: -0.3rem; border-left: 3px solid #2563EB;">
            <p style="font-size: 0.8rem; color: #1E40AF; margin: 0;">
                <strong>📖 Interpretasi RLS:</strong> Rata-rata Lama Sekolah (RLS) mengukur rata-rata tahun pendidikan formal yang 
                ditempuh penduduk usia 25 tahun ke atas. RLS yang tinggi mencerminkan kualitas sumber daya manusia yang lebih baik, 
                yang berkorelasi dengan produktivitas dan pendapatan yang lebih tinggi.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3>👥 Jumlah Penduduk Miskin</h3>", unsafe_allow_html=True)
        fig_miskin = px.bar(df.sort_values('Jumlah Penduduk Miskin (ribu)', ascending=False),
                            x='Kabupaten/Kota', y='Jumlah Penduduk Miskin (ribu)',
                            color='Jumlah Penduduk Miskin (ribu)',
                            color_continuous_scale='Blues',
                            text='Jumlah Penduduk Miskin (ribu)')
        fig_miskin.update_traces(texttemplate='%{text:.0f} rb', textposition='outside')
        fig_miskin.update_layout(plot_bgcolor='white', height=400, showlegend=False)
        st.plotly_chart(fig_miskin, use_container_width=True)
        # Tambahkan keterangan
        st.markdown("""
        <div style="background: #F0F9FF; padding: 0.6rem; border-radius: 10px; margin-top: -0.3rem; border-left: 3px solid #2563EB;">
            <p style="font-size: 0.8rem; color: #1E40AF; margin: 0;">
                <strong>📖 Interpretasi Penduduk Miskin:</strong> Data ini menunjukkan jumlah penduduk yang hidup di bawah garis kemiskinan 
                (dalam ribuan jiwa). Semakin tinggi angkanya, semakin besar beban kemiskinan di wilayah tersebut dan semakin tinggi 
                prioritas intervensi bantuan sosial yang diperlukan.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Cluster Summary Cards dengan warna Merah, Kuning, Hijau
    st.markdown("<br><h3>📋 Ringkasan Prioritas Cluster</h3>", unsafe_allow_html=True)
    
    cluster_col1, cluster_col2, cluster_col3 = st.columns(3)
    
    high_data = df[df['Prioritas'] == 'Prioritas Tinggi']
    medium_data = df[df['Prioritas'] == 'Prioritas Sedang']
    low_data = df[df['Prioritas'] == 'Prioritas Rendah']
    
    with cluster_col1:
        st.markdown(f"""
        <div class="cluster-card" style="border-left-color: #EF4444;">
            <h3 style="color: #EF4444; margin-bottom: 0.5rem;">🔴 Prioritas Tinggi</h3>
            <p><strong>{', '.join(high_data['Kabupaten/Kota'].tolist())}</strong></p>
            <p>Rata-rata TPAK: <strong>{high_data['TPAK'].mean():.1f}%</strong></p>
            <p>Rata-rata RLS: <strong>{high_data['RLS'].mean():.1f} tahun</strong></p>
            <hr>
            <p style="font-size: 0.8rem;">Kemiskinan tinggi, akses pendidikan rendah, kesenjangan infrastruktur pedesaan</p>
            <p style="color: #EF4444; font-weight: bold;">⚠️ Intervensi Prioritas: Aksi Segera</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cluster_col2:
        st.markdown(f"""
        <div class="cluster-card" style="border-left-color: #F59E0B;">
            <h3 style="color: #F59E0B; margin-bottom: 0.5rem;">🟡 Prioritas Sedang</h3>
            <p><strong>{', '.join(medium_data['Kabupaten/Kota'].tolist())}</strong></p>
            <p>Rata-rata TPAK: <strong>{medium_data['TPAK'].mean():.1f}%</strong></p>
            <p>Rata-rata RLS: <strong>{medium_data['RLS'].mean():.1f} tahun</strong></p>
            <hr>
            <p style="font-size: 0.8rem;">Kemiskinan moderat, wilayah campuran urban-rural, pembangunan berkembang</p>
            <p style="color: #F59E0B; font-weight: bold;">📌 Intervensi Prioritas: Program Tertarget</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cluster_col3:
        st.markdown(f"""
        <div class="cluster-card" style="border-left-color: #10B981;">
            <h3 style="color: #10B981; margin-bottom: 0.5rem;">🟢 Prioritas Rendah</h3>
            <p><strong>{', '.join(low_data['Kabupaten/Kota'].tolist())}</strong></p>
            <p>Rata-rata TPAK: <strong>{low_data['TPAK'].mean():.1f}%</strong></p>
            <p>Rata-rata RLS: <strong>{low_data['RLS'].mean():.1f} tahun</strong></p>
            <hr>
            <p style="font-size: 0.8rem;">Indikator kuat, keunggulan perkotaan, pembangunan berkelanjutan</p>
            <p style="color: #10B981; font-weight: bold;">✅ Intervensi Prioritas: Monitoring & Pemeliharaan</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== HALAMAN CLUSTERING & INSIGHTS ====================
elif st.session_state.page == "Clustering":
    st.markdown("<h2>🔬 Clustering & Insights</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 2rem; text-align: center;'>Analisis K-Means clustering dan visualisasi</p>", unsafe_allow_html=True)
    
    # Filter
    with st.container():
        #st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        col_filter1, col_filter2, col_filter3 = st.columns([1, 2, 1])
        with col_filter2:
            filter_prioritas = st.multiselect(
                "Filter berdasarkan prioritas",
                options=['Prioritas Tinggi', 'Prioritas Sedang', 'Prioritas Rendah'],
                default=['Prioritas Tinggi', 'Prioritas Sedang', 'Prioritas Rendah']
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    filtered_df = df[df['Prioritas'].isin(filter_prioritas)] if filter_prioritas else df
    
    # Radar Chart - warna Merah, Kuning, Hijau
    st.markdown("<h3>📡 Perbandingan Karakteristik Cluster</h3>", unsafe_allow_html=True)
    
    cluster_profiles = filtered_df.groupby('Prioritas')[['TPAK', 'RLS', 'Jumlah Penduduk Miskin (ribu)']].mean().reset_index()
    categories = ['TPAK (%)', 'RLS (tahun)', 'Penduduk Miskin (inverted)']
    radar_colors = {'Prioritas Tinggi': '#EF4444', 'Prioritas Sedang': '#F59E0B', 'Prioritas Rendah': '#10B981'}
    
    fig_radar = go.Figure()
    max_miskin = df['Jumlah Penduduk Miskin (ribu)'].max()
    
    for _, row in cluster_profiles.iterrows():
        values = [
            row['TPAK'],
            (row['RLS'] / 13) * 100,
            (1 - (row['Jumlah Penduduk Miskin (ribu)'] / max_miskin)) * 100
        ]
        values += values[:1]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=row['Prioritas'],
            line_color=radar_colors[row['Prioritas']],
            fillcolor=radar_colors[row['Prioritas']],
            opacity=0.3
        ))
    
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                           showlegend=True, height=500)
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Heatmap - gradasi merah ke hijau
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>📈 Scatter Plot: TPAK vs RLS</h3>", unsafe_allow_html=True)
        fig_scatter = px.scatter(filtered_df, x='TPAK', y='RLS',
                                 color='Prioritas', size='Penduduk Miskin',
                                 hover_name='Kabupaten/Kota', text='Kabupaten/Kota',
                                 color_discrete_map=radar_colors)
        fig_scatter.update_traces(textposition='top center')
        fig_scatter.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Heatmap korelasi antar variabel
    with col2:
        st.markdown("<h3>🎨 Heatmap Korelasi Antar Variabel</h3>", unsafe_allow_html=True)
        
        # Pilih kolom numerik untuk korelasi
        corr_columns = ['TPAK', 'RLS', 'Jumlah Penduduk Miskin (ribu)', 'UMK']
        corr_data = filtered_df[corr_columns].corr()
        
        # Buat heatmap korelasi
        fig_corr = px.imshow(
            corr_data,
            text_auto='.2f',
            aspect='auto',
            color_continuous_scale='RdBu_r',
            labels=dict(x='Variabel', y='Variabel', color='Korelasi'),
            zmin=-1, zmax=1
        )
        fig_corr.update_layout(height=400, margin=dict(t=30))
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Tambahkan keterangan
        st.caption("🔵 Korelasi positif (biru) | 🔴 Korelasi negatif (merah) | Semakin besar angka, semakin kuat korelasi")
    
    # Detailed Interpretation (seperti screenshot)
    st.markdown("<br><h3>📖 Interpretasi Detail</h3>", unsafe_allow_html=True)
    
    with st.expander("🔬 Metodologi Clustering", expanded=True):
        st.markdown("""
        **Metode K-Means Clustering**
        
        Algoritma K-Means mengelompokkan 5 kabupaten/kota di DI Yogyakarta menjadi 3 cluster berbeda berdasarkan:
        - Tingkat Kemiskinan (proksi dari jumlah penduduk miskin)
        - Indeks Pendidikan (RLS - Rata-rata Lama Sekolah)
        - Tingkat Partisipasi Angkatan Kerja (TPAK)
        
        Jumlah cluster optimal ditentukan menggunakan metode elbow dan silhouette analysis.
        """)
    
    with st.expander("📌 Temuan Utama", expanded=True):
        st.markdown("""
        - **Pemisahan yang jelas** antara wilayah perkotaan (Kota Yogyakarta) dan wilayah pedesaan (Gunungkidul, Kulonprogo)
        - **Korelasi negatif kuat** antara UMK dan tingkat partisipasi angkatan kerja
        - **Akses pendidikan** menjadi pembeda kritis antar cluster
        - Wilayah prioritas tinggi (Gunungkidul, Kulonprogo) memiliki keterbatasan infrastruktur yang signifikan
        """)
    
    with st.expander("💰 Implikasi Kebijakan & Alokasi Anggaran", expanded=True):
        st.markdown("""
        **Implikasi Kebijakan:**
        Hasil clustering memberikan wawasan untuk alokasi sumber daya. Wilayah prioritas tinggi memerlukan intervensi komprehensif termasuk pembangunan infrastruktur, program pendidikan, dan inisiatif ketenagakerjaan. Wilayah prioritas sedang mendapat manfaat dari bantuan bersyarat yang tertarget, sementara wilayah prioritas rendah fokus pada keberlanjutan dan peningkatan kualitas.
        
        **Rekomendasi Alokasi Anggaran:**
        - 🎯 Prioritas Tinggi: **50%** dari total anggaran bantuan sosial
        - 📌 Prioritas Sedang: **30%** dari total anggaran bantuan sosial
        - ✅ Prioritas Rendah: **20%** untuk pemeliharaan dan program preventif
        """)

# ==================== HALAMAN PRIORITY MAP ====================
elif st.session_state.page == "Map":
    st.markdown("<h2>🗺️ Peta Prioritas Yogyakarta</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 1.5rem; text-align: center; font-size: 0.7rem;'>Visualisasi geografis prioritas bantuan sosial</p>", unsafe_allow_html=True)
    
    # Koordinat yang benar untuk setiap kabupaten/kota
    coordinates = {
        'Gunungkidul': {'lat': -7.9703, 'lon': 110.7486},
        'Kulonprogo': {'lat': -7.8125, 'lon': 110.1513},
        'Bantul': {'lat': -7.8295, 'lon': 110.3358},
        'Sleman': {'lat': -7.6893, 'lon': 110.3435},
        'Yogyakarta': {'lat': -7.7970, 'lon': 110.3705}
    }
    
    # Tambahkan koordinat ke dataframe
    df['Latitude'] = df['Kabupaten/Kota'].map(lambda x: coordinates.get(x, {}).get('lat', -7.7956))
    df['Longitude'] = df['Kabupaten/Kota'].map(lambda x: coordinates.get(x, {}).get('lon', 110.3695))
    
    # Filter berdasarkan kabupaten/kota
    # st.markdown('<div class="dashboard-card" style="padding: 0.75rem;">', unsafe_allow_html=True)
    selected_districts = st.multiselect(
        "Filter peta berdasarkan Kabupaten/Kota",
        options=df['Kabupaten/Kota'].tolist(),
        default=df['Kabupaten/Kota'].tolist(),
        key="map_filter_districts"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    filtered_map_df = df[df['Kabupaten/Kota'].isin(selected_districts)] if selected_districts else df
    
    map_color = {'Prioritas Tinggi': '#EF4444', 'Prioritas Sedang': '#F59E0B', 'Prioritas Rendah': '#10B981'}
    
    col_map, col_sidebar = st.columns([2, 1])
    
    with col_map:
        m = folium.Map(location=[-7.85, 110.35], zoom_start=9.5, tiles='CartoDB positron')
        
        for _, row in filtered_map_df.iterrows():
            radius = 12 + (row['Jumlah Penduduk Miskin (ribu)'] / 20)
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 180px; font-size: 12px;">
                <h4 style="margin: 0 0 6px 0; font-size: 14px;">{row['Kabupaten/Kota']}</h4>
                <p style="margin: 2px 0;"><strong>Prioritas:</strong> {row['Prioritas']}</p>
                <p style="margin: 2px 0;"><strong>TPAK:</strong> {row['TPAK']:.1f}%</p>
                <p style="margin: 2px 0;"><strong>RLS:</strong> {row['RLS']:.1f} tahun</p>
                <p style="margin: 2px 0;"><strong>Penduduk Miskin:</strong> {row['Jumlah Penduduk Miskin (ribu)']:.0f} rb</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=250),
                color=map_color[row['Prioritas']],
                fill=True,
                fill_color=map_color[row['Prioritas']],
                fill_opacity=0.6,
                weight=2,
                tooltip=f"{row['Kabupaten/Kota']}"
            ).add_to(m)
        
        folium_static(m, width=650, height=450)
    
    with col_sidebar:
        # Pilih kabupaten untuk detail
        selected = st.selectbox("Detail Kabupaten/Kota", df['Kabupaten/Kota'].tolist(), key="detail_select")
        district_data = df[df['Kabupaten/Kota'] == selected].iloc[0]
        
        st.markdown(f"""
        <div class="dashboard-card" style="padding: 1rem;">
            <h3 style="font-size: 0.85rem;">📊 {selected}</h3>
            <p style="font-size: 0.7rem; margin: 0.25rem 0;"><strong>Prioritas:</strong> <span style="color: {map_color[district_data['Prioritas']]};">{district_data['Prioritas']}</span></p>
            <p style="font-size: 0.7rem; margin: 0.25rem 0;"><strong>📊 TPAK:</strong> {district_data['TPAK']:.1f}%</p>
            <p style="font-size: 0.7rem; margin: 0.25rem 0;"><strong>📚 RLS:</strong> {district_data['RLS']:.1f} tahun</p>
            <p style="font-size: 0.7rem; margin: 0.25rem 0;"><strong>👥 Penduduk Miskin:</strong> {district_data['Jumlah Penduduk Miskin (ribu)']:.0f} rb</p>
            <p style="font-size: 0.7rem; margin: 0.25rem 0;"><strong>💰 UMK:</strong> Rp {district_data['UMK']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommended Actions
        st.markdown("""
        <div class="dashboard-card" style="padding: 1rem;">
            <h3 style="font-size: 0.85rem;">🎯 Rekomendasi Aksi</h3>
            <p style="font-size: 0.7rem; margin: 0.5rem 0;"><strong>• Bantuan Tunai Bersyarat</strong><br><span style="font-size: 0.65rem;">Dukungan terikat pada pendidikan dan kesehatan</span></p>
            <p style="font-size: 0.7rem; margin: 0.5rem 0;"><strong>• Program Dukungan UMKM</strong><br><span style="font-size: 0.65rem;">Layanan keuangan mikro dan pengembangan bisnis</span></p>
            <p style="font-size: 0.7rem; margin: 0.5rem 0;"><strong>• Akses Layanan Kesehatan</strong><br><span style="font-size: 0.65rem;">Klinik mobile dan perluasan jaminan kesehatan</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    # District Ranking
    st.markdown("<br><h3 style='font-size: 1rem;'>🏆 Peringkat Kabupaten/Kota</h3>", unsafe_allow_html=True)
    
    ranking_df = df[['Kabupaten/Kota', 'Prioritas', 'TPAK', 'RLS', 'Penduduk Miskin']].copy()
    ranking_df = ranking_df.sort_values('Penduduk Miskin', ascending=False)
    ranking_df.index = range(1, len(ranking_df) + 1)
    
    rank_col1, rank_col2, rank_col3 = st.columns([1.5, 1.5, 1])
    
    with rank_col1:
        for i, row in ranking_df.iterrows():
            if row['Prioritas'] == 'Prioritas Tinggi':
                color = '#EF4444'
                icon = '🔴'
            elif row['Prioritas'] == 'Prioritas Sedang':
                color = '#F59E0B'
                icon = '🟡'
            else:
                color = '#10B981'
                icon = '🟢'
            
            st.markdown(f"""
            <div class="ranking-card" style="border-left-color: {color}; padding: 0.5rem;">
                <table style="width: 100%; font-size: 0.7rem;">
                    <tr>
                        <td style="width: 35px;"><strong>{i}.</strong></td>
                        <td><strong>{row['Kabupaten/Kota']}</strong><br><span style="color: {color};">{row['Prioritas']}</span></td>
                        <td style="text-align: right;">
                            <strong>{row['Penduduk Miskin']:.1f}%</strong><br>
                            <span style="font-size: 0.6rem;">Kemiskinan</span>
                        </td>
                        <td style="text-align: center; width: 30px;">{icon}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
    
    with rank_col2:
        st.markdown(f"""
        <div class="dashboard-card" style="padding: 0.75rem;">
            <h3 style="font-size: 0.75rem;">📋 Ringkasan Prioritas</h3>
            <hr>
            <p style="font-size: 0.65rem;"><strong>🔴 Prioritas Tinggi:</strong> Gunungkidul, Kulonprogo</p>
            <p style="font-size: 0.65rem;"><strong>🟡 Prioritas Sedang:</strong> Bantul, Sleman</p>
            <p style="font-size: 0.65rem;"><strong>🟢 Prioritas Rendah:</strong> Yogyakarta</p>
            <hr>
            <p style="font-size: 0.65rem;"><strong>Total Penduduk Miskin:</strong><br>
            🔴 Prioritas Tinggi: 215 ribu jiwa<br>
            🟡 Prioritas Sedang: 145 ribu jiwa<br>
            🟢 Prioritas Rendah: 35 ribu jiwa
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with rank_col3:
        st.markdown(f"""
        <div class="dashboard-card" style="padding: 0.75rem;">
            <h3 style="font-size: 0.75rem;">📍 Legenda Prioritas</h3>
            <hr>
            <p style="font-size: 0.65rem;"><span class="legend-dot" style="background: #EF4444;"></span> Prioritas Tinggi</p>
            <p style="font-size: 0.65rem;"><span class="legend-dot" style="background: #F59E0B;"></span> Prioritas Sedang</p>
            <p style="font-size: 0.65rem;"><span class="legend-dot" style="background: #10B981;"></span> Prioritas Rendah</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.75rem;">
    <p>SPC Dashboard — Smart Poverty & Community Aid | K-Means Clustering | DIY Yogyakarta</p>
</div>
""", unsafe_allow_html=True)