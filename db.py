import mysql.connector



def conectar():
    return mysql.connector.connect(
        host='162.241.203.62',
        user= 'avinfo61_servico',
        password='Sclara02',
        database='avinfo61_atendimento'
    )

def criar_usuario(nome, email, senha_hash, papel='usuario'):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES (%s, %s, %s, %s)",
                   (nome, email, senha_hash, papel))
    conn.commit()
    cursor.close()

def buscar_usuario_por_email(email):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()
    return usuario


def salvar_atendimento(usuario_id, cliente, descricao, status):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO atendimentos (usuario_id, cliente, descricao, status) VALUES (%s, %s, %s, %s)",
                    (usuario_id, cliente, descricao, status))
    conn.commit()
    cursor.close()


def listar_atendimentos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                    SELECT a.id, u.nome AS usuario, a.cliente, a.cliente, a.descricao, a.status, a.data
                    FROM atendimentos a
                    JOIN usuarios AS u ON a.usuario_id = u.id
                    ORDER BY a.data DESC
                """)
    dados = cursor.fetchall()
    cursor.close()
    return dados

def listar_usuarios():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, email, papel FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def atualizar_papel_usuario(user_id, novo_papel):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET papel = %s WHERE id = %s", (novo_papel, user_id))
    conn.commit()
    conn.close()

def listar_atendimentos_por_usuario(usuario_id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, cliente, descricao, status, data
        FROM atendimentos
        WHERE usuario_id = %s
        ORDER BY data DESC
    """, (usuario_id,))
    atendimentos = cursor.fetchall()
    conn.close()
    return atendimentos

def atualizar_status_atendimento(atendimento_id, novo_status):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE atendimentos SET status = %s WHERE id = %s", (novo_status, atendimento_id))
    conn.commit()
    conn.close()

def listar_cliente(parte_nome):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT codigo, razao_social FROM clientes WHERE razao_social LIKE %s ORDER BY razao_social", (f'%{parte_nome}%',))
    clientes = cursor.fetchall()
    cursor.close()
    return clientes

def cadastrar_cliente_completo(cnpj, razao_social, nome_fantasia, endereco, municipio, uf):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes 
        (cnpj, razao_social, nome_fantasia, endereco, municipio, uf) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        cnpj, razao_social, nome_fantasia, endereco, municipio, uf
    ))
    conn.commit()
    conn.close()

def cnpj_existe(cnpj):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clientes WHERE cnpj = %s", (cnpj,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None
