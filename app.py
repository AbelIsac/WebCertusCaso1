from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

@app.route('/explorar')
def explorar():
    return render_template('explorar.html')

if __name__ == '__main__':
    app.run(debug=True)
