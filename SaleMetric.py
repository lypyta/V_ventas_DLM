import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

# --- Configuración de la URL de Google Drive ---
# Conversión del enlace de edición a exportación directa (.xlsx)
GOOGLE_SALES_URL = 'https://docs.google.com/spreadsheets/d/1UNXW4LFYfc-P4eO-wVkav9FCSZtwC2Rw00cHZOQY5DI/export?format=xlsx'

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="SaleMetric | Business Intelligence", page_icon="📈")

# Estilos personalizados para métricas llamativas
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1565C0; font-weight: bold; }
    .stSelectbox label { font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- Lógica de Procesamiento de Datos ---
@st.cache_data
def load_and_process_sales(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        
        # Limpieza de nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        
        # Verificación de columnas esenciales
        required_cols = ['Cliente', 'Venta Neta Real', 'SEMANA', 'MES']
        if not all(col in df.columns for col in required_cols):
            st.error(f"El archivo debe contener las columnas: {', '.join(required_cols)}")
            return pd.DataFrame()

        # Convertir ventas a numérico
        df['Venta Neta Real'] = pd.to_numeric(df['Venta Neta Real'], errors='coerce').fillna(0)
        
        # Estandarizar MES y SEMANA
        df['MES'] = df['MES'].astype(str).str.upper().str.strip()
        df['SEMANA'] = df['SEMANA'].astype(str).str.upper().str.strip()
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return pd.DataFrame()

df_sales = load_and_process_sales(GOOGLE_SALES_URL)

# --- Título Principal ---
st.title('📈 SaleMetric - Inteligencia de Negocios')
st.markdown("---")

# --- Barra Lateral para Parámetros de Cálculo ---
st.sidebar.header("⚙️ Configuración")
dias_mes = st.sidebar.number_input("Días de operación al mes:", min_value=1, max_value=31, value=30, help="Define cuántos días se usan para calcular el promedio diario.")

# --- Navegación de Módulos ---
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    btn_resumen = st.button("📊 Resumen General", use_container_width=True)
with col_nav2:
    btn_semanal = st.button("📅 Análisis Semanal", use_container_width=True)
with col_nav3:
    btn_clientes = st.button("👥 Ranking Clientes", use_container_width=True)

if 'modulo_activo' not in st.session_state:
    st.session_state.modulo_activo = "Resumen"

if btn_resumen: st.session_state.modulo_activo = "Resumen"
if btn_semanal: st.session_state.modulo_activo = "Semanal"
if btn_clientes: st.session_state.modulo_activo = "Clientes"

st.markdown("---")

if not df_sales.empty:
    
    # --- MÓDULO 1: RESUMEN GENERAL ---
    if st.session_state.modulo_activo == "Resumen":
        st.subheader("Indicadores de Rendimiento Comercial")
        
        # Agrupación Mensual
        resumen_mensual = df_sales.groupby('MES')['Venta Neta Real'].sum().reset_index()
        orden_meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
        resumen_mensual['MES'] = pd.Categorical(resumen_mensual['MES'], categories=orden_meses, ordered=True)
        resumen_mensual = resumen_mensual.sort_values('MES')

        # Cálculo de Métricas
        total_acumulado = resumen_mensual['Venta Neta Real'].sum()
        promedio_mensual = resumen_mensual['Venta Neta Real'].mean()
        
        # VENTA PROMEDIO DIARIA (Total / (meses transcurridos * días configurados))
        num_meses = len(resumen_mensual[resumen_mensual['Venta Neta Real'] > 0])
        promedio_diario_global = total_acumulado / (num_meses * dias_mes) if num_meses > 0 else 0

        # Mostrar métricas principales
        k1, k2, k3 = st.columns(3)
        k1.metric("Venta Total Acumulada", f"${total_acumulado:,.0f}")
        k2.metric("Promedio Mensual", f"${promedio_mensual:,.0f}")
        k3.metric("Venta Promedio Diaria", f"${promedio_diario_global:,.0f}", help=f"Basado en {dias_mes} días por mes.")

        st.markdown("#### Evolución Mensual")
        fig_mes = px.bar(
            resumen_mensual, 
            x='MES', 
            y='Venta Neta Real',
            text_auto='.2s',
            title="Ingresos Consolidados por Mes",
            color_discrete_sequence=['#1E88E5']
        )
        st.plotly_chart(fig_mes, use_container_width=True)

        st.markdown("#### Detalle por Mes con Promedio Diario")
        # Agregar columna calculada a la tabla para mayor transparencia
        resumen_mensual['Promedio Diario'] = resumen_mensual['Venta Neta Real'] / dias_mes
        st.dataframe(resumen_mensual, use_container_width=True)

    # --- MÓDULO 2: DETALLE SEMANAL ---
    elif st.session_state.modulo_activo == "Semanal":
        st.subheader("Desglose por Períodos Semanales")
        
        meses_disponibles = sorted(df_sales['MES'].unique())
        mes_f = st.selectbox("Selecciona un Mes para auditar:", meses_disponibles)
        df_mes_f = df_sales[df_sales['MES'] == mes_f]
        
        resumen_semanal = df_mes_f.groupby('SEMANA')['Venta Neta Real'].sum().reset_index()
        resumen_semanal = resumen_semanal.sort_values('SEMANA')

        # Visualización de gráfico
        fig_sem = px.pie(
            resumen_semanal, 
            values='Venta Neta Real', 
            names='SEMANA',
            title=f"Distribución de Ingresos - {mes_f}",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_sem, use_container_width=True)
        
        # Tabla resumen por semana solicitada
        st.markdown(f"#### Resumen de Totales por Semana en {mes_f}")
        st.dataframe(resumen_semanal, use_container_width=True)
        
    # --- MÓDULO 3: RANKING DE CLIENTES ---
    elif st.session_state.modulo_activo == "Clientes":
        st.subheader("Top Clientes por Volumen de Compra")
        
        # Agrupación por cliente (totalizado)
        ranking = df_sales.groupby('Cliente')['Venta Neta Real'].sum().reset_index()
        ranking = ranking.sort_values(by='Venta Neta Real', ascending=False)
        
        # Gráfico de los mejores 15
        top_15 = ranking.head(15)
        fig_ranking = px.bar(
            top_15, 
            y='Cliente', 
            x='Venta Neta Real',
            orientation='h',
            title="Top 15 Clientes (Venta Neta Acumulada)",
            text_auto='.2s',
            color='Venta Neta Real',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

        # Tabla totalizada por cliente solicitada
        st.markdown("#### Tabla General de Clientes (Totalizados)")
        st.dataframe(ranking, use_container_width=True)

else:
    st.warning("⚠️ Sin datos para procesar. Verifica el acceso al Google Sheet.")

st.markdown("---")
st.caption("Stockify SaleMetric | Herramienta de Soporte a la Decisión")
