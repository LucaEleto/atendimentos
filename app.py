import streamlit as st
import db
import auth
import requests
import pandas as pd
import datetime

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
            try:
                data_obj = datetime.datetime.strptime(str(atendimento["data"]), "%Y-%m-%d %H:%M:%S")
                data_formatada = data_obj.strftime("%d/%m/%Y %H:%M")
            except Exception:
                data_formatada = atendimento["data"]  # fallback se não conseguir converter
            if atendimento.get("data_fin"):
                try:
                    data_fin_obj = datetime.datetime.strptime(str(atendimento["data_fin"]), "%Y-%m-%d %H:%M:%S")
                    data_fin_formatada = data_fin_obj.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    data_fin_formatada = atendimento["data_fin"]
                st.markdown(f'**Finalizado em:** {data_fin_formatada}')
            st.markdown(f'**Data do atendimento:** {data_formatada}')
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

    if st.button('🔍 Buscar Cliente'):
        resultado = db.listar_cliente(nome_digitado)
        if resultado:
            df_clientes = pd.DataFrame(resultado)
            df_clientes['exibir'] = df_clientes.apply(
                lambda row: f"{row.get('cnpj', '')} - {row['razao_social']} ({row.get('nome_fantasia', '')})", axis=1
            )
            st.session_state.clientes_filtrados = df_clientes.to_dict('records')
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
            cliente = st.session_state.clientes_filtrados[idx]
            st.session_state.cliente_selecionado = cliente['razao_social']
            st.session_state.observacao_cliente = cliente.get('observacao', '')
            st.success(f'Cliente selecionado: {selecionado}')

    elif cliente_selecionado:
        st.success(f'Cliente selecionado: {cliente_selecionado}')

    # Exibe a observação do cliente selecionado, se houver
    observacao_cliente = st.session_state.get('observacao_cliente', '')
    if observacao_cliente:
        st.info(f"Observação do cliente: {observacao_cliente}")

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
            # NÃO limpe observacao_cliente aqui!
            if 'radio_cliente' in st.session_state:
                del st.session_state.radio_cliente

def paniel_admin():
    st.title('Painel de Administração')
    atendimentos = db.listar_atendimentos()
    st.dataframe(atendimentos)

def buscar_dados_cnpj(cnpj):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(f"https://www.receitaws.com.br/v1/cnpj/{cnpj}", headers=headers)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get("status") == "OK":
                return dados
    except Exception as e:
        st.error("Erro ao buscar CNPJ: " + str(e))
    return None
st.session_state.empresa_selecionada = None
    
