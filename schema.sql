CREATE TABLE IF NOT EXISTS produtos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL, 
    sku         TEXT    UNIQUE NOT NULL,
    descricao   TEXT,
    preco       REAL    NOT NULL CHECK(preco >= 0),
    quantidade  INTEGER NOT NULL DEFAULT 0 CHECK(quantidade >= 0),
    localizacao TEXT,
    data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# NOT NULL -> Precisa ser preenchido, não pode ser um campo vazio.
# CURRENT_TEIMSTAMP -> Adiciona a data que foi inserido automaticamente