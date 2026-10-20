import math
from flask import Blueprint, render_template, request, url_for, flash, redirect
import db

main = Blueprint('main', __name__)

# ============================================================
# PAINEL DE CONTROLE
# ============================================================

@main.route('/')
def dashboard():
    metricas = db.get_metricas_dashboard()
    criticos = db.get_produtos_estoque_baixo()[:5]
    return render_template(
        'index.html',
        metricas=metricas,
        produtos_criticos=criticos
    )
    
# ============================================================
# PRODUTOS
# ============================================================

@main.route('/produtos')
def lista_produtos():
    """
    Lista paginada de todos os produtos.

    Parâmetros GET suportados:
      ?q=termo   → filtro de busca por nome ou SKU
      ?pagina=N  → número da página (padrão: 1)
    """
    # request.args lê os parâmetros da URL (query string)]
    
    busca = request.args.get('q', '').strip()
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 10

    produtos, total = db.get_todos_produtos(
        busca=busca, pagina=pagina, por_pagina=por_pagina
    )
    # math.ceil arredonda para cima: 21 itens / 10 = 3 páginas
    total_paginas = math.ceil(total / por_pagina) if total > 0 else 1

    return render_template(
        'produtos/lista.html',
        produtos=produtos,
        busca=busca,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total
    )
    
