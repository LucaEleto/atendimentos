import streamlit as st
import db
import auth
import requests
import pandas as pd

st.set_page_config(page_title='Sistema De Atendimento', layout='wide')

if 'usuario' not in st.session_state:
    st.session_state.usuario = None

def tela_login():
    st.image('logonova.bmp', width=150)
    st.title('Login')
    email = st.text_input('Email')
    senha = st.text_input('Senha', type='password')
    if st.button('Entrar'):
        usuario = auth.login(email, senha)
        if usuario:
            st.session_state.usuario = usuario
            st.success(f'Bem-vindo, {usuario["nome"]}!')
        else:
            st.error('Email ou senha incorretos.')

def tela_registro():
    st.title('Registro de Usuário')
    nome = st.text_input('Nome')
    email = st.text_input('Email')
    senha = st.text_input('Senha', type='password')
    if st.button('Registrar'):
        if db.buscar_usuario_por_email(email):
            st.error('Email já cadastrado.')
        else:
            senha_hash = auth.hash_senha(senha)
            db.criar_usuario(nome, email, senha_hash)
            st.success('Usuário registrado com sucesso!')

def meus_atendimentos():
    st.title("Meus Atendimentos")
    meus = db.listar_atendimentos_por_usuario(st.session_state.usuario['id'])

    if not meus:
        st.info("Você ainda não registrou atendimentos.")
        return

    # 🔽 Filtro por status
    status_opcoes = ["Todos", "Aberto", "Pendente", "Concluído"]
    status_filtro = st.selectbox("Filtrar por status:", status_opcoes)

    if status_filtro != "Todos":
        meus = [a for a in meus if a["status"] == status_filtro]

    if not meus:
        st.warning("Nenhum atendimento encontrado com esse status.")
        return
    
    for atendimento in meus:
        with st.expander(f"{atendimento['cliente']}"):
            # Editar descrição
            nova_descricao = st.text_area(
                "Descrição",
                value=atendimento["descricao"],
                key=f"desc_{atendimento['id']}"
            )
            if nova_descricao != atendimento["descricao"]:
                if st.button("Salvar Descrição", key=f"salvar_desc_{atendimento['id']}"):
                    db.atualizar_descricao_atendimento(atendimento["id"], nova_descricao)
                    st.success("Descrição atualizada.")
                    st.rerun()

            # Editar status
            novo_status = st.selectbox(
                "Status",
                ["Aberto", "Pendente", "Concluído"],
                index=["Aberto", "Pendente", "Concluído"].index(atendimento["status"]),
                key=f"status_{atendimento['id']}"
            )
            if novo_status != atendimento["status"]:
                db.atualizar_status_atendimento(atendimento["id"], novo_status)
                st.success("Status atualizado.")
                st.rerun()

            # Excluir atendimento
            if st.button("Excluir Atendimento", key=f"excluir_{atendimento['id']}"):
                db.excluir_atendimento(atendimento["id"])
                st.success("Atendimento excluído.")
                st.rerun()
                

def tela_atendimentos():
    st.title('Registro de Atendimentos')
    nome_digitado = st.text_input('Nome, CNPJ ou Fantasia do Cliente')
    cliente_selecionado = st.session_state.get('cliente_selecionado', None)

    if 'clientes_filtrados' not in st.session_state:
        st.session_state.clientes_filtrados = []

    # Limpa seleção ANTES de criar o radio, se necessário
    if st.button('🔍 Buscar Cliente'):
        resultado = db.listar_cliente(nome_digitado)
        if resultado:
            df_clientes = pd.DataFrame(resultado)
            df_clientes['exibir'] = df_clientes.apply(
                lambda row: f"{row.get('cnpj', '')} - {row['razao_social']} ({row.get('nome_fantasia', '')})", axis=1
            )
            st.session_state.clientes_filtrados = df_clientes.to_dict('records')
            # Limpa seleção antes de criar o radio
            if 'radio_cliente' in st.session_state:
                del st.session_state.radio_cliente
        else:
            st.session_state.clientes_filtrados = []
            st.warning('Nenhum cliente encontrado com esse filtro.')

    if st.session_state.clientes_filtrados:
        opcoes = [
            f"{c['cnpj']} - {c['razao_social']} ({c['nome_fantasia']})"
            for c in st.session_state.clientes_filtrados
        ]
        selecionado = st.radio(
            "Clientes encontrados:",
            options=opcoes,
            key="radio_cliente"
        )
        if st.button("Selecionar este cliente"):
            idx = opcoes.index(selecionado)
            st.session_state.cliente_selecionado = st.session_state.clientes_filtrados[idx]['razao_social']
            st.success(f'Cliente selecionado: {selecionado}')

    elif cliente_selecionado:
        st.success(f'Cliente selecionado: {cliente_selecionado}')

    descricao = st.text_area('Descrição')
    status = st.selectbox('Status', ['Aberto', 'Pendente', 'Concluído'])
    if st.button('Salvar Atendimento'):
        if not st.session_state.get('cliente_selecionado'):
            st.error('Selecione um cliente antes de salvar.')
        else:
            db.salvar_atendimento(
                st.session_state.usuario['id'],
                st.session_state.cliente_selecionado,
                descricao,
                status
            )
            st.success('Atendimento registrado com sucesso!')
            st.session_state.cliente_selecionado = None
            st.session_state.clientes_filtrados = []
            if 'radio_cliente' in st.session_state:
                del st.session_state.radio_cliente

