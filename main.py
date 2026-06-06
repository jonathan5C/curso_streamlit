import streamlit as st
import pandas as pd

def calc_general_stats(df: pd.DataFrame) -> pd.DataFrame:
    df_data = df.groupby(by='Data')[['Valor']].sum()

    df_data['lag_1'] = df_data['Valor'].shift(1)
    df_data['Diferença Mensal ABS'] = df_data["Valor"] - df_data['lag_1']
    df_data['Média 6M Diferença Mensal ABS'] = df_data['Diferença Mensal ABS'].rolling(6).mean()
    df_data['Média 12M Diferença Mensal ABS'] = df_data['Diferença Mensal ABS'].rolling(12).mean()
    df_data['Média 24M Diferença Mensal ABS'] = df_data['Diferença Mensal ABS'].rolling(14).mean()
    df_data['Diferença Mensal Rel'] = df_data["Valor"] / df_data['lag_1'] - 1    
    df_data['Evolução 6M Total'] = df_data['Valor'].rolling(6).apply(lambda x: x[-1] - x[0])
    df_data['Evolução 12M Total'] = df_data['Valor'].rolling(12).apply(lambda x: x[-1] - x[0])
    df_data['Evolução 24M Total'] = df_data['Valor'].rolling(14).apply(lambda x: x[-1] - x[0])
    df_data['Evolução 6M Relativa'] = df_data['Valor'].rolling(6).apply(lambda x: x[-1] / x[0] -1)
    df_data['Evolução 12M Relativa'] = df_data['Valor'].rolling(12).apply(lambda x: x[-1] / x[0] -1)
    df_data['Evolução 24M Relativa'] = df_data['Valor'].rolling(14).apply(lambda x: x[-1] / x[0] -1)
    
    df_data = df_data.drop('lag_1', axis=1)
    return df_data

st.set_page_config(page_title="Finanças", page_icon="💰")

st.markdown("""
# Boas vindas

## Nosso app financeiro!

Espero que você curta a experiência da nossa solução para organização financeira.
""")

# Widget de upload de dados
file_upload = st.file_uploader(label="Faça upload dos dados aqui", type=['csv'])

if file_upload:
    df = pd.read_csv(file_upload)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y').dt.date

    exp1 = st.expander("Dados Brutos")
    columns_fmt = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)
    
    df_instituicao = df.pivot_table(index='Data', columns='Instituição', values='Valor')
    exp2 = st.expander("Instituições")

    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)
    
    with tab_share:
        date = st.selectbox('Data', options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[date])
    
    exp3 = st.expander('Estatística Gerais')
    df_stats = calc_general_stats(df)

    columns_config = {
        'Diferença Mensal ABS': st.column_config.NumberColumn('Diferença Mensal ABS', format='R$ %.2f'), 
        'Média 6M Diferença Mensal ABS': st.column_config.NumberColumn('Média 6M Diferença Mensal ABS', format='R$ %.2f'),
        'Média 12M Diferença Mensal ABS': st.column_config.NumberColumn('Média 12M Diferença Mensal ABS', format='R$ %.2f'),
        'Média 24M Diferença Mensal ABS': st.column_config.NumberColumn('Média 24M Diferença Mensal ABS', format='R$ %.2f'),
        'Evolução 6M Total': st.column_config.NumberColumn('Evolução 6M Total', format='R$ %.2f'),
        'Evolução 12M Total': st.column_config.NumberColumn('Evolução 12M Total', format='R$ %.2f'),
        'Evolução 24M Total': st.column_config.NumberColumn('Evolução 24M Total', format='R$ %.2f'),
        'Diferença Mensal Rel': st.column_config.NumberColumn('Diferença Mensal Rel', format='percent'),
        'Evolução 6M Relativa': st.column_config.NumberColumn('Evolução 6M Relativa', format='percent'),  
        'Evolução 12M Relativa': st.column_config.NumberColumn('Evolução 12M Relativa', format='percent'),  
        'Evolução 24M Relativa': st.column_config.NumberColumn('Evolução 24M Relativa', format='percent'),  
    }

    tab_stats, tab_abs, tab_rel = exp3.tabs(tabs=['Dados', 'Histórico de evolução', 'Crescimento relativo'])

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:
        abs_colns = [
            'Diferença Mensal ABS',
            'Média 6M Diferença Mensal ABS',
            'Média 12M Diferença Mensal ABS',
            'Média 24M Diferença Mensal ABS',
        ]
        st.line_chart(df_stats[abs_colns])
    
    with tab_rel:
        rel_colns = [
            'Diferença Mensal Rel',
            'Evolução 6M Relativa',
            'Evolução 12M Relativa',
            'Evolução 24M Relativa',
        ]
        st.line_chart(df_stats[rel_colns])
    
    with st.expander('Metas'):
        col1, col2 = st.columns(2)

        data_inicio_meta = col1.date_input('Início de meta', max_value=df_stats.index.max())

        filter_data = df_stats.index <= data_inicio_meta
        data_filtrada = df_stats.index[filter_data][-1]


        custos_fixos = col1.number_input('Custos fixos', min_value=0., format='%.2f')
        salario_brut = col2.number_input('Salário bruto', min_value=0., format='%.2f')
        salario_liq = col2.number_input('Salário líquido', min_value=0., format='%.2f')

        col1_pot, col2_pot = st.columns(2)
        valor_inicio = df_stats.loc[data_filtrada]['Valor']
        col1.markdown(f'**Valor início meta:** R$ {valor_inicio:.2f}')

        mensal = salario_liq - custos_fixos
        with col1_pot.container(border=True):
            st.markdown(f'**Potencial arrecadação mensal:** \n\nR$ {mensal:.2f}')

        anual = mensal * 12
        with col2_pot.container(border=True):
            st.markdown(f'**Potencial arrecadação anual:** \n\nR$ {anual:.2f}')
        
        

        with st.container(border=True):
            coluna_meta01, coluna_meta02 = st.columns(2)

            with coluna_meta01:
                meta_estipulada = st.number_input('Meta estipulada', min_value=0., format='%.2f', value=anual)
            
            patrimonio_final = meta_estipulada + valor_inicio
            with coluna_meta02:
                st.markdown(f'Patrimônio estimado pós meta: \n\n R$ {patrimonio_final:.2f}')