@main.route('/produtos/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    """
    GET  → Exibe formulário de cadastro vazio.
    POST → Valida os dados e cria o produto no banco.

    Padrão PRG (Post/Redirect/Get): após salvar com sucesso,
    redirecionamos para evitar que o navegador reenvie o
    formulário ao recarregar a página.
    """
    if request.method == 'POST':
        # Coleta e sanitiza os dados do formulário
        nome = request.form.get('nome', '').strip()
        # SKU sempre em maiúsculas para consistência
        sku = request.form.get('sku', '').strip().upper()
        descricao = request.form.get('descricao', '').strip()
        # Substitui vírgula por ponto para aceitar "1,99" e "1.99"
        preco_str = request.form.get('preco', '0').replace(',', '.')
        quantidade_str = request.form.get('quantidade', '0')
        localizacao = request.form.get('localizacao', '').strip()

        # --- Validação ---
        erros = []

        if not nome:
            erros.append("O nome do produto é obrigatório.")
        if not sku:
            erros.append("O SKU é obrigatório.")

        try:
            preco = float(preco_str)
            if preco < 0:
                erros.append("O preço não pode ser negativo.")
        except ValueError:
            erros.append("Formato de preço inválido. Use números (ex: 29.90).")
            preco = 0.0

        try:
            quantidade = int(quantidade_str)
            if quantidade < 0:
                erros.append("A quantidade não pode ser negativa.")
        except ValueError:
            erros.append("A quantidade deve ser um número inteiro.")
            quantidade = 0

        # Verifica unicidade do SKU
        if sku and db.get_produto_por_sku(sku):
            erros.append(
                f"O SKU '{sku}' já está em uso. Cada produto precisa de um SKU único."
            )

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            # Reenvia os dados para o formulário não perder o que o usuário digitou
            return render_template(
                'produtos/adicionar.html', form_data=request.form
            )

        # Tudo válido → persiste no banco
        db.criar_produto(nome, sku, descricao, preco, quantidade, localizacao)
        flash(f"Produto '{nome}' cadastrado com sucesso!", 'success')
        return redirect(url_for('main.lista_produtos'))

    # Método GET → formulário em branco
    return render_template('produtos/adicionar.html', form_data={})

@main.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    """
    GET  → Formulário preenchido com os dados atuais do produto.
    POST → Valida e salva as alterações.

    O <int:id> na rota é um conversor: Flask garante que 'id'
    seja um inteiro antes de chamar a função.
    """
    produto = db.get_produto_por_id(id)

    if not produto:
        flash("Produto não encontrado.", 'danger')
        return redirect(url_for('main.lista_produtos'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        descricao = request.form.get('descricao', '').strip()
        preco_str = request.form.get('preco', '0').replace(',', '.')
        quantidade_str = request.form.get('quantidade', '0')
        localizacao = request.form.get('localizacao', '').strip()

        erros = []

        if not nome:
            erros.append("O nome do produto é obrigatório.")
        if not sku:
            erros.append("O SKU é obrigatório.")

        try:
            preco = float(preco_str)
            if preco < 0:
                erros.append("O preço não pode ser negativo.")
        except ValueError:
            erros.append("Formato de preço inválido.")
            preco = 0.0

        try:
            quantidade = int(quantidade_str)
            if quantidade < 0:
                erros.append("A quantidade não pode ser negativa.")
        except ValueError:
            erros.append("A quantidade deve ser um número inteiro.")
            quantidade = 0

        # Na edição, excluímos o próprio produto da verificação de SKU
        if sku and db.get_produto_por_sku(sku, excluir_id=id):
            erros.append(f"O SKU '{sku}' já pertence a outro produto.")

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template(
                'produtos/editar.html',
                produto=produto,
                form_data=request.form
            )

        db.atualizar_produto(id, nome, sku, descricao, preco, quantidade, localizacao)
        flash(f"Produto '{nome}' atualizado com sucesso!", 'success')
        return redirect(url_for('main.lista_produtos'))

    # GET → preenche o formulário com os dados atuais
    return render_template(
        'produtos/editar.html',
        produto=produto,
        form_data=produto  # sqlite3.Row se comporta como dict no template
    )

@main.route('/produtos/deletar/<int:id>', methods=['POST'])
def deletar_produto(id):
    """
    Aceita APENAS método POST (nunca GET).
    Isso evita que alguém delete um produto apenas acessando
    uma URL, seja por engano ou de forma maliciosa.
    A confirmação é feita via JavaScript (modal no navegador).
    """
    produto = db.get_produto_por_id(id)

    if produto:
        nome = produto['nome']
        db.deletar_produto(id)
        flash(f"Produto '{nome}' excluído com sucesso.", 'success')
    else:
        flash("Produto não encontrado.", 'danger')

    return redirect(url_for('main.lista_produtos'))

# ============================================================
# RELATÓRIO: ESTOQUE BAIXO
# ============================================================

@main.route('/relatorio/estoque-baixo')
def relatorio_estoque_baixo():
    """Página de relatório listando apenas os produtos com estoque crítico."""
    produtos = db.get_produtos_estoque_baixo()
    return render_template(
        'relatorio/estoque_baixo.html',
        produtos=produtos,
        limiar=db.LIMIAR_ESTOQUE_BAIXO
    )
    
# ============================================================
# TRANSAÇÃO DE ESTOQUE
# ============================================================

@main.route('/produtos/<int:id>/transacao', methods=['GET', 'POST'])
def transacao_estoque(id):
    """
    Permite registrar movimentações rápidas de estoque:
    - Entrada: produto chegou (compra/recebimento)
    - Saída: produto saiu (venda/consumo/perda)

    Mais prático que abrir o formulário de edição completo.
    """
    produto = db.get_produto_por_id(id)

    if not produto:
        flash("Produto não encontrado.", 'danger')
        return redirect(url_for('main.lista_produtos'))

    if request.method == 'POST':
        tipo = request.form.get('tipo')  # 'entrada' ou 'saida'
        quantidade_str = request.form.get('quantidade', '0')

        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise ValueError("Deve ser positivo")
        except ValueError:
            flash(
                "Informe uma quantidade válida (número inteiro maior que zero).",
                'danger'
            )
            return render_template('produtos/transacao.html', produto=produto)

        sucesso, mensagem = db.registrar_transacao(id, tipo, quantidade)

        if sucesso:
            flash(mensagem, 'success')
            return redirect(url_for('main.lista_produtos'))
        else:
            flash(mensagem, 'danger')

    return render_template('produtos/transacao.html', produto=produto)