def paniel_admin():
    st.title('Painel de Administração')
    atendimentos = db.listar_atendimentos()
    st.dataframe(atendimentos)

def buscar_dados_cnpj(cnpj):
    try:
        resposta = requests.get(f"https://www.receitaws.com.br/v1/cnpj/{cnpj}")
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get("status") == "OK":
                return dados
    except Exception as e:
        st.error("Erro ao buscar CNPJ: " + str(e))
    return None
    
def cadastrar_cliente():
    st.title("Cadastro de Cliente")

    cnpj = st.text_input("CNPJ (somente números)", max_chars=14)

    # Inicializa os campos vazios
    dados_api = None
    razao = fantasia = endereco = municipio = uf = ""
    email_cliente = contato_cliente = nome_contabilidade = ""
    email_contabilidade = contato_contabilidade = observacao = ""

    cliente_existente = None

    if len(cnpj) == 14:
        cliente_existente = db.buscar_cliente_por_cnpj(cnpj)
        dados_api = buscar_dados_cnpj(cnpj)

    if cliente_existente:
        st.info("CNPJ já cadastrado. Os dados foram carregados para edição.")
        # Campos do banco
        razao = cliente_existente.get("razao_social", "")
        fantasia = cliente_existente.get("nome_fantasia", "")
        email_cliente = cliente_existente.get("email_cliente", "")
        contato_cliente = cliente_existente.get("contato_cliente", "")
        nome_contabilidade = cliente_existente.get("nome_contabilidade", "")
        email_contabilidade = cliente_existente.get("email_contabilidade", "")
        contato_contabilidade = cliente_existente.get("contato_contabilidade", "")
        observacao = cliente_existente.get("observacao", "")

        # Se a API respondeu, sobrescreve o endereço, município e UF
        if dados_api:
            endereco = f"{dados_api.get('logradouro', '')}, {dados_api.get('numero', '')} - {dados_api.get('bairro', '')}"
            municipio = dados_api.get("municipio", "")
            uf = dados_api.get("uf", "")
        else:
            endereco = cliente_existente.get("endereco", "")
            municipio = cliente_existente.get("municipio", "")
            uf = cliente_existente.get("uf", "")
    else:
        # Novo cliente, busca tudo da API
        if dados_api:
            razao = dados_api.get("nome", "")
            fantasia = dados_api.get("fantasia", "")
            endereco = f"{dados_api.get('logradouro', '')}, {dados_api.get('numero', '')} - {dados_api.get('bairro', '')}"
            municipio = dados_api.get("municipio", "")
            uf = dados_api.get("uf", "")
            st.success("Dados carregados da Receita Federal.")
        else:
            st.warning("CNPJ não encontrado ou excedeu o limite da API.")

    # Formulário editável
    razao = st.text_input("Razão Social", value=razao)
    fantasia = st.text_input("Nome Fantasia", value=fantasia)
    endereco = st.text_input("Endereço", value=endereco)
    municipio = st.text_input("Município", value=municipio)
    uf = st.text_input("UF", value=uf)
    email_cliente = st.text_input("Email do Cliente", value=email_cliente)
    contato_cliente = st.text_input("Contato do Cliente", value=contato_cliente)
    nome_contabilidade = st.text_input("Nome da Contabilidade", value=nome_contabilidade)
    email_contabilidade = st.text_input("Email da Contabilidade", value=email_contabilidade)
    contato_contabilidade = st.text_input("Contato da Contabilidade", value=contato_contabilidade)
    observacao = st.text_area("Observações", value=observacao)

    if st.button("Salvar Cliente"):
        if not cnpj or not razao:
            st.error("CNPJ e Razão Social são obrigatórios.")
        elif cliente_existente:
            db.atualizar_cliente_por_cnpj(cnpj, razao, fantasia, endereco, municipio, uf,
                                          email_cliente, contato_cliente, nome_contabilidade,
                                          email_contabilidade, contato_contabilidade, observacao)
            st.success("Cliente atualizado com sucesso!")
            st.rerun()
        else:
            db.cadastrar_cliente_completo(cnpj, razao, fantasia, endereco, municipio, uf,
                                          email_cliente, contato_cliente, nome_contabilidade,
                                          email_contabilidade, contato_contabilidade, observacao)
            st.success("Cliente cadastrado com sucesso!")
            st.rerun()

