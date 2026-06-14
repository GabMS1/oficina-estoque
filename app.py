from flask import Flask, request, redirect, url_for, render_template
import pandas as pd
from sqlalchemy import create_engine, text

app = Flask(__name__)

USUARIO = 'app_user'
SENHA = 'user_password_oficina'
HOST = '127.0.0.1'
PORTA = '3307'
BANCO = 'oficina_hidraulica'

string_conexao = f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}?charset=utf8mb4"
engine = create_engine(string_conexao)

@app.route('/')
def mostrar_estoque():
    # Query principal atualizada para puxar o ENDEREÇO
    query_estoque = """
        SELECT 
            p.id AS cod,
            c.nome AS categoria,
            m.nome AS marca,
            p.nome AS produto,
            p.preco_custo AS custo,
            p.preco_venda AS venda,
            CONCAT(end.setor, ' > ', end.estante, ' > ', end.gaveta) AS localizacao,
            COALESCE(e.quantidade_atual, 0) AS qtd_estoque,
            (COALESCE(e.quantidade_atual, 0) * p.preco_custo) AS total_custo
        FROM produtos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        INNER JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN enderecos_estoque end ON p.endereco_id = end.id
        LEFT JOIN estoque_atual e ON p.id = e.produto_id;
    """
    
    query_categorias = """
        SELECT 
            c.nome AS categoria,
            SUM(COALESCE(e.quantidade_atual, 0) * p.preco_custo) AS total_custo
        FROM produtos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN estoque_atual e ON p.id = e.produto_id
        GROUP BY c.nome;
    """
    
    try:
        with engine.connect() as conn:
            total_produtos_cadastrados = conn.execute(text("SELECT COUNT(*) FROM produtos")).scalar() or 0
            total_itens_estoque = conn.execute(text("SELECT SUM(quantidade_atual) FROM estoque_atual")).scalar() or 0
        
        df_estoque = pd.read_sql(query_estoque, engine)
        df_cat = pd.read_sql(query_categorias, engine)
        
        valor_financeiro_total = df_estoque['total_custo'].sum() if not df_estoque.empty else 0.0
        
        lista_produtos = df_estoque.to_dict('records')
        lista_categorias = df_cat.to_dict('records')

        return render_template('index.html', 
                               produtos=lista_produtos,
                               categorias_valores=lista_categorias,
                               total_produtos=total_produtos_cadastrados,
                               total_itens=total_itens_estoque,
                               valor_total=f"{valor_financeiro_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    except Exception as e:
        return f"<h1>Erro ao carregar o banco de dados:</h1><p>{e}</p>"

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

@app.route('/novo_produto')
def novo_produto():
    return render_template('novo_produto.html')

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    nome = request.form['nome']
    categoria_nome = request.form['categoria_nome'].strip()
    marca_nome = request.form['marca_nome'].strip()
    preco_custo = request.form['preco_custo']
    preco_venda = request.form['preco_venda']
    
    # NOVOS CAMPOS DO ENDEREÇO
    setor = request.form['setor'].strip()
    estante = request.form['estante'].strip()
    gaveta = request.form['gaveta'].strip()

    try:
        with engine.connect() as conn:
            # Busca ou Cria Categoria
            query_busca_cat = text("SELECT id FROM categorias WHERE nome = :nome")
            cat_id = conn.execute(query_busca_cat, {"nome": categoria_nome}).scalar()
            if not cat_id:
                conn.execute(text("INSERT INTO categorias (nome) VALUES (:nome)"), {"nome": categoria_nome})
                cat_id = conn.execute(query_busca_cat, {"nome": categoria_nome}).scalar()

            # Busca ou Cria Marca
            query_busca_marca = text("SELECT id FROM marcas WHERE nome = :nome")
            marca_id = conn.execute(query_busca_marca, {"nome": marca_nome}).scalar()
            if not marca_id:
                conn.execute(text("INSERT INTO marcas (nome) VALUES (:nome)"), {"nome": marca_nome})
                marca_id = conn.execute(query_busca_marca, {"nome": marca_nome}).scalar()

            # BUSCA OU CRIA ENDEREÇO (A Mágica da Oficina)
            query_busca_end = text("SELECT id FROM enderecos_estoque WHERE setor = :setor AND estante = :estante AND gaveta = :gaveta")
            end_id = conn.execute(query_busca_end, {"setor": setor, "estante": estante, "gaveta": gaveta}).scalar()
            if not end_id:
                query_insere_end = text("INSERT INTO enderecos_estoque (setor, estante, gaveta) VALUES (:setor, :estante, :gaveta)")
                conn.execute(query_insere_end, {"setor": setor, "estante": estante, "gaveta": gaveta})
                end_id = conn.execute(query_busca_end, {"setor": setor, "estante": estante, "gaveta": gaveta}).scalar()

            # Salva o Produto linkado com Categoria, Marca e Endereço
            query_produto = text("""
                INSERT INTO produtos (nome, categoria_id, marca_id, endereco_id, preco_custo, preco_venda)
                VALUES (:nome, :categoria_id, :marca_id, :endereco_id, :preco_custo, :preco_venda)
            """)
            conn.execute(query_produto, {
                "nome": nome,
                "categoria_id": cat_id,
                "marca_id": marca_id,
                "endereco_id": end_id,
                "preco_custo": preco_custo,
                "preco_venda": preco_venda
            })
            
            conn.commit()

    except Exception as e:
        print(f"Erro ao cadastrar produto: {e}")

    return redirect(url_for('mostrar_estoque'))

if __name__ == '__main__':
    app.run(debug=True)