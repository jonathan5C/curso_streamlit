import datetime

import pandas as pd
import requests
import streamlit as st


@st.cache_data(ttl="1day")
def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    response = requests.get(url)
    df = pd.DataFrame(response.json()["conteudo"])

    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(
        datetime.datetime.today().date()
    )
    return df


def calc_general_stats(df: pd.DataFrame) -> pd.DataFrame:
    df_data = df.groupby(by="Data")[["Valor"]].sum()

    df_data["lag_1"] = df_data["Valor"].shift(1)
    df_data["Diferença Mensal ABS"] = df_data["Valor"] - df_data["lag_1"]
    df_data["Média 6M Diferença Mensal ABS"] = (
        df_data["Diferença Mensal ABS"].rolling(6).mean()
    )
    df_data["Média 12M Diferença Mensal ABS"] = (
        df_data["Diferença Mensal ABS"].rolling(12).mean()
    )
    df_data["Média 24M Diferença Mensal ABS"] = (
        df_data["Diferença Mensal ABS"].rolling(14).mean()
    )
    df_data["Diferença Mensal Rel"] = df_data["Valor"] / df_data["lag_1"] - 1
    df_data["Evolução 6M Total"] = (
        df_data["Valor"].rolling(6).apply(lambda x: x[-1] - x[0])
    )
    df_data["Evolução 12M Total"] = (
        df_data["Valor"].rolling(12).apply(lambda x: x[-1] - x[0])
    )
    df_data["Evolução 24M Total"] = (
        df_data["Valor"].rolling(14).apply(lambda x: x[-1] - x[0])
    )
    df_data["Evolução 6M Relativa"] = (
        df_data["Valor"].rolling(6).apply(lambda x: x[-1] / x[0] - 1)
    )
    df_data["Evolução 12M Relativa"] = (
        df_data["Valor"].rolling(12).apply(lambda x: x[-1] / x[0] - 1)
    )
    df_data["Evolução 24M Relativa"] = (
        df_data["Valor"].rolling(14).apply(lambda x: x[-1] / x[0] - 1)
    )

    df_data = df_data.drop("lag_1", axis=1)
    return df_data


def main_metas():
    col1, col2 = st.columns(2)

    data_inicio_meta = col1.date_input("Início de meta", max_value=df_stats.index.max())
    custos_fixos = col1.number_input("Custos fixos", min_value=0.0, format="%.2f")
    salario_brut = col2.number_input("Salário bruto", min_value=0.0, format="%.2f")
    salario_liq = col2.number_input("Salário líquido", min_value=0.0, format="%.2f")

    filter_data = df_stats.index <= data_inicio_meta
    data_filtrada = df_stats.index[filter_data][-1]
    valor_inicio = df_stats.loc[data_filtrada]["Valor"]
    col1.markdown(f"**Valor início meta:** R$ {valor_inicio:.2f}")

    selic_gov = get_selic()
    filter_selic_date = (selic_gov["DataInicioVigencia"] < data_inicio_meta) & (
        selic_gov["DataFimVigencia"] > data_inicio_meta
    )
    selic_default = selic_gov[filter_selic_date]["MetaSelic"].iloc[0]
    selic = st.number_input("SELIC", min_value=0.0, value=selic_default, format="%.2f")
    selic_ano = selic / 100
    selic_mes = (selic_ano + 1) ** (1 / 12) - 1

    rendimento_ano = valor_inicio * selic_ano
    rendimento_mes = valor_inicio * selic_mes

    col1_pot, col2_pot = st.columns(2)

    mensal = salario_liq - custos_fixos + rendimento_mes
    with col1_pot.container(border=True):
        st.markdown(
            f"**Potencial arrecadação mensal:** \n\nR$ {mensal:.2f}",
            help=f"{salario_liq:.2f} + (-{custos_fixos:.2f}) + {rendimento_mes:.2f}",
        )

    anual = 12 * (salario_liq - custos_fixos) + rendimento_ano
    with col2_pot.container(border=True):
        st.markdown(
            f"**Potencial arrecadação anual:** \n\nR$ {anual:.2f} + {rendimento_ano:.2f}",
            help=f"12 * ({salario_liq:.2f} + (-{custos_fixos:.2f})) + {rendimento_ano:.2f}",
        )

    with st.container(border=True):
        coluna_meta01, coluna_meta02 = st.columns(2)

        with coluna_meta01:
            meta_estipulada = st.number_input(
                "Meta estipulada", min_value=0.0, format="%.2f", value=anual
            )

        patrimonio_final = meta_estipulada + valor_inicio
        with coluna_meta02:
            st.markdown(f"Patrimônio estimado pós meta: \n\n R$ {patrimonio_final:.2f}")

    return data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final


st.set_page_config(page_title="Finanças", page_icon="💰")

st.markdown("""
# Boas vindas

## Nosso app financeiro!

Espero que você curta a experiência da nossa solução para organização financeira.
""")

# Widget de upload de dados
file_upload = st.file_uploader(label="Faça upload dos dados aqui", type=["csv"])

