import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

# --- Configuración de las URLs de Google Drive ---
# 1. Hoja de Ventas General
GOOGLE_SALES_URL = 'https://docs.google.com/spreadsheets/d/1UNXW4LFYfc-P4eO-wVkav9FCSZtwC2Rw00cHZOQY5DI/export?format=xlsx'

# 2. Hoja de Vendedores (Configurada con el nuevo enlace)
GOOGLE_VEND_URL = 'https://docs.google.com/spreadsheets/d/1vPLWxKrsnBlPYUV0-ogv65gWbdvw6N_m2kTI13r1uOU/export?format=xlsx' 

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="SaleMetric | Business Intelligence", page_icon="📈")

# Estilos personalizados
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1565C0; font-weight: bold; }
    .stSelectbox label { font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- Funciones de Carga de Datos ---
@st.cache_data
def load_data(url, columns_required):
    if not url: return pd.DataFrame()
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        df.columns = [c.strip() for c in df.columns]
        
        if not all(col in df.columns for col in columns_required):
            st.error(f"Faltan columnas en el archivo. Se requiere: {', '.join(columns_required)}")
            st.info(f"Columnas detectadas: {df.columns.tolist()}")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"Error al cargar datos de {url}: {e}")
        return pd.DataFrame()

# Cargar DataFrames
df_sales = load_data(GOOGLE_SALES_URL, ['Cliente', 'Venta Neta Real', 'SEMANA', 'MES'])
df_vend = load_data(GOOGLE_VEND_URL, ['Vendedor', 'Venta Neta Real'])

# --- Título Principal ---
st.title('📈 SaleMetric - Inteligencia de Negocios')
st.markdown("---")

# --- Barra Lateral ---
st.sidebar.header("⚙️ Configuración")
dias_mes = st.sidebar.number_input("Días de operación al mes:", min_value=1, max_value=31, value=30)

# --- Navegación (4 Columnas) ---
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
with col_nav1:
    btn_resumen = st.button("📊 Resumen", use_container_width=True)
with col_nav2:
    btn_semanal = st.button("📅 Semanal", use_container_width=True)
with col_nav3:
    btn_clientes = st.button("👥 Clientes", use_container_width=True)
with col_nav4:
    btn_vendedores = st.button("👤 Vendedores", use_container_width=True)

if 'modulo_activo' not in st.session_state:
    st.session_state.modulo_activo = "Resumen"

if btn_resumen: st.session_state.modulo_activo = "Resumen"
if btn_semanal: st.session_state.modulo_activo = "Semanal"
if btn_clientes: st.session_state.modulo_activo = "Clientes"
if btn_vendedores: st.session_state.modulo_activo = "Vendedores"

st.markdown("---")

# --- MÓDULOS ---

if st.session_state.modulo_activo == "Resumen" and not df_sales.empty:
    st.subheader("Indicadores de Rendimiento Comercial")
    resumen_mensual = df_sales.groupby('MES')['Venta Neta Real'].sum().reset_index()
    orden_meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    resumen_mensual['MES'] = pd.Categorical(resumen_mensual['MES'], categories=orden_meses, ordered=True)
    resumen_mensual = resumen_mensual.sort_values('MES')

    total_acumulado = resumen_mensual['Venta Neta Real'].sum()
    promedio_mensual = resumen_mensual['Venta Neta Real'].mean()
    num_meses = len(resumen_mensual[resumen_mensual['Venta Neta Real'] > 0])
    promedio_diario_global = total_acumulado / (num_meses * dias_mes) if num_meses > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Venta Total Acumulada", f"${total_acumulado:,.0f}")
    k2.metric("Promedio Mensual", f"${promedio_mensual:,.0f}")
    k3.metric("Venta Promedio Diaria", f"${promedio_diario_global:,.0f}")

    fig_mes = px.bar(resumen_mensual, x='MES', y='Venta Neta Real', text_auto=True, title="Ingresos Mensuales", color_discrete_sequence=['#1E88E5'])
    fig_mes.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig_mes, use_container_width=True)

elif st.session_state.modulo_activo == "Semanal" and not df_sales.empty:
    st.subheader("Análisis Semanal")
    mes_f = st.selectbox("Selecciona un Mes:", sorted(df_sales['MES'].unique()))
    df_mes_f = df_sales[df_sales['MES'] == mes_f]
    resumen_semanal = df_mes_f.groupby('SEMANA')['Venta Neta Real'].sum().reset_index().sort_values('SEMANA')
    
    st.plotly_chart(px.pie(resumen_semanal, values='Venta Neta Real', names='SEMANA', hole=0.4, title=f"Ventas en {mes_f}"), use_container_width=True)
    st.dataframe(resumen_semanal.style.format({"Venta Neta Real": "${:,.0f}"}), use_container_width=True)

elif st.session_state.modulo_activo == "Clientes" and not df_sales.empty:
    st.subheader("Ranking de Clientes")
    ranking = df_sales.groupby('Cliente')['Venta Neta Real'].sum().reset_index().sort_values(by='Venta Neta Real', ascending=False)
    st.plotly_chart(px.bar(ranking.head(15), y='Cliente', x='Venta Neta Real', orientation='h', title="Top 15 Clientes", text_auto=True), use_container_width=True)
    st.dataframe(ranking.style.format({"Venta Neta Real": "${:,.0f}"}), use_container_width=True)

elif st.session_state.modulo_activo == "Vendedores":
    if not df_vend.empty:
        st.subheader("Desempeño por Vendedor")
        
        # Agrupar: Suma de ventas y Conteo de filas (Tickets)
        stats_vend = df_vend.groupby('Vendedor')['Venta Neta Real'].agg(['sum', 'count']).reset_index()
        stats_vend.columns = ['Vendedor', 'Venta Total', 'Tickets Emitidos']
        
        # Calcular Ticket Promedio
        stats_vend['Ticket Promedio'] = stats_vend['Venta Total'] / stats_vend['Tickets Emitidos']
        stats_vend = stats_vend.sort_values(by='Venta Total', ascending=False)

        # Gráfico Comparativo
        fig_vend = px.bar(stats_vend, x='Vendedor', y='Venta Total', text_auto='.2s', title="Venta Total por Vendedor", color='Tickets Emitidos')
        st.plotly_chart(fig_vend, use_container_width=True)

        # Tabla de Indicadores con formato
        st.markdown("#### Tabla de Rendimiento")
        st.dataframe(
            stats_vend.style.format({
                "Venta Total": "${:,.0f}",
                "Tickets Emitidos": "{:,.0f}",
                "Ticket Promedio": "${:,.0f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No se han podido cargar los datos de vendedores. Asegúrate de que el archivo tenga las columnas 'Vendedor' y 'Venta Neta Real' y que el enlace sea accesible.")

st.markdown("---")
st.caption("SaleMetric | Inteligencia Comercial")
