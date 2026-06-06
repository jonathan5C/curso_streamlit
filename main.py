import streamlit as st
import pandas as pd

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