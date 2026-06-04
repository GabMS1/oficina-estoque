-- Garante a criação do banco de dados caso não exista
CREATE DATABASE IF NOT EXISTS oficina_hidraulica;
USE oficina_hidraulica;

-- 1. Tabela de Categorias
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabela de Marcas
CREATE TABLE IF NOT EXISTS marcas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabela Central de Produtos
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id INT NOT NULL,
    marca_id INT NOT NULL,
    codigo_barras VARCHAR(50) UNIQUE NULL,
    nome VARCHAR(150) NOT NULL,
    especificacoes JSON NULL, -- Guarda { "cor": "azul" } ou { "tamanho": "10mm" }
    preco_custo DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    preco_venda DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    estoque_minimo INT NOT NULL DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
    FOREIGN KEY (marca_id) REFERENCES marcas(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Registro Histórico de Movimentações (Kardex)
CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    tipo ENUM('ENTRADA', 'SAIDA') NOT NULL,
    quantidade INT NOT NULL,
    valor_unitario DECIMAL(10, 2) NOT NULL,
    data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(255) NULL,
    
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Posição de Estoque Atual (Visão Consolidada em Tempo Real)
CREATE TABLE IF NOT EXISTS estoque_atual (
    produto_id INT PRIMARY KEY,
    quantidade_atual INT NOT NULL DEFAULT 0,
    data_ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==========================================
-- GATILHO (TRIGGER) PARA ATUALIZAÇÃO EM TEMPO REAL
-- ==========================================
-- Esse bloco intercepta as inserções de entrada/saída e altera o estoque_atual automaticamente.

DELIMITER //

CREATE TRIGGER tr_atualiza_estoque_atual
AFTER INSERT ON movimentacoes_estoque
FOR EACH ROW
BEGIN
    -- Declaração da variação da quantidade baseado no tipo de movimento
    DECLARE variacao INT;
    
    IF NEW.tipo = 'ENTRADA' THEN
        SET variacao = NEW.quantidade;
    ELSE
        SET variacao = -NEW.quantidade;
    END IF;

    -- Tenta inserir o produto na tabela de saldo atual. Se já existir, atualiza a quantidade somando/subtraindo.
    INSERT INTO estoque_atual (produto_id, quantidade_atual)
    VALUES (NEW.produto_id, variacao)
    ON DUPLICATE KEY UPDATE 
        quantidade_atual = quantidade_atual + variacao;
END //

DELIMITER ;

-- ==========================================
-- INSERÇÃO DE DADOS DE TESTE (OPCIONAL)
-- ==========================================

INSERT INTO categorias (nome) VALUES ('Tinta'), ('Desengripante'), ('Parafuso'), ('Óleo');
INSERT INTO marcas (nome) VALUES ('Suvinil'), ('Coral'), ('Lubrax'), ('WD-40'), ('Ciser');

-- Exemplo de cadastro de um óleo Lubrax 15w40 e uma lata de tinta azul
INSERT INTO produtos (categoria_id, marca_id, nome, especificacoes, preco_custo, preco_venda, estoque_minimo) 
VALUES 
(4, 3, 'Óleo Motor 15W40', '{"viscosidade": "15W40", "tipo": "Mineral"}', 25.00, 45.00, 10),
(1, 1, 'Lata de Tinta Premium', '{"cor": "Azul", "volume": "900ml"}', 40.00, 75.00, 5);