import streamlit as st
import pandas as pd
from app.utils.state_manager import sync_sidebar_to_home, sync_sidebar_urg_to_home

def sidebar_filters(df, filter_config):
    """
    Renderiza filtros na sidebar e retorna o DataFrame filtrado e um dicionário de seleções.

    Args:
        df (pd.DataFrame): O DataFrame original para filtrar.
        filter_config (dict): Dicionário para configurar quais filtros mostrar e seus nomes de coluna.
                              Ex: {'ano': True, 'urg': True, 
                                   'escola': False, # home.py não quer filtro de escola na sidebar 
                                   'tipo': True # página com nome de coluna diferente
                                  }

    Returns:
        tuple: (df_filtrado, selections_dict)
               selections_dict é um dicionário contendo listas ordenadas e únicas das seleções
               efetivamente aplicadas para cada filtro. Se um filtro está desabilitado (via filter_config)
               ou nenhuma opção é selecionada pelo usuário (implicando "todos os itens daquele filtro"),
               a lista em selections_dict para aquela chave conterá todos os valores únicos e válidos
               da coluna original correspondente.
    """
    st.sidebar.header("Filtros")

    if df is None or df.empty:
        st.sidebar.warning("DataFrame de entrada está vazio ou é None. Nenhum filtro será aplicado.")
        empty_df_columns = df.columns if df is not None else []
        # Retorna um DataFrame vazio e um selections_dict vazio, mas com chaves esperadas se possível
        default_selections = {key: [] for key in ['ano', 'urg', 'escola', 'tipo'] if filter_config.get(key, False)}
        return pd.DataFrame(columns=empty_df_columns), default_selections

    # df_options_source é usado APENAS para obter as listas de opções disponíveis. Não é modificado por filtros.
    df_options_source = df.copy()
    # df_filtered é o DataFrame que será progressivamente filtrado.
    df_filtered = df.copy()
    selections_dict = {}

    # --- Lógica para Coluna 'Ano' (Derivação e Preparação das Opções) ---
    actual_ano_column_for_options = 'Ano' # Nome da coluna que contém os dados de ano em df_options_source
    anos_disponiveis_geral = []
    
    # Tenta usar 'Ano'. Se não existir ou for todo nulo, tenta derivar de colunas de data.
    if 'Ano' not in df_options_source.columns or df_options_source['Ano'].isnull().all():
        date_col_for_year = None
        if 'DtFechamento' in df_options_source.columns and pd.api.types.is_datetime64_any_dtype(df_options_source['DtFechamento']):
            date_col_for_year = 'DtFechamento'
        elif 'Data' in df_options_source.columns and pd.api.types.is_datetime64_any_dtype(df_options_source['Data']):
            date_col_for_year = 'Data'
        
        if date_col_for_year:
            # Deriva o ano em uma cópia para não alterar df_options_source permanentemente com a nova coluna
            temp_df_for_year_derivation = df_options_source.copy()
            temp_df_for_year_derivation['Ano_derived_temp'] = temp_df_for_year_derivation[date_col_for_year].dt.year
            actual_ano_column_for_options = 'Ano_derived_temp'
            # Adiciona a coluna derivada também ao df_filtered para poder filtrar por ela
            df_filtered['Ano_derived_temp'] = temp_df_for_year_derivation['Ano_derived_temp']
            
            if actual_ano_column_for_options in temp_df_for_year_derivation.columns:
                year_series = pd.to_numeric(temp_df_for_year_derivation[actual_ano_column_for_options], errors='coerce')
                anos_disponiveis_geral = sorted(list(year_series.dropna().astype(int).unique()))
    elif 'Ano' in df_options_source.columns: # 'Ano' existe e pode ter valores
        year_series = pd.to_numeric(df_options_source[actual_ano_column_for_options], errors='coerce')
        anos_disponiveis_geral = sorted(list(year_series.dropna().astype(int).unique()))

    # --- Filtro por Ano (Widget e Aplicação) ---
    if filter_config.get('ano', False):
        if not anos_disponiveis_geral and actual_ano_column_for_options in df_options_source.columns:
            st.sidebar.warning(f"Não há dados válidos de '{actual_ano_column_for_options}' disponíveis para filtrar.")
        
        anos_selecionados_usr = st.sidebar.multiselect(
            "Selecione o(s) Ano(s):",
            options=anos_disponiveis_geral,
            key="sidebar_year_filter",
            on_change=sync_sidebar_to_home,
            placeholder="Todos"
        )
        # Se nada selecionado pelo usuário, considera todos os anos disponíveis para o filtro
        anos_para_aplicar_filtro = anos_disponiveis_geral if not anos_selecionados_usr else [int(a) for a in anos_selecionados_usr]
        selections_dict['ano'] = anos_para_aplicar_filtro # Reflete a seleção efetiva
        
        if actual_ano_column_for_options in df_filtered.columns and anos_para_aplicar_filtro:
            # Garante que a coluna de ano no df_filtered também seja do tipo correto para comparação
            if pd.api.types.is_numeric_dtype(df_filtered[actual_ano_column_for_options]):
                 df_filtered[actual_ano_column_for_options] = pd.to_numeric(df_filtered[actual_ano_column_for_options], errors='coerce').astype('Int64')
            df_filtered = df_filtered[df_filtered[actual_ano_column_for_options].isin(anos_para_aplicar_filtro)]
    else:
        # Se filtro de ano não ativo na config, selections_dict reflete todas as opções disponíveis
        selections_dict['ano'] = anos_disponiveis_geral


    # --- Filtro por URG ---
    urg_col_config_name = filter_config.get('urg_col_name', 'URG') # Nome da coluna URG a ser usada
    urgs_disponiveis_geral = sorted(list(df_options_source[urg_col_config_name].dropna().unique())) if urg_col_config_name in df_options_source.columns else []
    urgs_selecionadas_usr = [] # Inicializa para evitar NameError no filtro de escola

    if filter_config.get('urg', False):
        if not urgs_disponiveis_geral and urg_col_config_name in df_options_source.columns:
            st.sidebar.warning(f"Não há dados de '{urg_col_config_name}' disponíveis para filtrar.")

        urgs_selecionadas_usr = st.sidebar.multiselect(
            "Selecione a(s) URG(s):",
            options=urgs_disponiveis_geral,
            key="sidebar_urg_filter",
            on_change=sync_sidebar_urg_to_home,
            placeholder="Todas"
        )
        urgs_para_aplicar_filtro = urgs_disponiveis_geral if not urgs_selecionadas_usr else urgs_selecionadas_usr
        selections_dict['urg'] = urgs_para_aplicar_filtro
        if urg_col_config_name in df_filtered.columns and urgs_para_aplicar_filtro:
            df_filtered = df_filtered[df_filtered[urg_col_config_name].isin(urgs_para_aplicar_filtro)]
    else:
        selections_dict['urg'] = urgs_disponiveis_geral

    # --- Filtro por Escola ---
    escola_column_name = 'Escola' 
    if filter_config.get('escola', False):
        # Lógica de cascata: se URG selecionada, filtra escolas disponíveis
        if urgs_selecionadas_usr and urg_col_config_name in df_options_source.columns:
            df_escolas_filtradas = df_options_source[df_options_source[urg_col_config_name].isin(urgs_selecionadas_usr)]
            escolas_disponiveis = sorted(list(df_escolas_filtradas[escola_column_name].dropna().unique()))
        else:
            escolas_disponiveis = sorted(list(df_options_source[escola_column_name].dropna().unique())) if escola_column_name in df_options_source.columns else []

        if not escolas_disponiveis and escola_column_name in df_options_source.columns:
            st.sidebar.warning("Não há escolas disponíveis para a URG selecionada.")

        escolas_selecionadas_usr = st.sidebar.multiselect(
            "Selecione a(s) Escola(s):",
            options=escolas_disponiveis,
            default=[],
            placeholder="Todas as Escolas",
            key="sidebar_escola_filter"
        )
        escolas_para_aplicar_filtro = escolas_disponiveis if not escolas_selecionadas_usr else escolas_selecionadas_usr
        selections_dict['escola'] = escolas_para_aplicar_filtro
        if escola_column_name in df_filtered.columns and escolas_para_aplicar_filtro:
            df_filtered = df_filtered[df_filtered[escola_column_name].isin(escolas_para_aplicar_filtro)]
    else:
        # Se o filtro não está ativo, retorna todas as escolas do dataset original para o selections_dict
        escolas_disponiveis_geral = sorted(list(df_options_source[escola_column_name].dropna().unique())) if escola_column_name in df_options_source.columns else []
        selections_dict['escola'] = escolas_disponiveis_geral

    # --- Filtro por Tipo (de Escola/Instituição) ---
    tipo_column_name = 'Tipo' # Nome padrão da coluna para este tipo de filtro
    tipos_disponiveis_geral = [] # Inicializa

    if filter_config.get('tipo', False):
        # O filtro de Tipo só é renderizado se a coluna existir no DataFrame
        if tipo_column_name in df_options_source.columns:
            tipos_disponiveis_geral = sorted(list(df_options_source[tipo_column_name].dropna().unique()))
            
            tipos_selecionados_usr = st.sidebar.multiselect(
                "Selecione o(s) Tipo(s):",
                options=tipos_disponiveis_geral,
                default=[],
                placeholder="Todos",
                key="sidebar_tipo_filter"
            )
            tipos_para_aplicar_filtro = tipos_disponiveis_geral if not tipos_selecionados_usr else tipos_selecionados_usr
            selections_dict['tipo'] = tipos_para_aplicar_filtro
            
            if tipo_column_name in df_filtered.columns and tipos_para_aplicar_filtro:
                df_filtered = df_filtered[df_filtered[tipo_column_name].isin(tipos_para_aplicar_filtro)]
        else:
            # Coluna não existe: limpa a seleção para não afetar a lógica a jusante
            selections_dict['tipo'] = []
    else:
        # O filtro 'tipo' não está ativo. Popula selections_dict com todas as opções disponíveis da coluna 'Tipo', se existir.
        if tipo_column_name in df_options_source.columns:
            selections_dict['tipo'] = sorted(list(df_options_source[tipo_column_name].dropna().unique()))
        else:
            selections_dict['tipo'] = []

    # Remove a coluna temporária de ano derivado, se foi criada e ainda existe no df_filtered
    if actual_ano_column_for_options == 'Ano_derived_temp' and 'Ano_derived_temp' in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=['Ano_derived_temp'])

    return df_filtered.copy(), selections_dict