def cadastrar_empresa():
    st.title("Cadastro de Empresa")

    # Busca empresa por nome
    busca = st.text_input("Buscar empresa por Razão Social ou Nome Fantasia")
    if busca:
        resultado = db.listar_cliente(busca)
        if resultado:
            if len(resultado) > 1:
                opcoes = [
                    f"{c['razao_social']} ({c['nome_fantasia']})"
                    for c in resultado
                ]
                selecionado = st.selectbox("Selecione a empresa encontrada:", opcoes)
                if st.button("Selecionar empresa"):
                    idx = opcoes.index(selecionado)
                    empresa = resultado[idx]
                    carregar_dados_empresa(empresa)
                    st.rerun()  # <--- Rerenderiza a tela com os dados preenchidos
            else:
                if st.button("Selecionar empresa"):
                    empresa = resultado[0]
                    carregar_dados_empresa(empresa)
                    st.rerun()

    # Define os campos com valor padrão do session_state
    cnpj = st.text_input("CNPJ", max_chars=14, key="cnpj_empresa")
    
    if st.button("Buscar na Receita Federal"):
        if len(cnpj) == 14 and cnpj.isdigit():
            dados_api = buscar_dados_cnpj(cnpj)
            if dados_api:
                # Atualiza somente o session_state de campos que ainda não foram instanciados
                st.session_state["razao_empresa"] = dados_api.get("nome", "")
                st.session_state["fantasia_empresa"] = dados_api.get("fantasia", "")
                st.session_state["endereco_empresa"] = f"{dados_api.get('logradouro', '')}, {dados_api.get('numero', '')} - {dados_api.get('bairro', '')}"
                st.session_state["municipio_empresa"] = dados_api.get("municipio", "")
                st.session_state["uf_empresa"] = dados_api.get("uf", "")
                st.success("Dados carregados da Receita Federal.")
                st.rerun()  # Rerenderiza para atualizar os campos com os dados
            else:
                st.warning("CNPJ não encontrado ou limite da API atingido.")
        else:
            st.warning("Digite um CNPJ válido.")

    # Campos do formulário com chave única
    st.text_input("Razão Social", value=st.session_state.empresa_form['razao'], key="razao_empresa")
    st.text_input("Nome Fantasia", value=st.session_state.empresa_form['fantasia'], key="fantasia_empresa")
    st.text_input("Endereço", value=st.session_state.empresa_form['endereco'], key="endereco_empresa")
    st.text_input("Município", value=st.session_state.empresa_form['municipio'], key="municipio_empresa")
    st.text_input("UF", value=st.session_state.empresa_form['uf'], key="uf_empresa")
    st.text_input("Email do Cliente", key="email_cliente")
    st.text_input("Contato do Cliente", key="contato_cliente")
    st.text_input("Nome da Contabilidade", key="nome_contabilidade")
    st.text_input("Email da Contabilidade", key="email_contabilidade")
    st.text_input("Contato da Contabilidade", key="contato_contabilidade")
    st.text_area("Observação", key="observacao")

    if st.button("Salvar Empresa"):
        if not st.session_state.cnpj_empresa or not st.session_state.razao_empresa:
            st.error("CNPJ e Razão Social são obrigatórios.")
            return

        empresa_existente = db.buscar_cliente_por_cnpj(st.session_state.cnpj_empresa)
        if empresa_existente:
            db.atualizar_cliente_por_cnpj(
                st.session_state.cnpj_empresa,
                st.session_state.razao_empresa,
                st.session_state.fantasia_empresa,
                st.session_state.endereco_empresa,
                st.session_state.municipio_empresa,
                st.session_state.uf_empresa,
                st.session_state.email_cliente,
                st.session_state.contato_cliente,
                st.session_state.nome_contabilidade,
                st.session_state.email_contabilidade,
                st.session_state.contato_contabilidade,
                st.session_state.observacao
            )
            st.success("Empresa atualizada com sucesso!")
        else:
            db.cadastrar_cliente_completo(
                st.session_state.cnpj_empresa,
                st.session_state.razao_empresa,
                st.session_state.fantasia_empresa,
                st.session_state.endereco_empresa,
                st.session_state.municipio_empresa,
                st.session_state.uf_empresa,
                st.session_state.email_cliente,
                st.session_state.contato_cliente,
                st.session_state.nome_contabilidade,
                st.session_state.email_contabilidade,
                st.session_state.contato_contabilidade,
                st.session_state.observacao
            )
            st.success("Empresa cadastrada com sucesso!")


        st.rerun()

def carregar_dados_empresa(empresa):
    st.session_state["cnpj_empresa"] = empresa.get("cnpj", "")
    st.session_state["razao_empresa"] = empresa.get("razao_social", "")
    st.session_state["fantasia_empresa"] = empresa.get("nome_fantasia", "")
    st.session_state["endereco_empresa"] = empresa.get("endereco", "")
    st.session_state["municipio_empresa"] = empresa.get("municipio", "")
    st.session_state["uf_empresa"] = empresa.get("uf", "")
    st.session_state["email_cliente"] = empresa.get("email_cliente", "")
    st.session_state["contato_cliente"] = empresa.get("contato_cliente", "")
    st.session_state["nome_contabilidade"] = empresa.get("nome_contabilidade", "")
    st.session_state["email_contabilidade"] = empresa.get("email_contabilidade", "")
    st.session_state["contato_contabilidade"] = empresa.get("contato_contabilidade", "")
    st.session_state["observacao"] = empresa.get("observacao", "")

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
        cadastrar_empresa()
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