def consulta_licenca():

    st.title('Consulta Licenças') 

    # Entrada do usuário
    consulta_sql_input = st.text_input('Pesquisar Cliente')

    # Consulta SQL
    consulta_sql = """
    SELECT razao_social, nome_fantasia, dias 
    FROM clientes 
    WHERE razao_social LIKE %s OR nome_fantasia LIKE %s
    """

    # Ação ao clicar no botão
    if st.button('Pesquisar'):
        conn = db.conectar()
        cursor_consulta = conn.cursor()
        # Passando o mesmo valor duas vezes para os dois campos do LIKE
        cursor_consulta.execute(consulta_sql, (f'%{consulta_sql_input}%', f'%{consulta_sql_input}%'))
        cliente_consulta = cursor_consulta.fetchall()
        cursor_consulta.close()

        # Exibindo os resultados
        if cliente_consulta:
            tb = pd.DataFrame(cliente_consulta, columns=['Razao Social', 'Nome Fantasia', 'Dias'])
            st.subheader('Consulta Cliente')
            st.dataframe(tb)
        else:
            st.warning("Nenhum cliente encontrado.")

def atualiza_licenca():
    st.title('Atualizar Dias de Licença')

    # Inicializar session_state para armazenar DataFrame
    if 'df_original' not in st.session_state:
        st.session_state.df_original = None

    # Entrada de busca
    busca = st.text_input('Pesquisar Cliente (Razao Social ou Nome Fantasia)')

    # Botão de busca
    if st.button('Buscar'):
        conn = db.conectar()
        cursor = conn.cursor()
        consulta = """
            SELECT razao_social, nome_fantasia, dias, vencimento 
            FROM clientes 
            WHERE razao_social LIKE %s OR nome_fantasia LIKE %s
        """
        cursor.execute(consulta, (f"%{busca}%", f"%{busca}%"))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        if resultados:
            df = pd.DataFrame(resultados, columns=['Razao Social', 'Nome Fantasia', 'Dias', 'Vencimento'])
            st.session_state.df_original = df  # salva na sessão
        else:
            st.warning("Nenhum cliente encontrado.")
            st.session_state.df_original = None  # limpa

    # Mostrar editor se houver dados
    if st.session_state.df_original is not None:
        st.subheader('Editar Dias')
        df_editado = st.data_editor(
            st.session_state.df_original,
            num_rows="dynamic",
            use_container_width=True,
            key='editor'
        )

        # Botão para salvar
        if st.button('Salvar Alterações'):
            conn = db.conectar()
            cursor = conn.cursor()
            linhas_afetadas = 0

            for index, row in df_editado.iterrows():
                razao_social = row['Razao Social']
                dias_novo = row['Dias']
                try:
                    cursor.execute(
                        "UPDATE clientes SET dias = %s WHERE razao_social = %s",
                        (dias_novo, razao_social)
                    )
                    if cursor.rowcount > 0:
                        linhas_afetadas += 1
                except Exception as e:
                    st.error(f"Erro ao atualizar cliente {razao_social}: {e}")

            conn.commit()
            cursor.close()
            conn.close()

            if linhas_afetadas > 0:
                st.success(f"{linhas_afetadas} registro(s) atualizado(s) com sucesso!")
            else:
                st.info("Nenhuma alteração detectada ou salva.")
    


def gerenciar_usuarios():
    st.title("Gerenciar Usuários")
    usuarios = db.listar_usuarios()

    for usuario in usuarios:
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            st.text(usuario['nome'])
        with col2:
            st.text(usuario['email'])
        with col3:
            novo_papel = st.selectbox(
                "Permissão",
                options=["usuario", "admin"],
                index=0 if usuario['papel'] == 'usuario' else 1,
                key=f"papel_{usuario['id']}"
            )
            if novo_papel != usuario['papel']:
                db.atualizar_papel_usuario(usuario['id'], novo_papel)
                st.success(f"Permissão de {usuario['nome']} atualizada para {novo_papel}.")
                st.rerun()

def tela_principal():

    st.sidebar.image('logonova.bmp', width=150)
    st.sidebar.write(f'👤 Usuário: {st.session_state.usuario["nome"]}')

    menu = ['Registrar Atendimento', 'Meus Atendimentos', 'Cadastrar Cliente', 'Consulta Licença']
    if st.session_state.usuario['papel'] == 'admin':
        menu.extend(['Painel de Administração', 'Atualizar Licença', 'Gerenciar Usuários'])
    menu.append('Sair')

    escolha = st.sidebar.selectbox('Menu', menu)

    if escolha == 'Registrar Atendimento':
        tela_atendimentos()
    elif escolha == "Meus Atendimentos":
        meus_atendimentos()
    elif escolha == 'Painel de Administração':
        paniel_admin()
    elif escolha == "Cadastrar Cliente":
        cadastrar_cliente()
    elif escolha == "Consulta Licença":
        consulta_licenca()
    elif escolha == "Atualizar Licença":
        atualiza_licenca()
    elif escolha == 'Gerenciar Usuários':
        gerenciar_usuarios()
    elif escolha == 'Sair':
        st.session_state.usuario = None
        st.rerun()

# Tela Inicial
if st.session_state.usuario:
    tela_principal()
else:
    aba = st.sidebar.selectbox('Acesso', ['Login', 'Registro'])

    if aba == 'Login':
        tela_login()
    else:
        tela_registro()

