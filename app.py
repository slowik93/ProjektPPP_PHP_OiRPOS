from flask import Flask, render_template, request, jsonify, session
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'twoj_tajny_klucz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database
db = SQLAlchemy(app)

# Tabela User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  

    def __repr__(self):
        return f"User('{self.username}', '{self.password}')"

# Tabela Currency
class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"Currency('{self.name}')"

# Tabela ConversionHistory
class ConversionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency_from_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    currency_to_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    value_from = db.Column(db.Float, nullable=False)
    value_to = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)

    currency_from = db.relationship('Currency', foreign_keys=[currency_from_id], backref='conversion_history_from')
    currency_to = db.relationship('Currency', foreign_keys=[currency_to_id], backref='conversion_history_to')

    def __repr__(self):
        return f"ConversionHistory('{self.currency_from.name}', '{self.currency_to.name}', '{self.value_from}', '{self.value_to}')"

def populate_database():
    existing_users = User.query.all()
    if not existing_users:
        # Add initial data to the database
        user1 = User(username='1', password='1')
        user2 = User(username='user1', password='haslo1')
        user3 = User(username='user2', password='haslo2')
        user4 = User(username='user3', password='haslo3')
        user5 = User(username='admin', password='adminpassword')

        db.session.add_all([user1, user2, user3, user4, user5 ])
        db.session.commit()

    existing_currencys = Currency.query.all()
    if not existing_currencys:
        # Add initial data to the database
        currency1 = Currency(name='PLN')
        currency2 = Currency(name='USD')
        currency3 = Currency(name='EUR')
        currency4 = Currency(name='GBP')

        db.session.add_all([currency1, currency2, currency3, currency4 ])
        db.session.commit()

with app.app_context():
    db.create_all()
    populate_database()

    # wyświetlanie użytkowników w bazie danych
    users = User.query.all()
    for user in users:
        print(user.username, user.password)

            # wyświetlanie użytkowników w bazie danych
    historyC = ConversionHistory.query.all()
    for h in historyC:
        print(h.rate, h.user_id)



API_KEY = "YOUR_API_KEY"  # Ensure you have your own API key for the currency conversion service

# Simple in-memory 'database' for demonstration purposes
users = {
    "1": "1",
    "user1": "haslo1",
    "user2": "haslo2",
    "admin": "adminpassword"  # Normally, you'd store passwords securely
}

# History of conversions for each user
histories = {}

useFileDatabase = True

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if useFileDatabase == True:
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username  # Log the user in
            # histories[username] = [] 
            return jsonify({'message': 'Zalogowano pomyślnie (baza danych)', 'logged_in': True})
        else:
            return jsonify({'message': 'Nieprawidłowa nazwa użytkownika lub hasło (baza danych)', 'logged_in': False})

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

    if useFileDatabase == True:
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user:
            return jsonify({'message': 'Nazwa użytkownika jest już zajęta (baza danych)'})
        else:
            # histories[new_username] = [] 
            newUser = User(username=new_username, password=new_password)
            db.session.add(newUser)
            db.session.commit()
            return jsonify({'message': 'Użytkownik został zarejestrowany (baza danych)'})

    if new_username in users:
        return jsonify({'message': 'Nazwa użytkownika jest już zajęta'})
    else:
        users[new_username] = new_password  # Securely hash passwords in real applications
        histories[new_username] = []  # Initialize history for the new user
        return jsonify({'message': 'Użytkownik został zarejestrowany'})

@app.route('/history', methods=['GET'])
def history():
    if useFileDatabase:
        if 'username' in session:
            username = session['username']
            user = User.query.filter_by(username=username).first()

            if user:
                if user.id is not None:
                    conversion_history_query = ConversionHistory.query.filter_by(user_id=user.id).all()

                    conversion_history_list = { }
                    conversion_history_raw = { }

                    # zwracanie danych w orginalnym formacie
                    if conversion_history_query and False:
                        conversion_history_list = [
                            {
                                'value': f"{item.value_from} {item.currency_from.name} to {item.value_to} {item.currency_to.name} at rate {item.rate}"
                            }
                            for item in conversion_history_query
                        ]

                        return jsonify({'history': conversion_history_list})

                    if conversion_history_query:
                        conversion_history_raw = [
                            {
                                'currency_from': item.currency_from.name,
                                'currency_to': item.currency_to.name,
                                'value_from': round(item.value_from, 4),
                                'value_to': round(item.value_to, 4),
                                'rate': round(item.rate, 4)
                            }
                            for item in conversion_history_query
                        ]

                        return jsonify({'history': conversion_history_raw})

                    return jsonify({'error': 'Brak dostępu do historii'})

                return jsonify({'error': 'User ID is None'})

            return jsonify({'error': 'Brak dostępu do historii'})

        return jsonify({'error': 'Brak dostępu do historii'})

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
        # Add to history
        if useFileDatabase:
            user = User.query.filter_by(username=session['username']).first()

            if user:
                id_currency_from = Currency.query.filter_by(name=from_currency).first()
                id_currency_to = Currency.query.filter_by(name=to_currency).first()

                if id_currency_from and id_currency_to:
                    new_conversion = ConversionHistory(
                        user_id=user.id,
                        currency_from_id=id_currency_from.id,
                        currency_to_id=id_currency_to.id,
                        value_from=amount,
                        value_to=converted_amount,
                        rate=rate
                    )

                    db.session.add(new_conversion)
                    db.session.commit()

                    return jsonify({'converted_amount': converted_amount})

                return jsonify({'error': 'Nieprawidłowe waluty'})

            return jsonify({'error': 'Brak użytkownika'})

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

    return jsonify({'message': f'Subskrypcja dla {email} na walutę {currency} z progiem {threshold} została zarejestrowana'})

if __name__ == '__main__':
    app.run(debug=True)

