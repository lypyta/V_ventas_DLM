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
# 3. Hoja de Productos
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

# Lista maestra para orden cronológico de meses
ORDEN_MESES = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']

# --- Función de Carga de Datos Inteligente ---
@st.cache_data(ttl=600)
def load_data(url, columns_required):
    if not url: return pd.DataFrame()
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = io.BytesIO(response.content)
        
        # Escaneamos las primeras 20 filas para encontrar el encabezado real saltando títulos
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
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Normalización de datos críticos
        if 'MES' in df.columns:
            df['MES'] = df['MES'].astype(str).str.upper().str.strip()
        if 'SEMANA' in df.columns:
            df['SEMANA'] = df['SEMANA'].astype(str).str.upper().str.strip()
        if 'VENTA NETA REAL' in df.columns:
            df['VENTA NETA REAL'] = pd.to_numeric(df['VENTA NETA REAL'], errors='coerce').fillna(0)
        if 'TOTAL VENTA' in df.columns:
            df['TOTAL VENTA'] = pd.to_numeric(df['TOTAL VENTA'], errors='coerce').fillna(0)
        if 'UNIDADES' in df.columns:
            df['UNIDADES'] = pd.to_numeric(df['UNIDADES'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# --- Barra Lateral (Configuración y Botón de Refrescar) ---
st.sidebar.header("⚙️ Configuración Global")

# Botón para forzar actualización de datos
if st.sidebar.button("🔄 Refrescar Datos (Actualizar Hojas)"):
    st.cache_data.clear()
    st.success("¡Memoria limpiada! Cargando datos nuevos...")
    st.rerun()

dias_mes = st.sidebar.number_input("Días de operación al mes:", min_value=1, value=30)

# Carga de los 3 archivos
df_sales = load_data(GOOGLE_SALES_URL, ['CLIENTE', 'VENTA NETA REAL', 'SEMANA', 'MES'])
df_vend = load_data(GOOGLE_VEND_URL, ['VENDEDOR', 'DOCUMENTO', 'VENTA NETA REAL', 'MES'])
df_prod = load_data(GOOGLE_PROD_URL, ['PRODUCTO', 'UNIDADES', 'TOTAL VENTA', 'MES'])

# -------------------- Título -----------------------
st.title('📈 Metricas de venta - Actualizado al 15/02/2026 ')
st.markdown("---")

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

# --- Módulos de Análisis ---

# 1. RESUMEN GENERAL
if st.session_state.modulo_activo == "Resumen" and not df_sales.empty:
    st.subheader("Indicadores de Rendimiento Comercial")
    
    meses_disponibles = [m for m in ORDEN_MESES if m in df_sales['MES'].unique()]
    mes_sel = st.selectbox("Analizar periodo:", ["TODOS LOS MESES"] + meses_disponibles)
    
    if mes_sel == "TODOS LOS MESES":
        df_resumen = df_sales
        num_meses_activos = len(df_sales['MES'].unique())
    else:
        df_resumen = df_sales[df_sales['MES'] == mes_sel]
        num_meses_activos = 1
    
    total_acumulado = df_resumen['VENTA NETA REAL'].sum()
    promedio_mensual = df_sales.groupby('MES')['VENTA NETA REAL'].sum().mean()
    promedio_diario = total_acumulado / (num_meses_activos * dias_mes)

    k1, k2, k3 = st.columns(3)
    k1.metric("Venta Total", f"${total_acumulado:,.0f}")
    k2.metric("Promedio Mensual (General)", f"${promedio_mensual:,.0f}")
    k3.metric("Venta Promedio Diaria", f"${promedio_diario:,.0f}")

    # Tabla de Ventas por Mes solicitada
    st.markdown("#### Detalle de Ventas Mensuales")
    resumen_tabla = df_sales.groupby('MES')['VENTA NETA REAL'].sum().reset_index()
    resumen_tabla['MES'] = pd.Categorical(resumen_tabla['MES'], categories=ORDEN_MESES, ordered=True)
    resumen_tabla = resumen_tabla.sort_values('MES').dropna(subset=['VENTA NETA REAL'])
    st.dataframe(resumen_tabla.style.format({"VENTA NETA REAL": "${:,.0f}"}), hide_index=True, use_container_width=True)

    # Gráfico de Evolución Mensual
    fig_mes = px.bar(resumen_tabla, x='MES', y='VENTA NETA REAL', text_auto=True, title="Evolución de Ingresos Mensuales", color_discrete_sequence=['#1E88E5'])
    fig_mes.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig_mes, use_container_width=True)

# 2. ANÁLISIS SEMANAL
elif st.session_state.modulo_activo == "Semanal" and not df_sales.empty:
    st.subheader("Análisis Semanal")
    meses_disponibles = [m for m in ORDEN_MESES if m in df_sales['MES'].unique()]
    mes_f = st.selectbox("Selecciona un Mes:", meses_disponibles, key="sem_mes")
    
    df_mes_f = df_sales[df_sales['MES'] == mes_f]
    total_mes_seleccionado = df_mes_f['VENTA NETA REAL'].sum()
    st.metric(f"Venta Total de {mes_f}", f"${total_mes_seleccionado:,.0f}")
    
    resumen_semanal = df_mes_f.groupby('SEMANA')['VENTA NETA REAL'].sum().reset_index().sort_values(by='VENTA NETA REAL', ascending=False)
    
    st.plotly_chart(px.pie(resumen_semanal, values='VENTA NETA REAL', names='SEMANA', hole=0.4, title=f"Distribución de Ventas en {mes_f}"), use_container_width=True)
    st.markdown("#### Totales por Semana")
    st.dataframe(resumen_semanal.style.format({"VENTA NETA REAL": "${:,.0f}"}), hide_index=True, use_container_width=True)

# 3. RANKING DE CLIENTES
elif st.session_state.modulo_activo == "Clientes" and not df_sales.empty:
    st.subheader("Ranking de Clientes")
    
    meses_cli = [m for m in ORDEN_MESES if m in df_sales['MES'].unique()]
    opciones_mes = ["GLOBAL"] + meses_cli
    mes_c_sel = st.selectbox("Selecciona el Periodo:", opciones_mes, key="cli_mes")
    
    if mes_c_sel == "GLOBAL":
        df_cli_filt = df_sales
        label_total = "Venta Total Global"
    else:
        df_cli_filt = df_sales[df_sales['MES'] == mes_c_sel]
        label_total = f"Venta Total en {mes_c_sel}"
        
    monto_total_cli = df_cli_filt['VENTA NETA REAL'].sum()
    st.metric(label_total, f"${monto_total_cli:,.0f}")
    
    ranking = df_cli_filt.groupby('CLIENTE')['VENTA NETA REAL'].sum().reset_index().sort_values(by='VENTA NETA REAL', ascending=False)
    
    # Agregar columna de Ranking Numérico (1 a X)
    ranking.insert(0, 'RANKING', range(1, 1 + len(ranking)))
    
    fig_cli = px.bar(
        ranking.head(15), 
        y='CLIENTE', 
        x='VENTA NETA REAL', 
        orientation='h', 
        title=f"Top 15 Clientes ({mes_c_sel})", 
        text_auto=True,
        color='VENTA NETA REAL',
        color_continuous_scale='Blues'
    )
    fig_cli.update_traces(texttemplate='$%{x:,.0f}', textposition='outside')
    fig_cli.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_cli, use_container_width=True)
    
    st.markdown(f"#### Detalle de Clientes - {mes_c_sel}")
    st.dataframe(ranking.style.format({"VENTA NETA REAL": "${:,.0f}"}), hide_index=True, use_container_width=True)

