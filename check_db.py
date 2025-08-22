import sqlite3

conn = sqlite3.connect('netplay.db')
cursor = conn.cursor()

# Verificar tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tabelas disponíveis:')
for table in tables:
    print(f'- {table[0]}')

# Se existir tabela de clientes, mostrar alguns registros
if any('client' in table[0].lower() for table in tables):
    for table in tables:
        if 'client' in table[0].lower():
            print(f'\nRegistros da tabela {table[0]}:')
            cursor.execute(f'SELECT * FROM {table[0]} LIMIT 3')
            rows = cursor.fetchall()
            for row in rows:
                print(row)

conn.close()