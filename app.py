from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
import psycopg2

app = Flask(__name__)
Bootstrap(app)

def connect_db():
    return psycopg2.connect(
        dbname='qts_db',
        user='rafael',
        password='7rFqVx4mP2F9f0XAFKvvIbn0835Yz7xd',
        host='dpg-coofaqol5elc739o5gj0-a.oregon-postgres.render.com',
        port='5432'
    )

# Quicksort function
def quicksort(arr, key=lambda x: x):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if key(x) < key(pivot)]
    middle = [x for x in arr if key(x) == key(pivot)]
    right = [x for x in arr if key(x) > key(pivot)]
    return quicksort(left, key) + middle + quicksort(right, key)

#-----------------------------------------------------------------PROFESSORES------------------------------------------------------------------

@app.route('/')
def index():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM professores')
    professores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', professores=professores)

@app.route('/new_professor', methods=['GET', 'POST'])
def new_professor():
    if request.method == 'POST':
        nome = request.form['nome']
        disciplina = request.form['disciplina']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO professores (nome, disciplina) VALUES (%s, %s)', (nome, disciplina))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir o professor: {e}")
    return render_template('new.html')

#-----------------------------------------------------------------DISCIPLINAS------------------------------------------------------------------

@app.route('/disciplinas')
def index_disciplinas():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM disciplinas')
    disciplinas = cur.fetchall()
    cur.close()
    conn.close()

    # Ordenar os dados pela carga horária (terceira coluna, índice 2)
    disciplinas = quicksort(disciplinas, key=lambda x: x[2])

    return render_template('disciplinas/indexDisciplina.html', disciplinas=disciplinas)

@app.route('/new_disciplina', methods=['GET', 'POST'])
def new_disciplina():
    if request.method == 'POST':
        nome = request.form['nome']
        carga_horaria = request.form['carga_horaria']
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO disciplinas (nome, carga_horaria) VALUES (%s, %s)', (nome, carga_horaria))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_disciplinas'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir a disciplina: {e}")
    return render_template('disciplinas/newDisciplina.html')

@app.route('/delete_disciplina/<int:id>', methods=['POST'])
def delete_disciplina(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM disciplinas WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_disciplinas'))
    except Exception as e:
        print(f"Ocorreu um erro ao deletar o curso: {e}")
        return redirect(url_for('index_disciplinas'))

#-----------------------------------------------------------------CURSOS------------------------------------------------------------------

@app.route('/cursos')
def index_curso():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT cursos.id, cursos.nome, cursos.duracao, array_agg(disciplinas.nome)
        FROM cursos
        JOIN curso_disciplinas ON cursos.id = curso_disciplinas.curso_id
        JOIN disciplinas ON curso_disciplinas.disciplina_id = disciplinas.id
        GROUP BY cursos.id, cursos.nome, cursos.duracao
    ''')
    cursos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('cursos/indexCurso.html', cursos=cursos)

@app.route('/new_curso', methods=['GET', 'POST'])
def new_curso():
    if request.method == 'POST':
        nome = request.form['nome']
        duracao = request.form['duracao']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO cursos (nome, duracao) VALUES (%s, %s) RETURNING id', (nome, duracao))
            curso_id = cur.fetchone()[0]
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO curso_disciplinas (curso_id, disciplina_id) VALUES (%s, %s)', (curso_id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_curso'))
        except Exception as e:
            print(f"Ocorreu um erro ao inserir o curso: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('cursos/newCurso.html', disciplinas=disciplinas)



@app.route('/delete_curso/<int:id>', methods=['POST'])
def delete_curso(id):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM curso_disciplinas WHERE curso_id = %s', (id,))
        cur.execute('DELETE FROM cursos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index_curso'))
    except Exception as e:
        print(f"Ocorreu um erro ao deletar o curso: {e}")
        return redirect(url_for('index_curso'))

@app.route('/edit_curso/<int:id>', methods=['GET', 'POST'])
def edit_curso(id):
    if request.method == 'POST':
        nome = request.form['nome']
        duracao = request.form['duracao']
        disciplinas = request.form.getlist('disciplinas[]')
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute('UPDATE cursos SET nome = %s, duracao = %s WHERE id = %s', (nome, duracao, id))
            cur.execute('DELETE FROM curso_disciplinas WHERE curso_id = %s', (id,))
            for disciplina_id in disciplinas:
                cur.execute('INSERT INTO curso_disciplinas (curso_id, disciplina_id) VALUES (%s, %s)', (id, disciplina_id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index_curso'))
        except Exception as e:
            print(f"Ocorreu um erro ao editar o curso: {e}")
    else:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('SELECT id, nome, duracao FROM cursos WHERE id = %s', (id,))
        curso = cur.fetchone()
        cur.execute('SELECT id, nome FROM disciplinas')
        disciplinas = cur.fetchall()
        cur.execute('SELECT disciplina_id FROM curso_disciplinas WHERE curso_id = %s', (id,))
        curso_disciplinas = cur.fetchall()
        curso_disciplinas_ids = [disciplina[0] for disciplina in curso_disciplinas]
        cur.close()
        conn.close()
        return render_template('cursos/editCurso.html', curso=curso, disciplinas=disciplinas, curso_disciplinas_ids=curso_disciplinas_ids)


if __name__ == '__main__':
    app.run(debug=True)
