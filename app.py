from flask import Flask, request, redirect, url_for, render_template
import pandas as pd
from sqlalchemy import create_engine, text

app = Flask(__name__)

# 1. Configurações de Conexão com o Banco
USUARIO = 'app_user'
SENHA = 'user_password_oficina'
HOST = '127.0.0.1'
PORTA = '3307'  # Verifique sua porta (3306 ou 3307)
BANCO = 'oficina_hidraulica'

string_conexao = f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}?charset=utf8mb4"
engine = create_engine(string_conexao)

# ... (Suas importações e conexão com o banco continuam aqui em cima) ...

@app.route('/')
def mostrar_estoque():
    query = """
        SELECT 
            p.id AS 'Cód.',
            c.nome AS 'Categoria',
            m.nome AS 'Marca',
            p.nome AS 'Produto',
            p.preco_custo AS 'Custo (R$)',
            p.preco_venda AS 'Venda (R$)',
            COALESCE(e.quantidade_atual, 0) AS 'Qtd. Estoque',
            (COALESCE(e.quantidade_atual, 0) * p.preco_custo) AS 'Total Custo (R$)'
        FROM produtos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        INNER JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN estoque_atual e ON p.id = e.produto_id;
    """
    
    try:
        df_estoque = pd.read_sql(query, engine)
        tabela_html = df_estoque.to_html(index=False, classes='table table-striped', justify='center')
        
        # Lógica do Dashboard
        with engine.connect() as conn:
            total_produtos_cadastrados = conn.execute(text("SELECT COUNT(*) FROM produtos")).scalar() or 0
            total_itens_estoque = conn.execute(text("SELECT SUM(quantidade_atual) FROM estoque_atual")).scalar() or 0
        
        # Calcula o valor total usando o Pandas
        valor_financeiro_total = df_estoque['Total Custo (R$)'].sum() if not df_estoque.empty else 0.0

        return render_template('index.html', 
                               tabela_html=tabela_html,
                               total_produtos=total_produtos_cadastrados,
                               total_itens=total_itens_estoque,
                               valor_total=f"{valor_financeiro_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")) # Formata para R$ BR

    except Exception as e:
        return f"<h1>Erro ao carregar o banco de dados:</h1><p>{e}</p>"

# --- NOVA ROTA PARA A TELA DE MOVIMENTAÇÃO ---
@app.route('/nova_movimentacao')
def nova_movimentacao():
    return render_template('nova_movimentacao.html')

@app.route('/movimentar', methods=['POST'])
def movimentar_estoque():
    produto_id = request.form['produto_id']
    tipo = request.form['tipo']
    quantidade = request.form['quantidade']
    valor_unitario = request.form['valor_unitario']
    motivo = request.form['motivo']

    query = text("""
        INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade, valor_unitario, motivo)
        VALUES (:produto_id, :tipo, :quantidade, :valor_unitario, :motivo)
    """)

    try:
        with engine.connect() as conn:
            conn.execute(query, {
                "produto_id": produto_id,
                "tipo": tipo,
                "quantidade": quantidade,
                "valor_unitario": valor_unitario,
                "motivo": motivo
            })
            conn.commit()
    except Exception as e:
        print(f"Erro ao inserir: {e}")

    return redirect(url_for('mostrar_estoque'))

# ... (seu código anterior continua lá em cima) ...

@app.route('/novo_produto')
def novo_produto():
    # A tela agora não precisa mais carregar listas do banco, ela apenas abre o HTML limpo
    return render_template('novo_produto.html')

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    nome = request.form['nome']
    # O .strip() remove espaços em branco que o usuário possa ter digitado sem querer no início ou fim
    categoria_nome = request.form['categoria_nome'].strip()
    marca_nome = request.form['marca_nome'].strip()
    preco_custo = request.form['preco_custo']
    preco_venda = request.form['preco_venda']

    try:
        with engine.connect() as conn:
            # --- 1. LÓGICA DA CATEGORIA (Buscar ou Criar) ---
            query_busca_cat = text("SELECT id FROM categorias WHERE nome = :nome")
            cat_id = conn.execute(query_busca_cat, {"nome": categoria_nome}).scalar()
            
            if not cat_id: # Se não achou, insere uma nova
                query_insere_cat = text("INSERT INTO categorias (nome) VALUES (:nome)")
                conn.execute(query_insere_cat, {"nome": categoria_nome})
                cat_id = conn.execute(query_busca_cat, {"nome": categoria_nome}).scalar()

            # --- 2. LÓGICA DA MARCA (Buscar ou Criar) ---
            query_busca_marca = text("SELECT id FROM marcas WHERE nome = :nome")
            marca_id = conn.execute(query_busca_marca, {"nome": marca_nome}).scalar()
            
            if not marca_id: # Se não achou, insere uma nova
                query_insere_marca = text("INSERT INTO marcas (nome) VALUES (:nome)")
                conn.execute(query_insere_marca, {"nome": marca_nome})
                marca_id = conn.execute(query_busca_marca, {"nome": marca_nome}).scalar()

            # --- 3. INSERIR O PRODUTO ---
            # Agora já temos o cat_id e o marca_id garantidos
            query_produto = text("""
                INSERT INTO produtos (nome, categoria_id, marca_id, preco_custo, preco_venda)
                VALUES (:nome, :categoria_id, :marca_id, :preco_custo, :preco_venda)
            """)
            conn.execute(query_produto, {
                "nome": nome,
                "categoria_id": cat_id,
                "marca_id": marca_id,
                "preco_custo": preco_custo,
                "preco_venda": preco_venda
            })
            
            # Confirma as alterações no banco de uma vez só
            conn.commit()

    except Exception as e:
        print(f"Erro ao cadastrar produto: {e}")

    # Volta para a tela inicial
    return redirect(url_for('mostrar_estoque'))

if __name__ == '__main__':
    app.run(debug=True)