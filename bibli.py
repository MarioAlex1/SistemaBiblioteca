
# Sistema de Biblioteca
# Criado para gerenciar empréstimos de livros em uma biblioteca

from flask import Flask, request, redirect, render_template_string, flash, url_for, session
import sqlite3
from datetime import datetime, timedelta

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_biblioteca'

# Função para conectar no banco de dados
def conectar_banco():
    banco = sqlite3.connect("biblioteca.db")
    banco.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return banco

# Função para criar as tabelas do banco
def criar_tabelas_banco():
    banco = conectar_banco()
    cursor = banco.cursor()

    # Criar tabela de livros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            isbn TEXT UNIQUE,
            ano INTEGER,
            quantidade INTEGER DEFAULT 1
        )
    ''')

    # Criar tabela de usuários/alunos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            curso TEXT
        )
    ''')

    # Criar tabela de empréstimos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            livro_id INTEGER NOT NULL,
            data_emprestimo DATE NOT NULL,
            data_prevista DATE NOT NULL,
            data_devolucao DATE,
            status TEXT DEFAULT 'emprestado',
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (livro_id) REFERENCES livros(id)
        )
    ''')

    # Criar tabela de administradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    banco.commit()
    banco.close()

# Função para criar um admin padrão
def criar_primeiro_admin():
    banco = conectar_banco()
    cursor = banco.cursor()

    # Verificar se já existe algum admin
    cursor.execute("SELECT COUNT(*) as total FROM administradores")
    resultado = cursor.fetchone()
    
    if resultado['total'] == 0:
        # Inserir admin padrão se não existir nenhum
        cursor.execute("""
            INSERT INTO administradores (nome, usuario, senha)
            VALUES ('Administrador Padrão', 'admin', 'admin123')
        """)
        banco.commit()

    banco.close()

# Função para verificar se usuário logado é admin
def usuario_eh_admin():
    if 'tipo_usuario' in session:
        return session['tipo_usuario'] == 'admin'
    return False

# Função para verificar se usuário logado é aluno
def usuario_eh_aluno():
    if 'tipo_usuario' in session:
        return session['tipo_usuario'] == 'aluno'
    return False

# Função decoradora para exigir login
def precisa_login(funcao):
    def funcao_protegida(*args, **kwargs):
        if 'tipo_usuario' not in session:
            return redirect(url_for('pagina_login'))
        return funcao(*args, **kwargs)
    funcao_protegida.__name__ = funcao.__name__
    return funcao_protegida

# Função decoradora para exigir acesso de admin
def precisa_ser_admin(funcao):
    def funcao_protegida(*args, **kwargs):
        if not usuario_eh_admin():
            flash("Você precisa ser administrador para acessar esta página!")
            return redirect(url_for('pagina_inicial'))
        return funcao(*args, **kwargs)
    funcao_protegida.__name__ = funcao.__name__
    return funcao_protegida

# HTML da página (template básico)
TEMPLATE_HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titulo }}</title>
    <style>
        /* Estilo básico da página */
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(45deg, #2196F3, #1976D2);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .cabecalho {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            position: relative;
        }
        
        .cabecalho h1 {
            color: #333;
            margin: 0;
            font-size: 2em;
        }
        
        .info-usuario {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #2196F3;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .menu {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .menu a {
            background: #2196F3;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
            display: inline-block;
            font-weight: bold;
        }
        
        .menu a:hover {
            background: #1976D2;
        }
        
        .conteudo {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .grupo-formulario {
            margin-bottom: 15px;
        }
        
        .grupo-formulario label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .grupo-formulario input, .grupo-formulario select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        
        .botao {
            background: #2196F3;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        
        .botao:hover {
            background: #1976D2;
        }
        
        .tabela {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .tabela th, .tabela td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .tabela th {
            background: #2196F3;
            color: white;
        }
        
        .tabela tr:hover {
            background: #f5f5f5;
        }
        
        .alerta {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .cartoes-estatistica {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .cartao {
            background: linear-gradient(45deg, #2196F3, #1976D2);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .numero-grande {
            font-size: 2em;
            font-weight: bold;
        }
        
        .formulario-login {
            max-width: 400px;
            margin: 50px auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .selecionar-tipo-usuario {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .opcao-tipo-usuario {
            background: #f8f9fa;
            border: 2px solid #ddd;
            padding: 20px;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
            flex: 1;
        }
        
        .opcao-tipo-usuario.selecionado {
            border-color: #21196F3;
            background: #e3f2fd;
        }
        
        .opcao-tipo-usuario:hover {
            border-color: #2196F3;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if session.get('tipo_usuario') %}
        <div class="cabecalho">
            <div class="info-usuario">
                {% if session.get('tipo_usuario') == 'admin' %}
                    👨‍💼 Admin: {{ session.get('nome_usuario') }}
                {% else %}
                    👨‍🎓 Aluno: {{ session.get('matricula_usuario') }}
                {% endif %}
                | <a href="/sair" style="color: white;">Sair</a>
            </div>
            <h1>📚 Sistema da Biblioteca</h1>
            <p>Gerenciar livros e empréstimos</p>
        </div>

        <div class="menu">
            <a href="/">🏠 Início</a>
            <a href="/livros">📖 Livros</a>
            {% if session.get('tipo_usuario') == 'admin' %}
            <a href="/usuarios">👥 Usuários</a>
            <a href="/emprestimos">📋 Empréstimos</a>
            {% else %}
            <a href="/meus_emprestimos">📋 Meus Empréstimos</a>
            {% endif %}
            <a href="/relatorios">📊 Relatórios</a>
        </div>
        {% endif %}

        <div class="conteudo">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alerta">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {{ conteudo|safe }}
        </div>
    </div>
</body>
</html>
'''

