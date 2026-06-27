from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy import create_engine, text
import pandas as pd

app = Flask(__name__)
engine = create_engine("mysql+pymysql://app_user:user_password_oficina@127.0.0.1:3307/oficina_hidraulica")

@app.route('/')
def mostrar_estoque():
    query = """
        SELECT p.id, p.nome, c.nome as categoria, m.nome as marca, 
               CONCAT(e.setor, ' > ', e.estante, ' > ', e.gaveta) as local,
               COALESCE(ea.quantidade_atual, 0) as qtd
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN marcas m ON p.marca_id = m.id
        LEFT JOIN enderecos_estoque e ON p.endereco_id = e.id
        LEFT JOIN estoque_atual ea ON p.id = ea.produto_id
    """
    produtos = pd.read_sql(query, engine).to_dict('records')
    return render_template('index.html', produtos=produtos)

@app.route('/movimentar', methods=['POST'])
def movimentar():
    p_id = request.form['produto_id']
    tipo = request.form['tipo']
    qtd = int(request.form['quantidade'])
    
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade) VALUES (:p, :t, :q)"), {"p": p_id, "t": tipo, "q": qtd})
        
        valor = qtd if tipo == 'entrada' else -qtd
        conn.execute(text("INSERT INTO estoque_atual (produto_id, quantidade_atual) VALUES (:p, :q) ON DUPLICATE KEY UPDATE quantidade_atual = quantidade_atual + :q"), {"p": p_id, "q": valor})
        conn.commit()
    return redirect(url_for('mostrar_estoque'))

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