from flask import Flask, flash, render_template, request, redirect, url_for, session, make_response
from authlib.integrations.flask_client import OAuth
import os
import sqlite3
import csv
import io
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'password1234'

# === Configuración OAuth con Google ===
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='7771642900-nmtncn8orno37csloo3ftk30s9gul1v2.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={'scope': 'email profile'}
)

# === Base de datos SQLite ===
def conectar_db():
    conn = sqlite3.connect('mi_base.db')
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            rol TEXT,
            clave TEXT
        )
    ''')
    conn.commit()
    conn.close()

crear_tablas()

# === Datos simulados ===
proyectos = [
    {'id': 1, 'nombre': 'Gestor de Tareas', 'autor': 'Juan Perez', 'precio': 30,
     'valoracion': 4, 'categoria': 'Software', 'colaboraciones': 12,
     'descripcion': 'Una aplicación web para tareas diarias.', 'imagen': 'img/tareas.png'},
    {'id': 2, 'nombre': 'Pack de Ilustraciones de Fantasía', 'autor': 'Juan Perez', 'precio': 25,
     'valoracion': 3, 'categoria': 'Ilustracion', 'colaboraciones': 8,
     'descripcion': 'Más de 20 ilustraciones estilo fantasía.', 'imagen': 'img/ilustraciones.png'},
    {'id': 3, 'nombre': 'Curso de Emprendimiento', 'autor': 'Ana Lopez', 'precio': 40,
     'valoracion': 5, 'categoria': 'Negocios', 'colaboraciones': 5,
     'descripcion': 'Aprende cómo lanzar tu primer negocio.', 'imagen': 'img/emprendimiento.png'},
    {'id': 4, 'nombre': 'Plantillas para Instagram', 'autor': 'Luis Ramos', 'precio': 35,
     'valoracion': 2, 'categoria': 'Diseno', 'colaboraciones': 3,
     'descripcion': '30 plantillas editables para Instagram.', 'imagen': 'img/plantillas.png'},
]

comentarios_por_proyecto = {
    1: [{'usuario': 'Camila', 'texto': '¡Me encantó!', 'valoracion': 5}],
    2: [{'usuario': 'Sofía', 'texto': 'Muy útiles.', 'valoracion': 4}],
    3: [{'usuario': 'Elena', 'texto': 'Súper claro.', 'valoracion': 5}],
    4: [{'usuario': 'Mario', 'texto': 'Repetitivo.', 'valoracion': 2}]
}

# === Pedidos simulados por usuario ===
pedidos_mock_por_usuario = {}

# === Rutas ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

@app.route('/login')
def login():
    rol = request.args.get('rol')
    if rol:
        session['rol_temp'] = rol
    redirect_uri = url_for('auth_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get('userinfo').json()

    correo = user_info['email']
    nombre = user_info.get('name', 'Usuario')
    rol = session.pop('rol_temp', None)

    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,))
    usuario = cur.fetchone()

    if not usuario:
        cur.execute("INSERT INTO usuarios (nombre, correo, rol, clave) VALUES (?, ?, ?, ?)",
                    (nombre, correo, rol or 'comprador', ''))
        conn.commit()
        cur.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,))
        usuario = cur.fetchone()

    session['usuario_id'] = usuario['id']
    session['usuario_nombre'] = usuario['nombre']
    session['usuario_rol'] = usuario['rol']
    conn.close()

    if session['usuario_rol'] == 'profesor':
        return redirect(url_for('panel_profesor'))
    elif session['usuario_rol'] == 'estudiante':
        return redirect(url_for('panel_estudiante'))
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/panel/profesor')
def panel_profesor():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('panel_profesor.html', nombre=session['usuario_nombre'])

@app.route('/panel/estudiante')
def panel_estudiante():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('panel_estudiante.html', nombre=session['usuario_nombre'])

@app.route('/explorar')
def explorar():
    categoria = request.args.get('categoria')
    orden = request.args.get('orden')
    filtrados = proyectos

    if categoria:
        filtrados = [p for p in filtrados if p['categoria'] == categoria]

    if orden == 'precio':
        filtrados = sorted(filtrados, key=lambda p: p['precio'])
    elif orden == 'valoracion':
        filtrados = sorted(filtrados, key=lambda p: p['valoracion'], reverse=True)

    return render_template('explorar.html', proyectos=filtrados, categoria=categoria, orden=orden)

@app.route('/proyecto/<int:id>')
def detalle_proyecto(id):
    proyecto = next((p for p in proyectos if p['id'] == id), None)
    if not proyecto:
        return "Proyecto no encontrado", 404

    otros_proyectos = [p for p in proyectos if p['autor'] == proyecto['autor'] and p['id'] != id]
    comentarios = comentarios_por_proyecto.get(id, [])
    return render_template('detalle_proyecto.html', proyecto=proyecto, otros_proyectos_autor=otros_proyectos, comentarios=comentarios)

@app.route('/agregar_carrito/<int:id>')
def agregar_carrito(id):
    producto = next((p for p in proyectos if p['id'] == id), None)
    if not producto:
        return redirect(url_for('explorar'))

    if 'carrito' not in session:
        session['carrito'] = []
    session['carrito'].append(producto)
    session.modified = True

    return redirect(url_for('carrito'))

@app.route('/eliminar_carrito/<int:id>')
def eliminar_carrito(id):
    if 'carrito' in session:
        session['carrito'] = [p for p in session['carrito'] if p['id'] != id]
        session.modified = True
    return redirect(url_for('carrito'))

@app.route('/carrito')
def carrito():
    productos = session.get('carrito', [])
    total = sum(p['precio'] for p in productos)
    return render_template('carrito.html', productos=productos, total=total)

@app.route('/pago', methods=['GET'])
def pago():
    productos = session.get('carrito', [])
    if not productos:
        return redirect(url_for('carrito'))
    return render_template('pago.html')
@app.route('/procesar_pago', methods=['POST'])
def procesar_pago():
    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    tarjeta = request.form.get('tarjeta')
    cvv = request.form.get('cvv')
    fecha = request.form.get('fecha')

    if not (nombre and correo and tarjeta and cvv and fecha):
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('pago'))

    productos = session.get('carrito', [])
    usuario = session.get('usuario_id') or session.get('usuario_nombre') or 'anonimo'

    if usuario not in pedidos_mock_por_usuario:
        pedidos_mock_por_usuario[usuario] = []

    for producto in productos:
        nuevo_pedido = {
            "id": random.randint(100, 999),
            "titulo": producto['nombre'],
            "fecha": datetime.now().strftime("%d %b, %Y"),
            "estado": "pendiente",
            "total": producto['precio']
        }
        pedidos_mock_por_usuario[usuario].append(nuevo_pedido)

    session.pop('carrito', None)
    return render_template('confirmacion.html', nombre=nombre, correo=correo)


@app.route('/pedidos')
def pedidos():
    usuario = session.get('usuario_id') or session.get('usuario_nombre') or 'anonimo'
    pedidos_usuario = pedidos_mock_por_usuario.get(usuario, [])
    return render_template('pedidos.html', pedidos=pedidos_usuario)

@app.route('/pedido/<int:pedido_id>')
def detalle_pedido(pedido_id):
    usuario = session.get('usuario_id') or session.get('usuario_nombre') or 'anonimo'
    pedidos_usuario = pedidos_mock_por_usuario.get(usuario, [])
    pedido = next((p for p in pedidos_usuario if p['id'] == pedido_id), None)
    if not pedido:
        return "Pedido no encontrado", 404
    return render_template('detalle_pedido.html', pedido=pedido)

@app.route('/descargar_pedidos')
def descargar_pedidos():
    usuario = session.get('usuario_id') or session.get('usuario_nombre') or 'anonimo'
    pedidos = pedidos_mock_por_usuario.get(usuario, [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Título', 'Fecha', 'Estado', 'Total'])
    for pedido in pedidos:
        writer.writerow([pedido['id'], pedido['titulo'], pedido['fecha'], pedido['estado'], pedido['total']])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=historial_pedidos.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

# === Ejecutar App ===
if __name__ == '__main__':
    app.run(debug=True)