# Página inicial do sistema
@app.route("/")
def pagina_inicial():
    # Se não estiver logado, redireciona para login
    if 'tipo_usuario' not in session:
        return redirect(url_for('pagina_login'))

    # Conectar no banco e buscar estatísticas
    banco = conectar_banco()
    cursor = banco.cursor()

    # Contar total de livros
    cursor.execute("SELECT COUNT(*) as total FROM livros")
    total_livros = cursor.fetchone()['total']

    # Contar total de usuários
    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    total_usuarios = cursor.fetchone()['total']

    # Contar livros emprestados
    cursor.execute("SELECT COUNT(*) as total FROM emprestimos WHERE status = 'emprestado'")
    total_emprestados = cursor.fetchone()['total']

    # Contar empréstimos atrasados
    cursor.execute("""
        SELECT COUNT(*) as total FROM emprestimos 
        WHERE status = 'emprestado' AND data_prevista < DATE('now')
    """)
    total_atrasados = cursor.fetchone()['total']

    banco.close()

    # Mostrar conteúdo diferente para admin e aluno
    if usuario_eh_admin():
        conteudo_pagina = f'''
        <h2>📊 Painel do Administrador</h2>
        <div class="cartoes-estatistica">
            <div class="cartao">
                <div class="numero-grande">{total_livros}</div>
                <div>Total de Livros</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">{total_usuarios}</div>
                <div>Usuários Cadastrados</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">{total_emprestados}</div>
                <div>Livros Emprestados</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">{total_atrasados}</div>
                <div>Empréstimos Atrasados</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <h3>👨‍💼 Bem-vindo, Administrador!</h3>
            <p>Você pode gerenciar livros, usuários e empréstimos usando o menu acima.</p>
        </div>
        '''
    else:
        # Para alunos, buscar quantidade de empréstimos dele
        banco = conectar_banco()
        cursor = banco.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE u.matricula = ? AND e.status = 'emprestado'
        """, (session.get('matricula_usuario'),))
        meus_emprestimos = cursor.fetchone()['total']
        banco.close()

        conteudo_pagina = f'''
        <h2>📚 Portal do Estudante</h2>
        <div class="cartoes-estatistica">
            <div class="cartao">
                <div class="numero-grande">{total_livros}</div>
                <div>Total de Livros</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">{total_livros - total_emprestados}</div>
                <div>Livros Disponíveis</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">{meus_emprestimos}</div>
                <div>Meus Empréstimos</div>
            </div>
            <div class="cartao">
                <div class="numero-grande">3</div>
                <div>Limite de Empréstimos</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <h3>👨‍🎓 Olá, {session.get('nome_usuario')}!</h3>
            <p>Você pode consultar livros e ver seus empréstimos.</p>
        </div>
        '''

    return render_template_string(TEMPLATE_HTML, titulo="Sistema Biblioteca", conteudo=conteudo_pagina)

# Página de login
@app.route("/login", methods=["GET", "POST"])
def pagina_login():
    if request.method == "POST":
        tipo_usuario = request.form.get('tipo_usuario')

        # Login de administrador
        if tipo_usuario == 'admin':
            usuario = request.form.get('usuario')
            senha = request.form.get('senha')

            banco = conectar_banco()
            cursor = banco.cursor()
            cursor.execute("""
                SELECT * FROM administradores 
                WHERE usuario = ? AND senha = ?
            """, (usuario, senha))
            admin = cursor.fetchone()
            banco.close()

            if admin:
                # Salvar dados na sessão
                session['tipo_usuario'] = 'admin'
                session['nome_usuario'] = admin['nome']
                session['usuario_id'] = admin['id']
                flash("Login realizado com sucesso!")
                return redirect(url_for('pagina_inicial'))
            else:
                flash("Usuário ou senha incorretos!")

        # Login de aluno
        elif tipo_usuario == 'aluno':
            matricula = request.form.get('matricula')

            banco = conectar_banco()
            cursor = banco.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE matricula = ?", (matricula,))
            usuario = cursor.fetchone()
            banco.close()

            if usuario:
                # Salvar dados na sessão
                session['tipo_usuario'] = 'aluno'
                session['nome_usuario'] = usuario['nome']
                session['matricula_usuario'] = usuario['matricula']
                session['usuario_id'] = usuario['id']
                flash(f"Bem-vindo, {usuario['nome']}!")
                return redirect(url_for('pagina_inicial'))
            else:
                flash("Matrícula não encontrada!")

    # HTML da página de login
    conteudo_login = '''
    <div class="formulario-login">
        <h2 style="text-align: center; margin-bottom: 30px;">🔐 Entrar no Sistema</h2>

        <div class="selecionar-tipo-usuario">
            <div class="opcao-tipo-usuario" onclick="escolherTipoUsuario('admin')" id="opcao-admin">
                <h3>👨‍💼 Administrador</h3>
                <p>Gerenciar sistema</p>
            </div>
            <div class="opcao-tipo-usuario" onclick="escolherTipoUsuario('aluno')" id="opcao-aluno">
                <h3>👨‍🎓 Estudante</h3>
                <p>Consultar livros</p>
            </div>
        </div>

        <form method="POST" id="formulario-login">
            <input type="hidden" name="tipo_usuario" id="tipo_usuario" value="">

            <div id="campos-admin" style="display: none;">
                <div class="grupo-formulario">
                    <label for="usuario">Usuário:</label>
                    <input type="text" id="usuario" name="usuario">
                </div>
                <div class="grupo-formulario">
                    <label for="senha">Senha:</label>
                    <input type="password" id="senha" name="senha">
                </div>
            </div>

            <div id="campos-aluno" style="display: none;">
                <div class="grupo-formulario">
                    <label for="matricula">Matrícula:</label>
                    <input type="text" id="matricula" name="matricula" placeholder="Digite sua matrícula">
                </div>
            </div>

            <button type="submit" class="botao" id="botao-entrar" style="width: 100%; display: none;">Entrar</button>
        </form>

        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <a href="/cadastro" style="color: #2196F3; text-decoration: none; font-weight: bold;">
                ➕ Cadastrar como administrador
            </a>
        </div>

        <div style="text-align: center; margin-top: 15px;">
            <small>
                <strong>Para teste:</strong><br>
                Admin - Usuário: admin / Senha: admin123<br>
                Aluno - Matrícula: 2024001
            </small>
        </div>
    </div>

    <script>
        function escolherTipoUsuario(tipo) {
            // Limpar seleções anteriores
            document.getElementById('opcao-admin').classList.remove('selecionado');
            document.getElementById('opcao-aluno').classList.remove('selecionado');
            document.getElementById('campos-admin').style.display = 'none';
            document.getElementById('campos-aluno').style.display = 'none';

            // Aplicar nova seleção
            document.getElementById('opcao-' + tipo).classList.add('selecionado');
            document.getElementById('campos-' + tipo).style.display = 'block';
            document.getElementById('tipo_usuario').value = tipo;
            document.getElementById('botao-entrar').style.display = 'block';
        }
    </script>
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Login", conteudo=conteudo_login)

# Página de cadastro de administradores
@app.route("/cadastro", methods=["GET", "POST"])
def pagina_cadastro():
    if request.method == "POST":
        nome = request.form.get('nome')
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')

        # Validar dados
        if not nome or not usuario or not senha:
            flash("Preencha todos os campos!")
        elif senha != confirmar_senha:
            flash("As senhas não são iguais!")
        elif len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres!")
        else:
            banco = conectar_banco()
            cursor = banco.cursor()

            try:
                cursor.execute("""
                    INSERT INTO administradores (nome, usuario, senha)
                    VALUES (?, ?, ?)
                """, (nome, usuario, senha))
                banco.commit()
                flash("Administrador cadastrado! Faça login agora.")
                return redirect(url_for('pagina_login'))
            except sqlite3.IntegrityError:
                flash("Este nome de usuário já existe!")
            except Exception as e:
                flash(f"Erro: {str(e)}")
            finally:
                banco.close()

    conteudo_cadastro = '''
    <div class="formulario-login">
        <h2 style="text-align: center; margin-bottom: 30px;">📝 Cadastrar Administrador</h2>

        <form method="POST">
            <div class="grupo-formulario">
                <label for="nome">Nome Completo:</label>
                <input type="text" id="nome" name="nome" required>
            </div>
            <div class="grupo-formulario">
                <label for="usuario">Nome de Usuário:</label>
                <input type="text" id="usuario" name="usuario" required>
            </div>
            <div class="grupo-formulario">
                <label for="senha">Senha:</label>
                <input type="password" id="senha" name="senha" required>
            </div>
            <div class="grupo-formulario">
                <label for="confirmar_senha">Confirmar Senha:</label>
                <input type="password" id="confirmar_senha" name="confirmar_senha" required>
            </div>

            <button type="submit" class="botao" style="width: 100%;">Cadastrar</button>
        </form>

        <div style="text-align: center; margin-top: 30px;">
            <a href="/login" style="color: #2196F3; text-decoration: none; font-weight: bold;">
                ← Voltar para Login
            </a>
        </div>
    </div>
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Cadastro", conteudo=conteudo_cadastro)

# Página para sair do sistema
@app.route("/sair")
def sair_sistema():
    session.clear()
    flash("Você saiu do sistema!")
    return redirect(url_for('pagina_login'))

# Página de livros
@app.route("/livros")
@precisa_login
def pagina_livros():
    # Buscar todos os livros
    banco = conectar_banco()
    cursor = banco.cursor()
    cursor.execute("SELECT * FROM livros ORDER BY titulo")
    livros = cursor.fetchall()
    banco.close()

    # Criar tabela HTML com os livros
    tabela_livros = ""
    if livros:
        tabela_livros = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Título</th>
                    <th>Autor</th>
                    <th>ISBN</th>
                    <th>Ano</th>
                    <th>Quantidade</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        '''
        for livro in livros:
            if livro['quantidade'] > 0:
                status = "✅ Disponível"
                cor_status = "green"
            else:
                status = "❌ Indisponível"
                cor_status = "red"

            tabela_livros += f'''
                <tr>
                    <td>{livro['id']}</td>
                    <td>{livro['titulo']}</td>
                    <td>{livro['autor']}</td>
                    <td>{livro['isbn'] or 'N/A'}</td>
                    <td>{livro['ano'] or 'N/A'}</td>
                    <td>{livro['quantidade']}</td>
                    <td style="color: {cor_status}; font-weight: bold;">{status}</td>
                </tr>
            '''
        tabela_livros += "</tbody></table>"
    else:
        tabela_livros = "<p>Nenhum livro cadastrado.</p>"

    # Formulário para cadastrar livro (só para admins)
    formulario_cadastro = ""
    if usuario_eh_admin():
        formulario_cadastro = '''
        <h3>➕ Cadastrar Novo Livro</h3>
        <form method="POST" action="/cadastrar_livro">
            <div class="grupo-formulario">
                <label for="titulo">Título:</label>
                <input type="text" id="titulo" name="titulo" required>
            </div>
            <div class="grupo-formulario">
                <label for="autor">Autor:</label>
                <input type="text" id="autor" name="autor" required>
            </div>
            <div class="grupo-formulario">
                <label for="isbn">ISBN:</label>
                <input type="text" id="isbn" name="isbn">
            </div>
            <div class="grupo-formulario">
                <label for="ano">Ano:</label>
                <input type="number" id="ano" name="ano" min="1800" max="2030">
            </div>
            <div class="grupo-formulario">
                <label for="quantidade">Quantidade:</label>
                <input type="number" id="quantidade" name="quantidade" min="1" value="1" required>
            </div>
            <button type="submit" class="botao">Cadastrar Livro</button>
        </form>
        '''

    # Título da seção
    if usuario_eh_aluno():
        titulo_secao = "📖 Livros da Biblioteca"
    else:
        titulo_secao = "📖 Gerenciar Livros"

    conteudo_livros = f'''
    <h2>{titulo_secao}</h2>

    {formulario_cadastro}

    <h3>📚 Lista de Livros</h3>
    {tabela_livros}
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Livros", conteudo=conteudo_livros)

# Ação para cadastrar livro
@app.route("/cadastrar_livro", methods=["POST"])
@precisa_ser_admin
def acao_cadastrar_livro():
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    isbn = request.form.get('isbn') or None
    ano = request.form.get('ano') or None
    quantidade = request.form.get('quantidade', 1)

    banco = conectar_banco()
    cursor = banco.cursor()

    try:
        cursor.execute("""
            INSERT INTO livros (titulo, autor, isbn, ano, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, autor, isbn, ano, quantidade))
        banco.commit()
        flash(f"Livro '{titulo}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        flash("Este ISBN já existe!")
    except Exception as e:
        flash(f"Erro: {str(e)}")
    finally:
        banco.close()

    return redirect(url_for('pagina_livros'))

# Página de usuários (só admins)
@app.route("/usuarios")
@precisa_ser_admin
def pagina_usuarios():
    # Buscar todos os usuários
    banco = conectar_banco()
    cursor = banco.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()
    banco.close()

    # Criar tabela HTML
    tabela_usuarios = ""
    if usuarios:
        tabela_usuarios = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Matrícula</th>
                    <th>Curso</th>
                </tr>
            </thead>
            <tbody>
        '''
        for usuario in usuarios:
            tabela_usuarios += f'''
                <tr>
                    <td>{usuario['id']}</td>
                    <td>{usuario['nome']}</td>
                    <td>{usuario['matricula']}</td>
                    <td>{usuario['curso'] or 'N/A'}</td>
                </tr>
            '''
        tabela_usuarios += "</tbody></table>"
    else:
        tabela_usuarios = "<p>Nenhum usuário cadastrado.</p>"

    conteudo_usuarios = f'''
    <h2>👥 Gerenciar Usuários</h2>

    <h3>➕ Cadastrar Novo Usuário</h3>
    <form method="POST" action="/cadastrar_usuario">
        <div class="grupo-formulario">
            <label for="nome">Nome Completo:</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div class="grupo-formulario">
            <label for="matricula">Matrícula:</label>
            <input type="text" id="matricula" name="matricula" required>
        </div>
        <div class="grupo-formulario">
            <label for="curso">Curso:</label>
            <input type="text" id="curso" name="curso">
        </div>
        <button type="submit" class="botao">Cadastrar Usuário</button>
    </form>

    <h3>👥 Lista de Usuários</h3>
    {tabela_usuarios}
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Usuários", conteudo=conteudo_usuarios)

# Ação para cadastrar usuário
@app.route("/cadastrar_usuario", methods=["POST"])
@precisa_ser_admin
def acao_cadastrar_usuario():
    nome = request.form.get('nome')
    matricula = request.form.get('matricula')
    curso = request.form.get('curso') or None

    banco = conectar_banco()
    cursor = banco.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, matricula, curso)
            VALUES (?, ?, ?)
        """, (nome, matricula, curso))
        banco.commit()
        flash(f"Usuário '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        flash("Esta matrícula já existe!")
    except Exception as e:
        flash(f"Erro: {str(e)}")
    finally:
        banco.close()

    return redirect(url_for('pagina_usuarios'))

# Página de empréstimos (só admins)
@app.route("/emprestimos")
@precisa_ser_admin
def pagina_emprestimos():
    banco = conectar_banco()
    cursor = banco.cursor()

    # Buscar usuários
    cursor.execute("SELECT * FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()

    # Buscar livros disponíveis
    cursor.execute("SELECT * FROM livros WHERE quantidade > 0 ORDER BY titulo")
    livros = cursor.fetchall()

    # Buscar empréstimos ativos
    cursor.execute("""
        SELECT e.*, u.nome as usuario_nome, u.matricula, l.titulo as livro_titulo
        FROM emprestimos e
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN livros l ON e.livro_id = l.id
        WHERE e.status = 'emprestado'
        ORDER BY e.data_emprestimo DESC
    """)
    emprestimos = cursor.fetchall()

    banco.close()

    # Criar opções para formulário
    opcoes_usuarios = ""
    for usuario in usuarios:
        opcoes_usuarios += f'<option value="{usuario["id"]}">{usuario["nome"]} ({usuario["matricula"]})</option>'

    opcoes_livros = ""
    for livro in livros:
        opcoes_livros += f'<option value="{livro["id"]}">{livro["titulo"]} - {livro["autor"]} (Qtd: {livro["quantidade"]})</option>'

    # Criar tabela de empréstimos
    tabela_emprestimos = ""
    if emprestimos:
        tabela_emprestimos = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Livro</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                    <th>Status</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in emprestimos:
            data_prevista = datetime.strptime(emp['data_prevista'], '%Y-%m-%d')
            hoje = datetime.now()
            
            if data_prevista < hoje:
                status_texto = "ATRASADO"
                cor_status = "red"
            else:
                status_texto = "No prazo"
                cor_status = "green"

            tabela_emprestimos += f'''
                <tr>
                    <td>{emp['id']}</td>
                    <td>{emp['usuario_nome']} ({emp['matricula']})</td>
                    <td>{emp['livro_titulo']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{data_prevista.strftime('%d/%m/%Y')}</td>
                    <td style="color: {cor_status}; font-weight: bold;">{status_texto}</td>
                    <td>
                        <form method="POST" action="/devolver_livro" style="display: inline;">
                            <input type="hidden" name="emprestimo_id" value="{emp['id']}">
                            <button type="submit" class="botao" style="padding: 5px 10px; font-size: 12px;">Devolver</button>
                        </form>
                    </td>
                </tr>
            '''
        tabela_emprestimos += "</tbody></table>"
    else:
        tabela_emprestimos = "<p>Nenhum empréstimo ativo.</p>"

    conteudo_emprestimos = f'''
    <h2>📋 Gerenciar Empréstimos</h2>

    <h3>➕ Fazer Novo Empréstimo</h3>
    <form method="POST" action="/fazer_emprestimo">
        <div class="grupo-formulario">
            <label for="usuario_id">Usuário:</label>
            <select id="usuario_id" name="usuario_id" required>
                <option value="">Escolha um usuário</option>
                {opcoes_usuarios}
            </select>
        </div>
        <div class="grupo-formulario">
            <label for="livro_id">Livro:</label>
            <select id="livro_id" name="livro_id" required>
                <option value="">Escolha um livro</option>
                {opcoes_livros}
            </select>
        </div>
        <button type="submit" class="botao">Fazer Empréstimo</button>
    </form>

    <h3>📚 Empréstimos Ativos</h3>
    {tabela_emprestimos}
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Empréstimos", conteudo=conteudo_emprestimos)

# Página de empréstimos do aluno
@app.route("/meus_emprestimos")
@precisa_login
def pagina_meus_emprestimos():
    # Só alunos podem ver esta página
    if not usuario_eh_aluno():
        return redirect(url_for('pagina_emprestimos'))

    banco = conectar_banco()
    cursor = banco.cursor()

    # Buscar empréstimos ativos do aluno
    cursor.execute("""
        SELECT e.*, l.titulo as livro_titulo, l.autor
        FROM emprestimos e
        JOIN livros l ON e.livro_id = l.id
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE u.matricula = ? AND e.status = 'emprestado'
        ORDER BY e.data_emprestimo DESC
    """, (session.get('matricula_usuario'),))
    emprestimos = cursor.fetchall()

    # Buscar histórico
    cursor.execute("""
        SELECT e.*, l.titulo as livro_titulo, l.autor
        FROM emprestimos e
        JOIN livros l ON e.livro_id = l.id
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE u.matricula = ? AND e.status = 'devolvido'
        ORDER BY e.data_devolucao DESC
        LIMIT 10
    """, (session.get('matricula_usuario'),))
    historico = cursor.fetchall()

    banco.close()

    # Criar tabela de empréstimos ativos
    tabela_emprestimos = ""
    if emprestimos:
        tabela_emprestimos = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in emprestimos:
            data_prevista = datetime.strptime(emp['data_prevista'], '%Y-%m-%d')
            hoje = datetime.now()
            
            if data_prevista < hoje:
                status_texto = "ATRASADO"
                cor_status = "red"
            else:
                status_texto = "No prazo"
                cor_status = "green"

            tabela_emprestimos += f'''
                <tr>
                    <td>{emp['livro_titulo']}</td>
                    <td>{emp['autor']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{data_prevista.strftime('%d/%m/%Y')}</td>
                    <td style="color: {cor_status}; font-weight: bold;">{status_texto}</td>
                </tr>
            '''
        tabela_emprestimos += "</tbody></table>"
    else:
        tabela_emprestimos = "<p>Você não tem empréstimos ativos.</p>"

    # Criar tabela de histórico
    tabela_historico = ""
    if historico:
        tabela_historico = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Data Empréstimo</th>
                    <th>Data Devolução</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in historico:
            tabela_historico += f'''
                <tr>
                    <td>{emp['livro_titulo']}</td>
                    <td>{emp['autor']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{datetime.strptime(emp['data_devolucao'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                </tr>
            '''
        tabela_historico += "</tbody></table>"
    else:
        tabela_historico = "<p>Nenhum histórico encontrado.</p>"

    conteudo_meus_emprestimos = f'''
    <h2>📋 Meus Empréstimos</h2>

    <h3>📚 Empréstimos Ativos</h3>
    {tabela_emprestimos}

    <div style="margin-top: 40px;">
        <h3>📜 Histórico</h3>
        {tabela_historico}
    </div>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px;">
        <h4>ℹ️ Informações:</h4>
        <ul>
            <li>Você pode ter até 3 livros emprestados</li>
            <li>Prazo de devolução: 7 dias</li>
            <li>Para renovar, procure um administrador</li>
        </ul>
    </div>
    '''

    return render_template_string(TEMPLATE_HTML, titulo="Meus Empréstimos", conteudo=conteudo_meus_emprestimos)

# Ação para fazer empréstimo
@app.route("/fazer_emprestimo", methods=["POST"])
@precisa_ser_admin
def acao_fazer_emprestimo():
    usuario_id = request.form.get('usuario_id')
    livro_id = request.form.get('livro_id')

    banco = conectar_banco()
    cursor = banco.cursor()

    try:
        # Verificar limite de empréstimos
        cursor.execute("""
            SELECT COUNT(*) as total FROM emprestimos 
            WHERE usuario_id = ? AND status = 'emprestado'
        """, (usuario_id,))
        total_emprestimos = cursor.fetchone()['total']

        if total_emprestimos >= 3:
            flash("Este usuário já tem 3 livros emprestados!")
            banco.close()
            return redirect(url_for('pagina_emprestimos'))

        # Verificar se livro está disponível
        cursor.execute("SELECT quantidade FROM livros WHERE id = ?", (livro_id,))
        livro = cursor.fetchone()

        if not livro or livro['quantidade'] <= 0:
            flash("Este livro não está disponível!")
            banco.close()
            return redirect(url_for('pagina_emprestimos'))

        # Fazer empréstimo
        data_emprestimo = datetime.now().strftime('%Y-%m-%d')
        data_prevista = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, livro_id, data_emprestimo, data_prevista))

        # Diminuir quantidade do livro
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?
        """, (livro_id,))

        banco.commit()
        flash("Empréstimo realizado com sucesso!")

    except Exception as e:
        flash(f"Erro: {str(e)}")
    finally:
        banco.close()

    return redirect(url_for('pagina_emprestimos'))

