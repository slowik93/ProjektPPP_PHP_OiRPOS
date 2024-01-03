from flask import Flask, render_template, request, jsonify, session
import requests

app = Flask(__name__)
app.secret_key = 'twoj_tajny_klucz'

API_KEY = "YOUR_API_KEY"

users = {
    "user1": "haslo1",
    "user2": "haslo2",
    "admin": "adminpassword"
}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username in users and users[username] == password:
        session['username'] = username
        return jsonify({'message': 'Zalogowano pomyślnie', 'logged_in': True})
    else:
        return jsonify({'message': 'Nieprawidłowa nazwa użytkownika lub hasło', 'logged_in': False})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Wylogowano pomyślnie'})

@app.route('/users', methods=['GET'])
def get_users():
    if 'username' in session and session['username'] == 'admin':
        return jsonify({'users': users})
    return jsonify({'error': 'Brak dostępu'})

@app.route('/convert', methods=['GET'])
def convert():
    if 'username' not in session:
        return jsonify({'error': 'Nie jesteś zalogowany'})

    amount = request.args.get('amount', type=float)
    from_currency = request.args.get('from_currency')
    to_currency = request.args.get('to_currency')

    response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}",
                            params={"apikey": API_KEY})
    if response.status_code != 200:
        return jsonify({'error': 'Błąd pobierania kursu walut'})

    rates = response.json().get('rates', {})
    rate = rates.get(to_currency)

    if rate:
        converted_amount = rate * amount
        return jsonify({'converted_amount': converted_amount})

    return jsonify({'error': 'Błąd konwersji'})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'username' not in session:
        return jsonify({'error': 'Nie jesteś zalogowany'})

    email = request.form.get('email')
    currency = request.form.get('currency')
    threshold = request.form.get('threshold', type=float)

    # Tutaj można dodać logikę zapisywania subskrypcji
    return jsonify({'message': f'Subskrypcja dla {email} na walutę {currency} z progiem {threshold} została zarejestrowana'})

if __name__ == '__main__':
    app.run(debug=True)
