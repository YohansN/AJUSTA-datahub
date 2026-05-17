import streamlit as st
import utils.auth as auth

st.set_page_config(
    page_title="Sobre - AJUSTA",
    page_icon="📖",
    layout="wide",
)

auth.check_auth()

st.title("📖 Sobre o AJUSTA Data Hub")
st.markdown(
    "Este guia explica como usar o sistema passo a passo. "
    "Clique em cada seção para expandir e ler as instruções."
)

st.divider()

# ── Fluxo recomendado ────────────────────────────────────────────────────────

st.header("Fluxo recomendado de uso")
st.markdown(
    """
Siga esta ordem ao configurar o sistema pela primeira vez ou ao incorporar uma nova turma de beneficiários:

| Passo | O que fazer | Onde |
|-------|-------------|------|
| **1** | Cadastre os projetos/ações em andamento | Projetos |
| **2** | Registre os beneficiários vinculando-os aos projetos | Novo Cadastro |
| **3** | Adicione outros administradores que precisam de acesso | Administração |
| **4** | Acompanhe os indicadores e o ranking de vulnerabilidade | Dashboard · Vulnerabilidades |
"""
)

st.divider()

# ── Projetos ────────────────────────────────────────────────────────────────

st.header("📁 Projetos")

with st.expander("Como cadastrar um projeto"):
    st.markdown(
        """
1. Acesse **Projetos** no menu lateral.
2. Clique em **Adicionar Projeto**.
3. Preencha os campos:
   - **Nome do projeto** *(obrigatório)*
   - **O projeto está ativo?** *(obrigatório)* — escolha **Sim** para que o projeto apareça na lista do formulário de cadastro de beneficiários.
   - **Descrição** *(opcional)* — resumo do objetivo do projeto.
   - **Principal Responsável** *(opcional)* — nome do coordenador.
4. Clique em **Salvar**.

> O sistema registra automaticamente quem cadastrou o projeto e a data.
"""
    )

with st.expander("Como ativar ou desativar um projeto"):
    st.markdown(
        """
1. Clique em **Alterar Status do Projeto**.
2. Informe o **ID** do projeto (visível na tabela principal).
3. Confirme a alteração.

Projetos **inativados** deixam de aparecer como opção no cadastro de novos beneficiários, mas os vínculos já existentes são preservados.
"""
    )

with st.expander("Como excluir um projeto"):
    st.warning("Esta ação é **irreversível**. Os beneficiários vinculados **não** são excluídos, mas o vínculo deixa de aparecer nos relatórios.", icon="⚠️")
    st.markdown(
        """
1. Clique em **Excluir Projeto**.
2. Informe o **ID** do projeto.
3. Verifique os dados exibidos e confirme a exclusão.
"""
    )

with st.expander("Como ver os beneficiários de um projeto"):
    st.markdown(
        """
Na parte inferior da página **Projetos**, cada projeto possui um expansor com:
- Status atual (ativo/inativo).
- Número de beneficiários vinculados.
- Lista de nomes dos beneficiários associados.
"""
    )

st.divider()

# ── Cadastro de Beneficiários ────────────────────────────────────────────────

st.header("👤 Cadastro de Beneficiários")

with st.expander("Visão geral do formulário"):
    st.markdown(
        """
O formulário está dividido em **6 seções**. Campos marcados com * são obrigatórios.

| Seção | Campos principais |
|-------|-------------------|
| **Dados Pessoais** | Nome*, CPF*, Data de Nascimento*, Sexo*, Escolaridade, Cor/Raça, Telefone, Ocupação |
| **Dados Residenciais** | Endereço*, Bairro*, Tipo de Residência, Acesso a Água/Esgoto/Energia |
| **Dados Familiares** | Estado Civil, Nº de Filhos, Nº de Membros*, Renda Bruta Total |
| **Histórico de Hanseníase** | Diagnóstico, Classificação, Forma Clínica, Lesões, Nervos Afetados |
| **Projeto/Ação** | Seleção múltipla dos projetos ativos |
| **Responsáveis** | Responsável pelo Preenchimento (automático), Responsável pela Entrevista |
"""
    )

with st.expander("Renda per capita — cálculo automático"):
    st.markdown(
        """
O campo **Renda per Capita** é calculado automaticamente:

> Renda Bruta Total ÷ Número de Membros da Família

Você não precisa preenchê-lo manualmente. Basta garantir que a renda bruta e o número de membros estejam corretos.
"""
    )

with st.expander("Dicas de preenchimento"):
    st.info(
        "Prefira registrar **Não informado** a deixar campos em branco quando o dado não estiver disponível. "
        "Isso melhora a qualidade dos indicadores no Dashboard e no modelo de Vulnerabilidades.",
        icon="💡",
    )
    st.markdown(
        """
- **CPF**: insira apenas os dígitos ou no formato `000.000.000-00`.
- **Projeto/Ação**: selecione todos os projetos aos quais o beneficiário está vinculado — um beneficiário pode participar de mais de um.
- **Hanseníase**: se o beneficiário nunca teve hanseníase, selecione **Não** no primeiro campo; os demais campos desta seção serão desconsiderados pelo modelo.
"""
    )

st.divider()

# ── Administração ────────────────────────────────────────────────────────────