# Ação para devolver livro
@app.route("/devolver_livro", methods=["POST"])
@precisa_ser_admin
def acao_devolver_livro():
    emprestimo_id = request.form.get('emprestimo_id')

    banco = conectar_banco()
    cursor = banco.cursor()

    try:
        # Buscar dados do empréstimo
        cursor.execute("""
            SELECT e.*, l.titulo FROM emprestimos e
            JOIN livros l ON e.livro_id = l.id
            WHERE e.id = ?
        """, (emprestimo_id,))
        emprestimo = cursor.fetchone()

        if not emprestimo:
            flash("Empréstimo não encontrado!")
            banco.close()
            return redirect(url_for('pagina_emprestimos'))

        # Marcar como devolvido
        data_devolucao = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE emprestimos 
            SET data_devolucao = ?, status = 'devolvido'
            WHERE id = ?
        """, (data_devolucao, emprestimo_id))

        # Aumentar quantidade do livro
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade + 1 WHERE id = ?
        """, (emprestimo['livro_id'],))

        banco.commit()
        flash(f"Livro '{emprestimo['titulo']}' devolvido!")

    except Exception as e:
        flash(f"Erro: {str(e)}")
    finally:
        banco.close()

    return redirect(url_for('pagina_emprestimos'))

# Página de relatórios
@app.route("/relatorios")
@precisa_login
def pagina_relatorios():
    banco = conectar_banco()
    cursor = banco.cursor()

    if usuario_eh_admin():
        # Relatórios para admin

        # Livros emprestados
        cursor.execute("""
            SELECT l.titulo, l.autor, u.nome as usuario_nome, u.matricula,
                   e.data_emprestimo, e.data_prevista
            FROM emprestimos e
            JOIN livros l ON e.livro_id = l.id
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.status = 'emprestado'
            ORDER BY e.data_emprestimo DESC
        """)
        livros_emprestados = cursor.fetchall()

        # Empréstimos atrasados
        cursor.execute("""
            SELECT u.nome, u.matricula, u.curso, l.titulo, 
                   e.data_emprestimo, e.data_prevista,
                   julianday('now') - julianday(e.data_prevista) as dias_atraso
            FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            JOIN livros l ON e.livro_id = l.id
            WHERE e.status = 'emprestado' AND e.data_prevista < DATE('now')
            ORDER BY dias_atraso DESC
        """)
        emprestimos_atrasados = cursor.fetchall()

        # Livros disponíveis
        cursor.execute("""
            SELECT titulo, autor, isbn, ano, quantidade
            FROM livros
            WHERE quantidade > 0
            ORDER BY titulo
        """)
        livros_disponiveis = cursor.fetchall()

    else:
        # Para alunos só mostrar livros disponíveis
        livros_emprestados = []
        emprestimos_atrasados = []

        cursor.execute("""
            SELECT titulo, autor, isbn, ano, quantidade
            FROM livros
            WHERE quantidade > 0
            ORDER BY titulo
        """)
        livros_disponiveis = cursor.fetchall()

    banco.close()

    # Função para criar tabela de emprestados
    def criar_tabela_emprestados():
        if not livros_emprestados:
            return "<p>Nenhum livro emprestado no momento.</p>"

        html = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Usuário</th>
                    <th>Matrícula</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                </tr>
            </thead>
            <tbody>
        '''
        for item in livros_emprestados:
            html += f'''
                <tr>
                    <td>{item['titulo']}</td>
                    <td>{item['autor']}</td>
                    <td>{item['usuario_nome']}</td>
                    <td>{item['matricula']}</td>
                    <td>{datetime.strptime(item['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{datetime.strptime(item['data_prevista'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    # Função para criar tabela de atrasados
    def criar_tabela_atrasados():
        if not emprestimos_atrasados:
            return "<p>Nenhum empréstimo em atraso! 🎉</p>"

        html = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>Usuário</th>
                    <th>Matrícula</th>
                    <th>Curso</th>
                    <th>Livro</th>
                    <th>Data Prevista</th>
                    <th>Dias de Atraso</th>
                </tr>
            </thead>
            <tbody>
        '''
        for item in emprestimos_atrasados:
            dias_atraso = int(item['dias_atraso'])
            html += f'''
                <tr style="background-color: #ffebee;">
                    <td>{item['nome']}</td>
                    <td>{item['matricula']}</td>
                    <td>{item['curso'] or 'N/A'}</td>
                    <td>{item['titulo']}</td>
                    <td>{datetime.strptime(item['data_prevista'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td style="color: red; font-weight: bold;">{dias_atraso} dias</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    # Função para criar tabela de disponíveis
    def criar_tabela_disponiveis():
        if not livros_disponiveis:
            return "<p>Nenhum livro disponível.</p>"

        html = '''
        <table class="tabela">
            <thead>
                <tr>
                    <th>Título</th>
                    <th>Autor</th>
                    <th>ISBN</th>
                    <th>Ano</th>
                    <th>Quantidade</th>
                </tr>
            </thead>
            <tbody>
        '''
        for livro in livros_disponiveis:
            html += f'''
                <tr>
                    <td>{livro['titulo']}</td>
                    <td>{livro['autor']}</td>
                    <td>{livro['isbn'] or 'N/A'}</td>
                    <td>{livro['ano'] or 'N/A'}</td>
                    <td style="color: green; font-weight: bold;">{livro['quantidade']}</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    # Conteúdo diferente para admin e aluno
    if usuario_eh_admin():
        conteudo_relatorios = f'''
        <h2>📊 Relatórios da Biblioteca</h2>

        <div style="margin-bottom: 40px;">
            <h3>📚 Livros Emprestados</h3>
            {criar_tabela_emprestados()}
        </div>

        <div style="margin-bottom: 40px;">
            <h3>⚠️ Empréstimos Atrasados</h3>
            {criar_tabela_atrasados()}
        </div>

        <div style="margin-bottom: 40px;">
            <h3>✅ Livros Disponíveis</h3>
            {criar_tabela_disponiveis()}
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" class="botao">🖨️ Imprimir</button>
        </div>
        '''
    else:
        conteudo_relatorios = f'''
        <h2>📊 Livros Disponíveis</h2>

        <div style="margin-bottom: 40px;">
            <h3>✅ Livros para Empréstimo</h3>
            {criar_tabela_disponiveis()}
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px;">
            <h4>ℹ️ Como emprestar:</h4>
            <p>Para emprestar um livro, procure um administrador com sua matrícula e o nome do livro.</p>
        </div>
        '''

    return render_template_string(TEMPLATE_HTML, titulo="Relatórios", conteudo=conteudo_relatorios)

# Função para inserir dados de exemplo
def inserir_dados_exemplo():
    banco = conectar_banco()
    cursor = banco.cursor()

    # Verificar se já tem dados
    cursor.execute("SELECT COUNT(*) as total FROM livros")
    if cursor.fetchone()['total'] > 0:
        banco.close()
        return

    # Inserir livros de exemplo
    livros_exemplo = [
        ("Dom Casmurro", "Machado de Assis", "978-85-359-0277-5", 1899, 2),
        ("O Cortiço", "Aluísio Azevedo", "978-85-260-1631-8", 1890, 1),
        ("Capitães da Areia", "Jorge Amado", "978-85-254-0024-7", 1937, 3),
        ("Python para Iniciantes", "Eric Matthes", "978-85-7522-718-3", 2019, 2),
        ("Algoritmos e Estruturas de Dados", "Thomas Cormen", "978-85-352-8913-9", 2012, 1),
        ("História do Brasil", "Boris Fausto", "978-85-314-0556-2", 2013, 2)
    ]

    for livro in livros_exemplo:
        cursor.execute("""
            INSERT INTO livros (titulo, autor, isbn, ano, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, livro)

    # Inserir usuários de exemplo
    usuarios_exemplo = [
        ("João Silva Santos", "2024001", "Análise e Desenvolvimento de Sistemas"),
        ("Maria Oliveira Lima", "2024002", "Engenharia de Software"),
        ("Pedro Costa Ferreira", "2024003", "Sistemas de Informação"),
        ("Leticia Rodrigues", "2024004", "Química"),
        ("Carlos Eduardo Souza", "2024005", "Zootecnia")
    ]

    for usuario in usuarios_exemplo:
        cursor.execute("""
            INSERT INTO usuarios (nome, matricula, curso)
            VALUES (?, ?, ?)
        """, usuario)

    # Inserir alguns empréstimos de exemplo
    emprestimos_exemplo = [
        (1, 1, "2025-05-20", "2025-05-27"),
        (2, 4, "2025-05-22", "2025-05-29"),
        (3, 5, "2025-05-15", "2025-05-22"),
    ]

    for emp in emprestimos_exemplo:
        cursor.execute("""
            INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista)
            VALUES (?, ?, ?, ?)
        """, emp)

        # Diminuir quantidade do livro
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?
        """, (emp[1],))

    banco.commit()
    banco.close()
    print("Dados de exemplo inseridos!")

# Executar o sistema
if __name__ == "__main__":
    # Configurar banco de dados
    criar_tabelas_banco()
    criar_primeiro_admin()
    inserir_dados_exemplo()
    
    # Mensagens de inicialização
    print("=" * 50)
    print("🚀 SISTEMA DE BIBLIOTECA FUNCIONANDO!")
    print("=" * 50)
    print("📍 Acesse: http://0.0.0.0:5000")
    print("📚 Sistema pronto!")
    print("👨‍💼 Admin: admin / admin123")
    print("👨‍🎓 Alunos: 2024001 a 2024005")
    print("=" * 50)
    
    # Iniciar servidor
    app.run(debug=True, host='0.0.0.0', port=5000)
