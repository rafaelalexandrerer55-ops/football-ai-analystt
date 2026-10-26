
import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Football AI Analyst",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Football AI Analyst")
st.caption("Análise estatística de futebol e avaliação de odds")

st.info(
    "Versão inicial: as análises dependem dos dados carregados. "
    "As estimativas não garantem resultados nem lucro."
)

st.header("📂 1. Carregar dados históricos")

ficheiro = st.file_uploader(
    "Carrega o CSV dos jogos (por exemplo, p1.csv)",
    type=["csv"]
)

if ficheiro is not None:
    try:
        df = pd.read_csv(ficheiro, encoding="latin1")
        df.columns = df.columns.str.strip()

        colunas = ["HomeTeam", "AwayTeam", "FTHG", "FTAG"]
        faltam = [c for c in colunas if c not in df.columns]

        if faltam:
            st.error(f"Faltam colunas necessárias: {faltam}")
            st.stop()

        df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce")
        df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce")
        jogos = df.dropna(subset=colunas).copy()

        st.success(f"{len(jogos)} jogos carregados.")

        st.header("📊 2. Estatísticas")
        media_casa = jogos["FTHG"].mean()
        media_fora = jogos["FTAG"].mean()

        c1, c2, c3 = st.columns(3)
        c1.metric("Jogos analisados", len(jogos))
        c2.metric("Média de golos em casa", f"{media_casa:.2f}")
        c3.metric("Média de golos fora", f"{media_fora:.2f}")

        ataque_casa = jogos.groupby("HomeTeam")["FTHG"].mean()
        sofridos_casa = jogos.groupby("HomeTeam")["FTAG"].mean()
        ataque_fora = jogos.groupby("AwayTeam")["FTAG"].mean()
        sofridos_fora = jogos.groupby("AwayTeam")["FTHG"].mean()

        equipas = sorted(
            set(jogos["HomeTeam"]) | set(jogos["AwayTeam"])
        )

        st.subheader("Estatísticas por equipa")
        estatisticas = pd.DataFrame({
            "Golos marcados em casa": ataque_casa,
            "Golos sofridos em casa": sofridos_casa,
            "Golos marcados fora": ataque_fora,
            "Golos sofridos fora": sofridos_fora
        }).round(2)

        st.dataframe(estatisticas, use_container_width=True)

        st.header("🔮 3. Analisar um jogo")

        casa = st.selectbox("Equipa da casa", equipas)
        visitantes = [e for e in equipas if e != casa]
        fora = st.selectbox("Equipa visitante", visitantes)

        st.subheader("🎯 4. Comparar com as odds")

        o1, o2, o3 = st.columns(3)
        with o1:
            odd_casa = st.number_input(
                "Odd vitória da casa", min_value=1.01,
                value=2.00, step=0.05
            )
        with o2:
            odd_empate = st.number_input(
                "Odd empate", min_value=1.01,
                value=3.20, step=0.05
            )
        with o3:
            odd_fora = st.number_input(
                "Odd vitória visitante", min_value=1.01,
                value=3.50, step=0.05
            )

        if st.button("Analisar jogo", type="primary"):
            if media_casa <= 0 or media_fora <= 0:
                st.error("Não existem médias de golos válidas.")
            else:
                lambda_c = (
                    ataque_casa.get(casa, media_casa)
                    * sofridos_fora.get(fora, media_casa)
                    / media_casa
                )
                lambda_f = (
                    ataque_fora.get(fora, media_fora)
                    * sofridos_casa.get(casa, media_fora)
                    / media_fora
                )

                def poisson(media, k):
                    return math.exp(-media) * media**k / math.factorial(k)

                max_golos = 12
                pc = [poisson(lambda_c, k) for k in range(max_golos + 1)]
                pf = [poisson(lambda_f, k) for k in range(max_golos + 1)]

                p_c = p_e = p_f = 0.0

                for i in range(max_golos + 1):
                    for j in range(max_golos + 1):
                        p = pc[i] * pf[j]
                        if i > j:
                            p_c += p
                        elif i == j:
                            p_e += p
                        else:
                            p_f += p

                total = p_c + p_e + p_f
                probs = [p_c / total, p_e / total, p_f / total]
                odds = [odd_casa, odd_empate, odd_fora]
                nomes = [
                    "Vitória da casa", "Empate", "Vitória visitante"
                ]

                st.subheader(f"{casa} vs {fora}")
                m1, m2 = st.columns(2)
                m1.metric("Golos esperados da casa", f"{lambda_c:.2f}")
                m2.metric("Golos esperados fora", f"{lambda_f:.2f}")

                resultados = []
                for nome, prob, odd in zip(nomes, probs, odds):
                    resultados.append({
                        "Resultado": nome,
                        "Probabilidade estimada": f"{prob:.1%}",
                        "Odd justa": round(1 / prob, 2),
                        "Odd introduzida": odd,
                        "Valor esperado estimado": f"{(prob * odd - 1):+.1%}"
                    })

                st.dataframe(
                    pd.DataFrame(resultados),
                    use_container_width=True,
                    hide_index=True
                )

                st.warning(
                    "Modelo experimental baseado em médias históricas. "
                    "Não está validado e não deve ser usado isoladamente "
                    "para decidir apostas."
                )

    except Exception as erro:
        st.error(f"Não foi possível analisar o ficheiro: {erro}")
else:
    st.write(
        "Carrega o CSV da Primeira Liga para veres as estatísticas "
        "e experimentares a análise de jogos."
    )
