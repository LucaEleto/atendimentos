import hashlib
import db

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def login(email, senha):
    usuario = db.buscar_usuario_por_email(email)
    if usuario and usuario['senha_hash'] == hash_senha(senha):
        return usuario
    return None