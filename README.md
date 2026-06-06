# 📦 Sistema de Gestão de Estoque - Oficina Mecânica

Sistema web desenvolvido do zero para controle de fluxo de materiais e análise financeira de uma oficina mecânica. O projeto soluciona o problema de controle de peças físicas, oferecendo um painel gerencial em tempo real com métricas de custos e inventário.

## 🚀 Tecnologias Utilizadas
* **Backend:** Python (Flask)
* **Análise e Manipulação de Dados:** Pandas
* **Banco de Dados:** MySQL (Relacional)
* **Infraestrutura:** Docker e Docker Compose
* **Frontend:** HTML5, CSS3 e Jinja2 (Arquitetura MVC)

## 📊 Funcionalidades e Diferenciais Técnicos
* **Dashboard Gerencial:** Cálculo dinâmico do valor total em estoque e contagem de categorias utilizando queries SQL otimizadas e processamento com Pandas.
* **Arquitetura Relacional:** Modelagem de dados estruturada com chaves estrangeiras (Categorias, Marcas, Produtos e Movimentações) garantindo a integridade das informações.
* **Lógica de "Buscar ou Criar":** Algoritmo inteligente no backend que identifica se uma marca/categoria digitada já existe no banco (evitando duplicidade) ou se precisa ser instanciada dinamicamente.
* **Tratamento de Dados Brutos:** Uso da função `COALESCE` e `JOINs` complexos no SQL para cruzar o cadastro de produtos com o saldo real no estoque.

## ⚙️ Como executar o projeto localmente
1. Clone este repositório: `git clone https://github.com/GabMS1/oficina-estoque.git`
2. Suba o banco de dados via Docker: `docker-compose up -d`
3. Crie um arquivo `.env` com as credenciais do banco.
4. Execute a aplicação Flask: `python app.py`
5. Acesse `http://localhost:5000` no navegador.