# 4. DESEMPEÑO POR VENDEDOR
elif st.session_state.modulo_activo == "Vendedores":
    if not df_vend.empty:
        st.subheader("Desempeño por Vendedor")
        
        # Filtro dinámico por Mes o Global
        meses_v = [m for m in ORDEN_MESES if m in df_vend['MES'].unique()]
        opciones_v = ["GLOBAL"] + meses_v
        mes_v_sel = st.selectbox("Selecciona el Periodo:", opciones_v, key="vend_mes")
        
        if mes_v_sel == "GLOBAL":
            df_v_filt = df_vend
            label_v = "Venta Total Global (Vendedores)"
        else:
            df_v_filt = df_vend[df_vend['MES'] == mes_v_sel]
            label_v = f"Venta Total en {mes_v_sel}"
            
        monto_v = df_v_filt['VENTA NETA REAL'].sum()
        st.metric(label_v, f"${monto_v:,.0f}")
        
        if not df_v_filt.empty:
            stats_v = df_v_filt.groupby('VENDEDOR').agg({'VENTA NETA REAL': 'sum', 'DOCUMENTO': 'count'}).reset_index()
            stats_v.columns = ['Vendedor', 'Venta Total', 'Tickets Emitidos']
            stats_v['Ticket Promedio'] = stats_v['Venta Total'] / stats_v['Tickets Emitidos']
            stats_v = stats_v.sort_values(by='Venta Total', ascending=False)
            
            # Ranking Numérico para Vendedores
            stats_v.insert(0, 'RANKING', range(1, 1 + len(stats_v)))

            fig_v = px.bar(stats_v, x='Vendedor', y='Venta Total', text_auto=True, title=f"Venta por Vendedor - {mes_v_sel}", color='Tickets Emitidos')
            fig_v.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
            st.plotly_chart(fig_v, use_container_width=True)
            st.dataframe(stats_v.style.format({"Venta Total": "${:,.0f}", "Tickets Emitidos": "{:,.0f}", "Ticket Promedio": "${:,.0f}"}), hide_index=True, use_container_width=True)
        else:
            st.warning(f"Sin datos registrados para {mes_v_sel}.")
    else:
        st.warning("⚠️ No se pudieron cargar datos de vendedores.")

