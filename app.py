from flask import Flask, flash, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = 'password1234'  # ✅ Usa una fija y segura


# Configuración de OAuth con Google
oauth = OAuth(app)


google = oauth.register(
    name='google',
    client_id='7771642900-nmtncn8orno37csloo3ftk30s9gul1v2.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={
        'scope': 'email profile'
    }

)

# Función de conexión a la base de datos
def conectar_db():
    conn = psycopg2.connect(
        host="localhost",
        database="creali_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD")  # ✅ bien escrito aquí
    )
    return conn



proyectos = [
    {
        'id': 1,
        'nombre': 'Gestor de Tareas',
        'autor': 'Juan Perez',
        'precio': 30,
        'valoracion': 4,
        'categoria': 'Software',
        'colaboraciones': 12,
        'descripcion': 'Una aplicación web minimalista para gestionar tus tareas diarias. Puedes crear, editar, organizar y priorizar actividades. Ideal para freelancers o equipos pequeños.',
        'imagen': 'img/tareas.png'
    },
    {
        'id': 2,
        'nombre': 'Pack de Ilustraciones de Fantasía',
        'autor': 'Juan Perez',
        'precio': 25,
        'valoracion': 3,
        'categoria': 'Ilustracion',
        'colaboraciones': 8,
        'descripcion': 'Incluye más de 20 ilustraciones digitales de estilo fantasía medieval: criaturas, mapas y personajes. Listas para usar en juegos de rol, novelas o cómics.',
        'imagen': 'img/ilustraciones.png'
    },
    {
        'id': 3,
        'nombre': 'Curso de Emprendimiento desde Cero',
        'autor': 'Ana Lopez',
        'precio': 40,
        'valoracion': 5,
        'categoria': 'Negocios',
        'colaboraciones': 5,
        'descripcion': 'Aprende paso a paso cómo validar ideas, construir una propuesta de valor y lanzar tu primer negocio usando herramientas reales del mercado.',
        'imagen': 'img/emprendimiento.png'
    },
    {
        'id': 4,
        'nombre': 'Plantillas para Instagram',
        'autor': 'Luis Ramos',
        'precio': 35,
        'valoracion': 2,
        'categoria': 'Diseno',
        'colaboraciones': 3,
        'descripcion': 'Colección de 30 plantillas editables en Canva y Photoshop para crear contenido impactante en Instagram. Estilo moderno y adaptable a cualquier marca.',
        'imagen': 'img/plantillas.png'
    },
]


comentarios_por_proyecto = {
    1: [
        {'usuario': 'Camila', 'texto': 'El diseño es hermoso y fácil de personalizar. ¡Me encantó!', 'valoracion': 5},
        {'usuario': 'Eduardo', 'texto': 'Muy bien explicado, ideal para quienes están comenzando.', 'valoracion': 4},
        {'usuario': 'Jorge', 'texto': 'Buen contenido, pero faltan instrucciones claras en algunas partes.', 'valoracion': 3},
    ],
    2: [
        {'usuario': 'Sofía', 'texto': 'Las ilustraciones están muy bien hechas. Usé varias en mi juego.', 'valoracion': 4},
    ],
    3: [
        {'usuario': 'Elena', 'texto': 'Me ayudó a lanzar mi negocio. Súper claro y práctico.', 'valoracion': 5},
        {'usuario': 'Andrés', 'texto': 'Muy completo, pero esperaba más ejemplos en video.', 'valoracion': 4}
    ],
    4: [
        {'usuario': 'Mario', 'texto': 'Bonito diseño pero muy repetitivo.', 'valoracion': 2}
    ]
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

from flask import redirect, url_for, session

@app.route('/login')
def login():
    rol = request.args.get('rol')
    if rol:
        session['rol_temp'] = rol  # ✅ se guarda antes del redireccionamiento

    redirect_uri = url_for('auth_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def auth_google_callback():
    token = oauth.google.authorize_access_token()

    # ❌ NO uses parse_id_token
    # user_info = oauth.google.parse_id_token(token) ← esto da error

    # ✅ Mejor usa la API de Google para obtener la información del usuario
    user_info = oauth.google.get('userinfo').json()

    correo = user_info['email']
    nombre = user_info.get('name', 'Usuario')
    rol = session.pop('rol_temp', None)

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
    usuario = cur.fetchone()

    if not usuario:
        cur.execute("""
            INSERT INTO usuarios (nombre, correo, rol, clave)
            VALUES (%s, %s, %s, %s)
        """, (nombre, correo, rol or 'comprador', ''))
        conn.commit()
        cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cur.fetchone()

    session['usuario_id'] = usuario[0]
    session['usuario_nombre'] = usuario[1]
    session['usuario_rol'] = usuario[3]

    conn.close()

    # Redirección según el rol
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

    return render_template(
        'detalle_proyecto.html',
        proyecto=proyecto,
        otros_proyectos_autor=otros_proyectos,
        comentarios=comentarios
    )

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

    # Validaciones simples (puedes extender esto)
    if not (nombre and correo and tarjeta and cvv and fecha):
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for('pago'))

    # Limpiar carrito
    session.pop('carrito', None)

    return render_template('confirmacion.html', nombre=nombre, correo=correo)



if __name__ == '__main__':
    app.run(debug=True)






