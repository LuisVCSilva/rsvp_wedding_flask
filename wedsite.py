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


def pop_db():
    with closing(sqlite3.connect('wishlist.sqlite3')) as db:
        cur = db.cursor()
        cur.execute('''
        INSERT INTO wishlist (label, desc, link, booked, reserver, reservation_date, changed) VALUES
        ('Smartphone', 'Um smartphone topo de linha', 'https://example.com/smartphone', 0, NULL, NULL, NULL),
        ('Notebook', 'Notebook ultrafino e leve', 'https://example.com/notebook', 1, 'João', '2025-01-06', NULL),
        ('Fones de ouvido', 'Fones de ouvido Bluetooth', 'https://example.com/fones', 0, NULL, NULL, NULL),
        ('Câmera fotográfica', 'Câmera DSLR profissional', 'https://example.com/camera', 0, NULL, NULL, NULL);
        ''')
        db.commit()  # Confirmar as inserções no banco de dados


# CREATE TABLE wishlist (id INTEGER PRIMARY KEY AUTOINCREMENT, label, desc, link, booked, changed);
@app.route('/presentes.html', methods=['GET', 'POST'])
def wishlist():
    name = request.form.get('name', '')
    checked = [int(key) for key in request.form.keys() if re.match(r'^\d+$', key)]  # Alterado aqui
    msg = None
    success = False
    with closing(sqlite3.connect('wishlist.sqlite3')) as db:
        cur = db.cursor()
        with db:
            if request.method == 'POST':
                if not name:
                    msg = u'Por favor, forneça seu nome'
                elif not checked:
                    msg = u'Por favor, marque pelo menos um presente'
                else:
                    msg = u'Você reservou com sucesso o(s) presente(s) selecionado(s), obrigado'.format(
                            '' if len(checked) == 1 else 'ka')
                    cur.executemany('''UPDATE wishlist SET 
                        booked = ?, 
                        reserver = ?, 
                        reservation_date = CURRENT_TIMESTAMP, 
                        changed = CURRENT_TIMESTAMP 
                        WHERE id = ? AND booked IS NULL''',
                        [(1, name, item) for item in checked])
                    success = True
            items = cur.execute('SELECT id, label, IFNULL(desc, ""), link, booked, reserver, reservation_date FROM wishlist').fetchall()

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
