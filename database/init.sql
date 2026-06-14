CREATE DATABASE IF NOT EXISTS oficina_hidraulica;
USE oficina_hidraulica;

CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS marcas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

-- NOSSA NOVA TABELA DO MAPA (Vem antes dos produtos!)
CREATE TABLE IF NOT EXISTS enderecos_estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor VARCHAR(100) NOT NULL,
    estante VARCHAR(100) NOT NULL,
    gaveta VARCHAR(100) NOT NULL
);

-- TABELA PRODUTOS ATUALIZADA
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    categoria_id INT,
    marca_id INT,
    endereco_id INT,
    preco_custo DECIMAL(10,2) NOT NULL,
    preco_venda DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (marca_id) REFERENCES marcas(id),
    FOREIGN KEY (endereco_id) REFERENCES enderecos_estoque(id)
);

CREATE TABLE IF NOT EXISTS estoque_atual (
    produto_id INT PRIMARY KEY,
    quantidade_atual INT DEFAULT 0,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    tipo ENUM('entrada', 'saida') NOT NULL,
    quantidade INT NOT NULL,
    valor_unitario DECIMAL(10,2) NOT NULL,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(255),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);