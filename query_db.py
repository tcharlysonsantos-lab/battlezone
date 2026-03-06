import sqlite3

db = sqlite3.connect('instance/database.db')
cursor = db.cursor()

# Contar partidas
cursor.execute('SELECT COUNT(*) FROM partidas')
total_partidas = cursor.fetchone()[0]
print(f'Total de Partidas: {total_partidas}')

#Contar operadores
cursor.execute('SELECT COUNT(*) FROM operadores')
total_operadores = cursor.fetchone()[0]
print(f'Total de Operadores: {total_operadores}')

# Listar Keno e Tete
cursor.execute('SELECT id, nome FROM operadores WHERE nome IN ("Keno", "Tete")')
operadores = cursor.fetchall()
print(f'Operadores encontrados: {operadores}')

if total_partidas > 0:
    print(f'\nPrimeiras 3 partidas:')
    cursor.execute('SELECT id, nome, campo, plano FROM partidas LIMIT 3')
    for row in cursor.fetchall():
        print(f'  #{row[1]}: {row[2]} - {row[3]}')
    
    print(f'\nUltimas 3 partidas:')
    cursor.execute('SELECT id, nome, campo, plano FROM partidas ORDER BY id DESC LIMIT 3')
    for row in reversed(cursor.fetchall()):
        print(f'  #{row[1]}: {row[2]} - {row[3]}')

db.close()
