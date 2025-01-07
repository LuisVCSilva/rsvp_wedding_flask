#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from flask import Flask, render_template, redirect, url_for, request
from contextlib import closing
from base64 import b64encode
import sqlite3, re

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', home=True)

@app.route('/igreja.html')
def local():
    return render_template('igreja.html', local=True)

@app.route('/festa.html')
def cerimonia():
    return render_template('festa.html', cerimonia=True)

@app.route('/contato.html')
def contato():
    return render_template('contato.html', contato=True)

def init_db():
    # Connect to SQLite database
    conn = sqlite3.connect('wishlist.sqlite3')
    cursor = conn.cursor()

    # SQL to create the table with additional columns for 'reserver' and 'reservation_date'
    cursor.execute('''CREATE TABLE wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        label TEXT, 
        desc TEXT, 
        link TEXT, 
        booked INTEGER, 
        reserver TEXT, 
        reservation_date TEXT, 
        changed TEXT
    );''')
    cursor.execute('''
    CREATE TABLE rsvp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        names TEXT NOT NULL,
        cerimonia BOOLEAN DEFAULT 0,
        local BOOLEAN DEFAULT 0,
        notes TEXT,
        added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')


def pop_db():
    with closing(sqlite3.connect('wishlist.sqlite3')) as db:
        cur = db.cursor()
        cur.execute('''
    INSERT INTO wishlist (label, desc, link, booked, reserver, reservation_date, changed) VALUES
    ('Geladeira', 'Geladeira', 'https://example.com/geladeira', 0, NULL, NULL, NULL),
    ('Sofá', 'Sofá', 'https://example.com/sofa', 0, NULL, NULL, NULL),
    ('TV (32 a 43)', 'TV entre 32 e 43 polegadas', 'https://example.com/tv', 0, NULL, NULL, NULL),
    ('Rack ou painel para TV', 'Rack ou painel para TV', 'https://example.com/rack', 0, NULL, NULL, NULL),
    ('Cortinas', 'Cortinas para a sala de estar', 'https://example.com/cortinas', 0, NULL, NULL, NULL),
    ('Microondas', 'Microondas', 'https://example.com/microondas', 0, NULL, NULL, NULL),
    ('Guarda-roupa', 'Guarda-roupa', 'https://example.com/guarda-roupa', 0, NULL, NULL, NULL),
    ('Liquidificador', 'Liquidificador', 'https://example.com/liquidificador', 0, NULL, NULL, NULL),
    ('Mesa de jantar (4 cadeiras)', 'Mesa de jantar com 4 cadeiras', 'https://example.com/mesa-jantar', 0, NULL, NULL, NULL),
    ('Cortina de banho', 'Cortina de banho', 'https://example.com/cortina-banho', 0, NULL, NULL, NULL),
    ('Armário ou prateleiras para banheiro', 'Armário ou prateleiras para o banheiro', 'https://example.com/armario-banho', 0, NULL, NULL, NULL),
    ('Itens de higiene', 'Itens de higiene (cesta, tapetes, saboneteira, etc.)', 'https://example.com/itens-higiene', 0, NULL, NULL, NULL),
    ('Lâmpadas (qtde 6)', 'Lâmpadas (quantidade 6)', 'https://example.com/lampadas', 0, NULL, NULL, NULL),
    ('Almofadas (qtde 2)', 'Almofadas (quantidade 2)', 'https://example.com/almofadas', 0, NULL, NULL, NULL),
    ('Varal de roupas', 'Varal de roupas', 'https://example.com/varal', 0, NULL, NULL, NULL),
    ('Cestos para roupa suja', 'Cestos para roupa suja', 'https://example.com/cestos', 0, NULL, NULL, NULL),
    ('Aspirador de pó', 'Aspirador de pó', 'https://example.com/aspirador', 0, NULL, NULL, NULL),
    ('Produtos de limpeza básicos', 'Produtos de limpeza básicos (vassoura, rodo, balde, pano de chão, etc.)', 'https://example.com/produtos-limpeza', 0, NULL, NULL, NULL),
    ('Organizadores', 'Organizadores (gavetas, caixas para armazenar)', 'https://example.com/organizadores', 0, NULL, NULL, NULL),
    ('Lixeira (cozinha, banheiro e área externa)', 'Lixeira para cozinha, banheiro e área externa', 'https://example.com/lixeira', 0, NULL, NULL, NULL);
        ''')

        db.commit()  # Confirmar as inserções no banco de dados



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error_500.html', error=error), 500
    
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

# CREATE TABLE wishlist (id INTEGER PRIMARY KEY AUTOINCREMENT, label, desc, link, booked, changed);

@app.route('/presentes.html', methods=['GET', 'POST'])
def wishlist():
    name = request.form.get('name', '')
    checked = [int(key) for key in request.form.keys() if re.match(r'^\d+$', key)]  # Alterado aqui
    msg = None
    success = False

    # Conectando ao banco de dados
    with closing(sqlite3.connect('wishlist.sqlite3')) as db:
        cur = db.cursor()
        with db:
            if request.method == 'POST':
                if not name:
                    msg = u'Por favor, forneça seu nome'
                elif not checked:
                    msg = u'Por favor, marque pelo menos um presente'
                else:
                    # Obter os nomes dos presentes selecionados
                    cur.execute('SELECT id, label FROM wishlist WHERE id IN ({})'.format(','.join('?' for _ in checked)), checked)
                    reserved_items = cur.fetchall()
                    
                    # Obter os nomes dos presentes reservados
                    reserved_names = [item[1] for item in reserved_items]
                    
                    # Criar a mensagem com os nomes dos presentes reservados
                    msg = u'Você presenteou com sucesso o(s) presente(s) selecionado(s): ' + ', '.join(reserved_names) + '. Obrigado :)'
                    
                    # Atualizando o banco de dados
                    cur.executemany('''UPDATE wishlist SET 
                        booked = ?, 
                        reserver = ?, 
                        reservation_date = CURRENT_TIMESTAMP, 
                        changed = CURRENT_TIMESTAMP 
                        WHERE id = ? AND booked IS NULL''',
                        [(1, name, item) for item in checked])
                    
                    success = True

            # Obtendo os itens da lista de presentes
            items = cur.execute('SELECT id, label, booked, reserver, reservation_date FROM wishlist').fetchall()

    return render_template('presentes.html', wishlist=True, items=items,
                           name=name, checked=checked, msg=msg, success=success)


FIELDS = ('names', 'notes')
EVENTS = ('local', 'cerimonia', 'vacsora')

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    success = False
    if request.method == 'POST':
        rf = request.form
        invalid = not rf.get('names') or not any(event in rf for event in EVENTS)
        if not invalid:
            success = True
            save_rsvp()
    else:
        invalid = False
    return render_template('rsvp.html', invalid=invalid, success=success, fields=request.form)

# CREATE TABLE rsvp (names, local, cerimonia, vacsora, notes, added);
def save_rsvp():
    with closing(sqlite3.connect('rsvp.sqlite3')) as db:
        with db:
            keys = list(FIELDS) + list(EVENTS)
            db.execute('INSERT INTO rsvp ({fields}, added) VALUES ({qmarks}, CURRENT_TIMESTAMP)'.format(
                fields=','.join(keys), qmarks=','.join('?' * len(keys))),
                [request.form.get(key) for key in keys])

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='img/favicon.ico'))

if __name__ == '__main__':
    #init_db()
    #pop_db()
    app.run(debug=True, host='0.0.0.0')