if file_upload:
    df = pd.read_csv(file_upload)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date

    exp1 = st.expander("Dados Brutos")
    columns_fmt = {"Valor": st.column_config.NumberColumn("Valor", format="R$ %f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)

    df_instituicao = df.pivot_table(index="Data", columns="Instituição", values="Valor")
    exp2 = st.expander("Instituições")

    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    with tab_data:
        st.dataframe(df_instituicao)

    with tab_history:
        st.line_chart(df_instituicao)

    with tab_share:
        date = st.selectbox("Data", options=df_instituicao.index)
        st.bar_chart(df_instituicao.loc[date])

    exp3 = st.expander("Estatística Gerais")
    df_stats = calc_general_stats(df)

    columns_config = {
        "Diferença Mensal ABS": st.column_config.NumberColumn(
            "Diferença Mensal ABS", format="R$ %.2f"
        ),
        "Média 6M Diferença Mensal ABS": st.column_config.NumberColumn(
            "Média 6M Diferença Mensal ABS", format="R$ %.2f"
        ),
        "Média 12M Diferença Mensal ABS": st.column_config.NumberColumn(
            "Média 12M Diferença Mensal ABS", format="R$ %.2f"
        ),
        "Média 24M Diferença Mensal ABS": st.column_config.NumberColumn(
            "Média 24M Diferença Mensal ABS", format="R$ %.2f"
        ),
        "Evolução 6M Total": st.column_config.NumberColumn(
            "Evolução 6M Total", format="R$ %.2f"
        ),
        "Evolução 12M Total": st.column_config.NumberColumn(
            "Evolução 12M Total", format="R$ %.2f"
        ),
        "Evolução 24M Total": st.column_config.NumberColumn(
            "Evolução 24M Total", format="R$ %.2f"
        ),
        "Diferença Mensal Rel": st.column_config.NumberColumn(
            "Diferença Mensal Rel", format="percent"
        ),
        "Evolução 6M Relativa": st.column_config.NumberColumn(
            "Evolução 6M Relativa", format="percent"
        ),
        "Evolução 12M Relativa": st.column_config.NumberColumn(
            "Evolução 12M Relativa", format="percent"
        ),
        "Evolução 24M Relativa": st.column_config.NumberColumn(
            "Evolução 24M Relativa", format="percent"
        ),
    }

    tab_stats, tab_abs, tab_rel = exp3.tabs(
        tabs=["Dados", "Histórico de evolução", "Crescimento relativo"]
    )

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:
        abs_colns = [
            "Diferença Mensal ABS",
            "Média 6M Diferença Mensal ABS",
            "Média 12M Diferença Mensal ABS",
            "Média 24M Diferença Mensal ABS",
        ]
        st.line_chart(df_stats[abs_colns])

    with tab_rel:
        rel_colns = [
            "Diferença Mensal Rel",
            "Evolução 6M Relativa",
            "Evolução 12M Relativa",
            "Evolução 24M Relativa",
        ]
        st.line_chart(df_stats[rel_colns])

    with st.expander("Metas"):
        tab_main, tab_data_meta, tab_graph = st.tabs(
            tabs=["Configuração", "Dados", "Gráficos"]
        )

        with tab_main:
            data_inicio_meta, valor_inicio, meta_estipulada, patrimonio_final = (
                main_metas()
            )

        with tab_data_meta:
            meses = pd.DataFrame(
                {
                    "Data Referência": [
                        (data_inicio_meta + pd.DateOffset(months=i))
                        for i in range(1, 13)
                    ],
                    "Meta Mensal": [
                        valor_inicio + round(meta_estipulada / 12, 2) * i
                        for i in range(1, 13)
                    ],
                }
            )

            meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(
                df_patrimonio["Data"]
            ).dt.strftime("%Y-%m")
            meses = meses.merge(df_patrimonio, how="left", on="Data Referência")

            meses = meses[["Data Referência", "Meta Mensal", "Valor"]]
            meses["Atingimento (%)"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Ano"] = meses["Valor"] / patrimonio_final
            meses["Atingimento Esperado"] = meses["Meta Mensal"] / patrimonio_final
            meses = meses.set_index("Data Referência")

            columns_config_meses = {
                "Meta Mensal": st.column_config.NumberColumn(
                    "Meta Mensal", format="R$ %.2f"
                ),
                "Valor": st.column_config.NumberColumn(
                    "Valor Atingido", format="R$ %.2f"
                ),
                "Atingimento (%)": st.column_config.NumberColumn(
                    "Atingimento (%)", format="percent"
                ),
                "Atingimento Ano": st.column_config.NumberColumn(
                    "Atingimento ano", format="percent"
                ),
                "Atingimento Esperado": st.column_config.NumberColumn(
                    "Atingimento Esperado", format="percent"
                ),
            }

            st.dataframe(meses, column_config=columns_config_meses)

        with tab_graph:
            st.line_chart(meses[["Atingimento Ano", "Atingimento Esperado"]])
