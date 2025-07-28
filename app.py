import streamlit as st
import db
import auth
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
            st.write("📋", atendimento["descricao"])
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

def tela_atendimentos():
    st.title('Registro de Atendimentos')
    nome_digitado = st.text_input('Nome do Cliente')

    cliente_selecionado = None
    if nome_digitado.strip():
        resultado = db.listar_cliente(nome_digitado)
        nomes = [cliente['cliente'] for cliente in resultado]

        if len(nomes) == 1:
            cliente_selecionado = nomes[0]
            st.success(f'Cliente selecionado: {cliente_selecionado}')
        elif len(nomes) > 1:
            cliente_selecionado = st.selectbox('Selecione o Cliente', nomes)
        else:
            st.warning('Nenhum cliente encontrado com esse nome.')   
    descricao = st.text_area('Descrição')
    status = st.selectbox('Status', ['Pendente', 'Em Progresso', 'Concluído'])
    if st.button('Salvar Atendimento'):
        db.salvar_atendimento(st.session_state.usuario['id'], cliente_selecionado, descricao, status)
        st.success('Atendimento registrado com sucesso!')

def paniel_admin():
    st.title('Painel de Administração')
    atendimentos = db.listar_atendimentos()
    st.dataframe(atendimentos)

def cadastrar_cliente():
    st.title("Cadastrar Novo Cliente")

    cliente = st.text_input("Razão Social")
    fantasia = st.text_input("Nome Fantasia")
    cnpj = st.text_input("CNPJ")

    if st.button("Salvar"):
        if nome.strip() == "":
            st.warning("Digite um nome válido.")
        else:
            db.cadastrar_cliente(nome.strip())
            st.success("Cliente cadastrado com sucesso!")

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

    menu = ['Registrar Atendimento', 'Meus Atendimentos']
    if st.session_state.usuario['papel'] == 'admin':
        menu.extend(['Painel de Administração', 'Gerenciar Usuários'])
    menu.append('Sair')

    escolha = st.sidebar.selectbox('Menu', menu)

    if escolha == 'Registrar Atendimento':
        tela_atendimentos()
    elif escolha == "Meus Atendimentos":
        meus_atendimentos()
    elif escolha == 'Painel de Administração':
        paniel_admin()
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

