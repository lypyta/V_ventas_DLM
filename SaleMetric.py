import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

# --- Configuración de la URL de Google Drive ---
# 🚨 Reemplaza con tu enlace de "Publicar en la web" de Google Sheets (formato XLSX)
GOOGLE_SALES_URL = 'https://docs.google.com/spreadsheets/d/1UNXW4LFYfc-P4eO-wVkav9FCSZtwC2Rw00cHZOQY5DI/export?format=xlsx'

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="SaleMetric | Business Intelligence", page_icon="📈")

# Estilos personalizados para una interfaz limpia y profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 26px; color: #0D47A1; font-weight: bold; }
    .stSelectbox label { font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- Lógica de Procesamiento de Datos ---
@st.cache_data
def load_and_process_sales(url):
    try:
        if "TU_ID_AQUI" in url:
            # Datos de demostración basados en tu captura definitiva
            data = {
                'Cliente': ['CARLOS PEÑA', 'TAPIA MAQUINARIAS', 'LO MAXIMO', 'LUIS GENEY', 'ANIBAL MUÑOZ', 'LEONARDO SOSA', 'ROBERTO JIMENEZ', 'GENESIS MARTINEZ', 'JOSE RIVAS'],
                'Venta Neta Real': [0, 0, 365, 730, 840, 949, 949, 1008, 1460],
                'SEMANA': ['SEMANA 3', 'SEMANA 5', 'SEMANA 4', 'SEMANA 5', 'SEMANA 2', 'SEMANA 2', 'SEMANA 4', 'SEMANA 3', 'SEMANA 4'],
                'MES': ['ENERO', 'ENERO', 'ENERO', 'ENERO', 'ENERO', 'ENERO', 'ENERO', 'ENERO', 'ENERO']
            }
            return pd.DataFrame(data)

        response = requests.get(url)
        response.raise_for_status()
        
        # Leer el Excel
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        
        # Limpieza de columnas basada en tu imagen definitiva
        # Buscamos las columnas exactas: Cliente, Venta Neta Real, SEMANA, MES
        expected_cols = {
            'Cliente': 'Cliente',
            'Venta Neta Real': 'Venta Neta Real',
            'SEMANA': 'SEMANA',
            'MES': 'MES'
        }
        
        # Si los nombres en el Excel tienen espacios o variaciones, intentamos mapearlos
        df.columns = [c.strip() for c in df.columns]
        
        # Convertir ventas a numérico
        df['Venta Neta Real'] = pd.to_numeric(df['Venta Neta Real'], errors='coerce').fillna(0)
        
        # Asegurar que MES y SEMANA sean texto limpio
        df['MES'] = df['MES'].astype(str).str.upper()
        df['SEMANA'] = df['SEMANA'].astype(str).str.upper()
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

df_sales = load_and_process_sales(GOOGLE_SALES_URL)

# --- Título Principal ---
st.title('📈 SaleMetric - Análisis Comercial')
st.markdown("---")

# --- Navegación de Módulos ---
# Usamos columnas fijas arriba para que sea fácil de ver en móvil
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    btn_resumen = st.button("📊 Resumen General", use_container_width=True)
with col_nav2:
    btn_semanal = st.button("📅 Análisis Semanal", use_container_width=True)
with col_nav3:
    btn_clientes = st.button("👥 Ranking Clientes", use_container_width=True)

# Lógica de estados para la navegación
if 'modulo_activo' not in st.session_state:
    st.session_state.modulo_activo = "Resumen"

if btn_resumen: st.session_state.modulo_activo = "Resumen"
if btn_semanal: st.session_state.modulo_activo = "Semanal"
if btn_clientes: st.session_state.modulo_activo = "Clientes"

st.markdown("---")

if not df_sales.empty:
    
    # --- MÓDULO 1: RESUMEN GENERAL ---
    if st.session_state.modulo_activo == "Resumen":
        st.subheader("Totales Mensuales e Indicadores Clave")
        
        # Cálculos Agrupados por Mes
        resumen_mensual = df_sales.groupby('MES')['Venta Neta Real'].sum().reset_index()
        # Orden lógico de meses (opcional si vienen desordenados)
        orden_meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
        resumen_mensual['MES'] = pd.Categorical(resumen_mensual['MES'], categories=orden_meses, ordered=True)
        resumen_mensual = resumen_mensual.sort_values('MES')

        # KPIs
        total_acumulado = resumen_mensual['Venta Neta Real'].sum()
        promedio_mensual = resumen_mensual['Venta Neta Real'].mean()
        
        k1, k2 = st.columns(2)
        k1.metric("Venta Total Acumulada", f"${total_acumulado:,.0f}")
        k2.metric("Promedio de Venta Mensual", f"${promedio_mensual:,.0f}")

        # Gráfico de Totales Mensuales solicitado
        st.markdown("#### Evolución de Ventas por Mes")
        fig_mes = px.bar(
            resumen_mensual, 
            x='MES', 
            y='Venta Neta Real',
            text_auto='.2s',
            title="Ingresos Totales por Mes",
            color_discrete_sequence=['#1976D2']
        )
        st.plotly_chart(fig_mes, use_container_width=True)

    # --- MÓDULO 2: DETALLE SEMANAL ---
    elif st.session_state.modulo_activo == "Semanal":
        st.subheader("Desglose por Semana")
        
        # Filtro de Mes para el detalle
        mes_f = st.selectbox("Selecciona un Mes para ver sus semanas:", df_sales['MES'].unique())
        df_mes_f = df_sales[df_sales['MES'] == mes_f]
        
        # Agrupar por Semana
        resumen_semanal = df_mes_f.groupby('SEMANA')['Venta Neta Real'].sum().reset_index()
        resumen_semanal = resumen_semanal.sort_values('SEMANA')

        fig_sem = px.pie(
            resumen_semanal, 
            values='Venta Neta Real', 
            names='SEMANA',
            title=f"Distribución Semanal en {mes_f}",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_sem, use_container_width=True)
        
        st.markdown("#### Detalle de Transacciones de la Semana")
        st.dataframe(df_mes_f[['Cliente', 'SEMANA', 'Venta Neta Real']], use_container_width=True)

    # --- MÓDULO 3: RANKING DE CLIENTES ---
    elif st.session_state.modulo_activo == "Clientes":
        st.subheader("Top Clientes por Venta Neta")
        
        ranking = df_sales.groupby('Cliente')['Venta Neta Real'].sum().reset_index()
        ranking = ranking.sort_values(by='Venta Neta Real', ascending=False).head(15)
        
        fig_ranking = px.bar(
            ranking, 
            y='Cliente', 
            x='Venta Neta Real',
            orientation='h',
            title="Top 15 Clientes (Venta Acumulada)",
            text_auto='.2s',
            color='Venta Neta Real',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

else:
    st.warning("⚠️ No se detectaron datos. Asegúrate de que la hoja publicada tenga las columnas: Cliente, Venta Neta Real, SEMANA, MES.")

st.markdown("---")
st.caption("SaleMetric - Desarrollado para análisis de alto impacto comercial.")