st.header("⚙️ Administradores")

with st.expander("Como adicionar um novo administrador"):
    st.markdown(
        """
1. Acesse **Administração** no menu lateral.
2. Clique em **Adicionar Novo Usuário Administrador**.
3. Preencha:
   - **Nome** *(obrigatório)*
   - **E-mail** *(obrigatório)* — deve ser a conta Google que a pessoa usará para fazer login.
   - **Telefone** *(obrigatório)*
4. Clique em **Salvar**.

A partir desse momento, o e-mail cadastrado será aceito pelo sistema ao efetuar login com o Google.
"""
    )
    st.info(
        "O e-mail precisa ser exatamente igual ao da conta Google. "
        "Erros de digitação impedirão o acesso.",
        icon="ℹ️",
    )

with st.expander("Como remover um administrador"):
    st.warning("Esta ação é **irreversível**. O usuário perderá acesso imediatamente.", icon="⚠️")
    st.markdown(
        """
1. Clique em **Remover Usuário Administrador**.
2. Informe o **e-mail** do usuário.
3. Confirme a remoção após verificar os dados exibidos.
"""
    )

st.divider()

# ── Dashboard ────────────────────────────────────────────────────────────────

st.header("📊 Dashboard")

with st.expander("Abas disponíveis"):
    st.markdown(
        """
| Aba | O que mostra |
|-----|-------------|
| **Visão Geral** | Totais e médias: beneficiários, renda per capita, membros familiares, projetos |
| **Demografia e Localização** | Distribuição por sexo, gênero, faixa etária e bairro |
| **Moradia e Serviços** | Tipo de residência; acesso a água, esgoto e energia elétrica |
| **Projetos e Saúde** | Participação por projeto; situação clínica de hanseníase |
| **Renda e Perfil** | Histograma de renda per capita; distribuição por cor/raça |
"""
    )

with st.expander("Como usar os filtros"):
    st.markdown(
        """
Os filtros ficam na **barra lateral (sidebar)** e funcionam em conjunto (lógica **E**):

- **Projeto** — exibe apenas beneficiários vinculados ao(s) projeto(s) selecionado(s).
- **Bairro**, **Sexo**, **Tipo de Residência**, **Categoria de Hanseníase** — restringem ainda mais o conjunto exibido.

Clique em **Limpar filtros** para voltar à visão completa da base.
"""
    )
    st.info(
        "O contador de **Projetos distintos** na Visão Geral sempre reflete a base completa, "
        "independentemente dos filtros aplicados.",
        icon="ℹ️",
    )

st.divider()

# ── Vulnerabilidades ────────────────────────────────────────────────────────

st.header("⚕️ Vulnerabilidades")

with st.expander("O que é o modelo de risco clínico"):
    st.markdown(
        """
A página **Vulnerabilidades** usa um modelo de machine learning treinado com dados públicos do **SINAN** (Sistema de Informação de Agravos de Notificação) para estimar a probabilidade de incapacidade física entre beneficiários com histórico de hanseníase.

| Score | Categoria |
|-------|-----------|
| < 0,30 | 🟢 **Baixo** |
| 0,30 – 0,69 | 🟡 **Médio** |
| ≥ 0,70 | 🔴 **Alto** |
"""
    )
    st.warning(
        "Este modelo **não é uma ferramenta diagnóstica**. "
        "Ele serve para apoiar a priorização institucional e análises populacionais, "
        "não para substituir avaliação clínica.",
        icon="⚠️",
    )

with st.expander("Critério de elegibilidade para o modelo"):
    st.markdown(
        """
O modelo só consegue calcular o score quando **todos** os campos abaixo estão preenchidos com valores válidos (sem *Não sabe* ou *Não informado*):

- Sexo (Masculino ou Feminino)
- Cor/Raça
- Escolaridade
- Número de lesões
- Nervos afetados
- Classificação operacional (PB ou MB)
- Forma clínica

Beneficiários sem esses dados aparecem nas métricas gerais, mas **não entram no ranking**.
"""
    )
    st.info(
        "Para aumentar a cobertura do modelo, incentive o preenchimento completo do histórico de hanseníase no cadastro.",
        icon="💡",
    )

with st.expander("Como usar os filtros e ler os gráficos"):
    st.markdown(
        """
**Filtros do sidebar:**
- **Categoria de risco** — mostra apenas Baixo, Médio ou Alto.
- **Bairro** e **Faixa de renda** — recortes socioeconômicos.
- **Filtros clínicos** — refletem diretamente os campos usados pelo modelo (lesões, nervos, classificação, etc.).

**Gráficos (mostram sempre todos os elegíveis, ignoram filtros):**
- **Score médio por faixa de renda** — identifica se beneficiários de menor renda concentram maior risco.
- **Score médio por escolaridade** — correlação entre nível educacional e risco clínico.
- **Distribuição de scores** — histograma que mostra se a base está concentrada em risco baixo, médio ou alto.
"""
    )

st.divider()

# ── Contato ─────────────────────────────────────────────────────────────────

st.header("Dúvidas e suporte")
st.markdown(
    "Em caso de dúvidas, problemas de acesso ou solicitações de ajuste no sistema, "
    "entre em contato com **yohans.dev@gmail.com**."
)
