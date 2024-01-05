from flask import Flask, render_template, request, jsonify, session
import requests

app = Flask(__name__)
app.secret_key = 'twoj_tajny_klucz'

API_KEY = "YOUR_API_KEY"  # Ensure you have your own API key for the currency conversion service

# Simple in-memory 'database' for demonstration purposes
users = {
    "user1": "haslo1",
    "user2": "haslo2",
    "admin": "adminpassword"  # Normally, you'd store passwords securely
}

# History of conversions for each user
histories = {}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username in users and users[username] == password:
        session['username'] = username  # Log the user in
        # Initialize user's history if not present
        if username not in histories:
            histories[username] = []
        return jsonify({'message': 'Zalogowano pomyślnie', 'logged_in': True})
    else:
        return jsonify({'message': 'Nieprawidłowa nazwa użytkownika lub hasło', 'logged_in': False})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Log the user out
    return jsonify({'message': 'Wylogowano pomyślnie'})

@app.route('/register', methods=['POST'])
def register():
    new_username = request.form.get('username')
    new_password = request.form.get('password')

    if new_username in users:
        return jsonify({'message': 'Nazwa użytkownika jest już zajęta'})
    else:
        users[new_username] = new_password  # Securely hash passwords in real applications
        histories[new_username] = []  # Initialize history for the new user
        return jsonify({'message': 'Użytkownik został zarejestrowany'})

@app.route('/history', methods=['GET'])
def history():
    if 'username' in session:
        username = session['username']
        return jsonify({'history': histories.get(username, [])})
    return jsonify({'error': 'Brak dostępu do historii'})

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
        # Add to history
        history_entry = f"{amount} {from_currency} to {converted_amount} {to_currency} at rate {rate}"
        histories[session['username']].append(history_entry)

        return jsonify({'converted_amount': converted_amount})

    return jsonify({'error': 'Nie można przeliczyć waluty'})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'username' not in session:
        return jsonify({'error': 'Nie jesteś zalogowany'})

    email = request.form.get('email')
    currency = request.form.get('currency')
    threshold = request.form.get('threshold', type=float)

    # Add subscription logic or storage here

    return jsonify({'message': f'Subskrypcja dla {email} na walutę {currency} z progiem {threshold} została zarejestrowana'})

if __name__ == '__main__':
    app.run(debug=True)