# 5. ANÁLISIS DE PRODUCTOS
elif st.session_state.modulo_activo == "Productos":
    if not df_prod.empty:
        st.subheader("Análisis de Ventas por Producto")
        
        # Filtro dinámico por Mes o Global
        meses_p = [m for m in ORDEN_MESES if m in df_prod['MES'].unique()]
        opciones_p = ["GLOBAL"] + meses_p
        mes_p_sel = st.selectbox("Selecciona el Periodo:", opciones_p, key="prod_mes")
        
        if mes_p_sel == "GLOBAL":
            df_p_filt = df_prod
            label_p = "Venta Total Global (Productos)"
        else:
            df_p_filt = df_prod[df_prod['MES'] == mes_p_sel]
            label_p = f"Venta Total en {mes_p_sel}"

        monto_p = df_p_filt['TOTAL VENTA'].sum()
        st.metric(label_p, f"${monto_p:,.0f}")
        
        if not df_p_filt.empty:
            stats_p = df_p_filt.groupby('PRODUCTO').agg({'UNIDADES': 'sum', 'TOTAL VENTA': 'sum'}).reset_index()
            stats_p = stats_p.sort_values(by='TOTAL VENTA', ascending=False)
            
            # Agregar columna de Ranking Numérico (1 a X)
            stats_p.insert(0, 'RANKING', range(1, 1 + len(stats_p)))

            fig_p = px.bar(
                stats_p.head(15), 
                x='TOTAL VENTA', 
                y='PRODUCTO', 
                orientation='h', 
                text_auto=True, 
                title=f"Top 15 Productos - {mes_p_sel}", 
                color='UNIDADES', 
                color_continuous_scale='Viridis'
            )
            fig_p.update_traces(texttemplate='$%{x:,.0f}', textposition='outside')
            fig_p.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_p, use_container_width=True)
            st.dataframe(stats_p.style.format({"UNIDADES": "{:,.0f}", "TOTAL VENTA": "${:,.0f}"}), hide_index=True, use_container_width=True)
        else:
            st.warning(f"Sin registros de productos para {mes_p_sel}.")

st.markdown("---")
st.caption("SaleMetric | Business Intelligence System")
