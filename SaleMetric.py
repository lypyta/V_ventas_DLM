import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests

# --- Configuración de las URLs de Google Drive ---
# 1. Hoja de Ventas General
GOOGLE_SALES_URL = 'https://docs.google.com/spreadsheets/d/1UNXW4LFYfc-P4eO-wVkav9FCSZtwC2Rw00cHZOQY5DI/export?format=xlsx'

# 2. Hoja de Vendedores
GOOGLE_VEND_URL = 'https://docs.google.com/spreadsheets/d/1SlUysxWzTF1zL441076J3-Av1DZpOEqAt_MkUBAReo0/export?format=xlsx' 

# 3. Hoja de Productos (URL Actualizada)
GOOGLE_PROD_URL = 'https://docs.google.com/spreadsheets/d/1v8-YlcX6kuXEjPndqgIj6itGPKmG5tyL_ud5exORebI/export?format=xlsx' 

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="SaleMetric | Business Intelligence", page_icon="📈")

# Estilos personalizados para métricas y legibilidad
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1565C0; font-weight: bold; }
    .stSelectbox label { font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- Funciones de Carga de Datos Inteligente ---
@st.cache_data
def load_data(url, columns_required):
    if not url: return pd.DataFrame()
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = io.BytesIO(response.content)
        
        # Escaneamos las primeras 20 filas para encontrar el encabezado real
        df_scan = pd.read_excel(content, engine='openpyxl', header=None, nrows=20)
        
        header_row = 0
        req_upper = [c.upper() for c in columns_required]
        
        for i, row in df_scan.iterrows():
            row_values = [str(val).strip().upper() for val in row.values if pd.notna(val)]
            if all(col in row_values for col in req_upper):
                header_row = i
                break
        
        content.seek(0)
        df = pd.read_excel(content, engine='openpyxl', header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        
        if not all(col in df.columns for col in columns_required):
            st.error(f"Faltan columnas en el archivo de {url}.")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# Cargar DataFrames
df_sales = load_data(GOOGLE_SALES_URL, ['Cliente', 'Venta Neta Real', 'SEMANA', 'MES'])
df_vend = load_data(GOOGLE_VEND_URL, ['Vendedor', 'Documento', 'Venta Neta Real', 'MES'])
df_prod = load_data(GOOGLE_PROD_URL, ['PRODUCTO', 'UNIDADES', 'TOTAL VENTA', 'MES'])

# --- Título ---
st.title('📈 SaleMetric - Inteligencia de Negocios')
st.markdown("---")

# --- Barra Lateral ---
st.sidebar.header("⚙️ Configuración Global")
dias_mes = st.sidebar.number_input("Días de operación al mes:", min_value=1, value=30)

# --- Navegación (5 Botones) ---
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)
with col_nav1: btn_resumen = st.button("📊 Resumen", use_container_width=True)
with col_nav2: btn_semanal = st.button("📅 Semanal", use_container_width=True)
with col_nav3: btn_clientes = st.button("👥 Clientes", use_container_width=True)
with col_nav4: btn_vendedores = st.button("👤 Vendedores", use_container_width=True)
with col_nav5: btn_productos = st.button("📦 Productos", use_container_width=True)

if 'modulo_activo' not in st.session_state: st.session_state.modulo_activo = "Resumen"
if btn_resumen: st.session_state.modulo_activo = "Resumen"
if btn_semanal: st.session_state.modulo_activo = "Semanal"
if btn_clientes: st.session_state.modulo_activo = "Clientes"
if btn_vendedores: st.session_state.modulo_activo = "Vendedores"
if btn_productos: st.session_state.modulo_activo = "Productos"

st.markdown("---")

# --- Módulos ---

# 1. RESUMEN GENERAL
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

# 2. ANÁLISIS SEMANAL
elif st.session_state.modulo_activo == "Semanal" and not df_sales.empty:
    st.subheader("Análisis Semanal")
    mes_f = st.selectbox("Selecciona un Mes:", sorted(df_sales['MES'].unique()), key="sem_mes")
    df_mes_f = df_sales[df_sales['MES'] == mes_f]
    resumen_semanal = df_mes_f.groupby('SEMANA')['Venta Neta Real'].sum().reset_index().sort_values('SEMANA')
    
    st.plotly_chart(px.pie(resumen_semanal, values='Venta Neta Real', names='SEMANA', hole=0.4, title=f"Ventas en {mes_f}"), use_container_width=True)
    st.dataframe(resumen_semanal.style.format({"Venta Neta Real": "${:,.0f}"}), use_container_width=True)

# 3. RANKING DE CLIENTES
elif st.session_state.modulo_activo == "Clientes" and not df_sales.empty:
    st.subheader("Ranking de Clientes")
    ranking = df_sales.groupby('Cliente')['Venta Neta Real'].sum().reset_index().sort_values(by='Venta Neta Real', ascending=False)
    st.plotly_chart(px.bar(ranking.head(15), y='Cliente', x='Venta Neta Real', orientation='h', title="Top 15 Clientes", text_auto=True), use_container_width=True)
    st.dataframe(ranking.style.format({"Venta Neta Real": "${:,.0f}"}), use_container_width=True)

# 4. DESEMPEÑO POR VENDEDOR
elif st.session_state.modulo_activo == "Vendedores":
    if not df_vend.empty:
        st.subheader("Desempeño por Vendedor")
        df_vend['MES'] = df_vend['MES'].astype(str).str.upper()
        mes_v_sel = st.selectbox("Selecciona el Mes:", sorted(df_vend['MES'].unique()), key="vend_mes")
        df_v_filt = df_vend[df_vend['MES'] == mes_v_sel]
        
        if not df_v_filt.empty:
            stats_v = df_v_filt.groupby('Vendedor').agg({'Venta Neta Real': 'sum', 'Documento': 'count'}).reset_index()
            stats_v.columns = ['Vendedor', 'Venta Total', 'Tickets Emitidos']
            stats_v['Ticket Promedio'] = stats_v['Venta Total'] / stats_v['Tickets Emitidos']
            stats_v = stats_v.sort_values(by='Venta Total', ascending=False)

            fig_v = px.bar(stats_v, x='Vendedor', y='Venta Total', text_auto=True, title=f"Venta por Vendedor - {mes_v_sel}")
            fig_v.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
            st.plotly_chart(fig_v, use_container_width=True)
            st.dataframe(stats_v.style.format({"Venta Total": "${:,.0f}", "Tickets Emitidos": "{:,.0f}", "Ticket Promedio": "${:,.0f}"}), use_container_width=True)
        else:
            st.warning(f"Sin datos de vendedores para {mes_v_sel}.")
    else:
        st.warning("⚠️ No se detectaron datos de vendedores.")

# 5. ANÁLISIS DE PRODUCTOS (NUEVO)
elif st.session_state.modulo_activo == "Productos":
    if not df_prod.empty:
        st.subheader("Análisis de Ventas por Producto")
        
        # Filtro de Mes
        df_prod['MES'] = df_prod['MES'].astype(str).str.upper()
        mes_p_sel = st.selectbox("Selecciona el Mes para el análisis de productos:", sorted(df_prod['MES'].unique()), key="prod_mes")
        df_p_filt = df_prod[df_prod['MES'] == mes_p_sel].copy()
        
        if not df_p_filt.empty:
            # AGRUPACIÓN Y UNIFICACIÓN
            stats_p = df_p_filt.groupby('PRODUCTO').agg({
                'UNIDADES': 'sum',
                'TOTAL VENTA': 'sum'
            }).reset_index()
            
            stats_p = stats_p.sort_values(by='TOTAL VENTA', ascending=False)

            # Visualización: Top Productos por Ingresos
            fig_p = px.bar(
                stats_p.head(15), 
                x='TOTAL VENTA', 
                y='PRODUCTO', 
                orientation='h',
                text_auto=True,
                title=f"Top 15 Productos por Ingresos - {mes_p_sel}",
                color='UNIDADES',
                color_continuous_scale='Viridis'
            )
            fig_p.update_traces(texttemplate='$%{x:,.0f}', textposition='outside')
            st.plotly_chart(fig_p, use_container_width=True)

            # Tabla Detallada
            st.markdown("#### Detalle Unificado de Productos")
            st.dataframe(
                stats_p.style.format({
                    "UNIDADES": "{:,.0f}",
                    "TOTAL VENTA": "${:,.0f}"
                }),
                use_container_width=True
            )
        else:
            st.warning(f"Sin registros de productos para {mes_p_sel}.")
    else:
        st.info("💡 Asegúrate de que el archivo de Productos tenga las columnas: 'PRODUCTO', 'UNIDADES', 'TOTAL VENTA' y 'MES'.")

st.markdown("---")
st.caption("SaleMetric | Inteligencia de Negocios")
```
