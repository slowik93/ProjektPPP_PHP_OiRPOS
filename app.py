from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'twoj_tajny_klucz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database
db = SQLAlchemy(app)

api_key = 'KSAVRUPOUXAA64X8'
symbol = 'PLNUSD'
endpoint = 'https://www.alphavantage.co/query'
function = 'FX_DAILY'

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

class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    base_currency = db.Column(db.String(3))
    target_currency = db.Column(db.String(3))
    open_price = db.Column(db.Float)
    high_price = db.Column(db.Float)
    low_price = db.Column(db.Float)
    close_price = db.Column(db.Float)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency = db.Column(db.String(50), nullable=False)
    threshold = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))

    def __repr__(self):
        return f"Subscription('{self.user.username}', '{self.currency}', '{self.threshold}')"

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

    exchange_rates = ExchangeRate.query.all()
    if not exchange_rates:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=29)
        current_date = start_date

        formatted_date = current_date.strftime('%Y-%m-%d')

        params = {
            'function': function,
            'from_symbol': symbol[:3],
            'to_symbol': symbol[3:],
            'apikey': api_key,
            'date': formatted_date,
        }

        response = requests.get(endpoint, params=params)
        data = response.json()

        if 'Time Series FX (Daily)' in data:
            for date, values in data['Time Series FX (Daily)'].items():
                exchange_rate = ExchangeRate(
                    date=date,
                    base_currency=symbol[:3],
                    target_currency=symbol[3:],
                    open_price=float(values['1. open']),
                    high_price=float(values['2. high']),
                    low_price=float(values['3. low']),
                    close_price=float(values['4. close'])
                )
                db.session.add(exchange_rate)
                db.session.commit()


def fetch_exchange_rate_data(date):
    params = {
        'function': function,
        'from_symbol': symbol[:3],
        'to_symbol': symbol[3:],
        'apikey': api_key,
        'date': date,
    }
    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        # If the request was not successful, print an error message
        print(f"Error fetching data from API. Status code: {response.status_code}")
        return None


def get_previous_date_data():
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    record = ExchangeRate.query.filter_by(date=yesterday_date).first()

    if not record:
        # If no record is found, fetch data from the API and save it to the database
        api_data = fetch_exchange_rate_data(yesterday_date)
        if 'Time Series FX (Daily)' in api_data:
            latest_data = api_data['Time Series FX (Daily)'][yesterday_date]
            new_record = ExchangeRate(
                date=yesterday_date,
                base_currency=symbol[:3],
                target_currency=symbol[3:],
                open_price=float(latest_data['1. open']),
                high_price=float(latest_data['2. high']),
                low_price=float(latest_data['3. low']),
                close_price=float(latest_data['4. close'])
            )
            db.session.add(new_record)
            db.session.commit()

            record = new_record

    data_for_response = {
        'date': record.date,
        'base_currency': record.base_currency,
        'target_currency': record.target_currency,
        'open_price': record.open_price,
        'high_price': record.high_price,
        'low_price': record.low_price,
        'close_price': record.close_price
    } if record else None

    return jsonify({'previous_date_data': data_for_response})



with app.app_context():
    db.create_all()
    populate_database()

    # wyświetlanie użytkowników w bazie danych
    # users = User.query.all()
    # for user in users:
    #     print(user.username, user.password)

    #         # wyświetlanie użytkowników w bazie danych
    # historyC = ConversionHistory.query.all()
    # for h in historyC:
    #     print(h.rate, h.user_id)

    # all_exchange_rates = ExchangeRate.query.all()
    # for rate in all_exchange_rates:
    #     print(f"Date: {rate.date}, Base Currency: {rate.base_currency}, Target Currency: {rate.target_currency}, "
    #           f"Open Price: {rate.open_price}, High Price: {rate.high_price}, Low Price: {rate.low_price}, "
    #           f"Close Price: {rate.close_price}")



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

@app.route('/display_exchange_data_for_30_days', methods=['GET'])
def display_exchange_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=29)

    exchange_data = ExchangeRate.query.filter(
        ExchangeRate.date >= start_date.strftime('%Y-%m-%d'),
        ExchangeRate.date <= end_date.strftime('%Y-%m-%d')
    ).all()

    data_for_render = []
    for entry in exchange_data:
        data_for_render.append({
            'date': entry.date,
            'base_currency': entry.base_currency,
            'target_currency': entry.target_currency,
            'open_price': entry.open_price,
            'high_price': entry.high_price,
            'low_price': entry.low_price,
            'close_price': entry.close_price,
        })

    return jsonify({'exchange_data': data_for_render})

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

# @app.route('/subscribe', methods=['POST'])
# def subscribe():
#     if 'username' not in session:
#         return jsonify({'error': 'Musisz być zalogowany, aby subskrybować powiadomienia'}), 401

#     username = session['username']
#     user = User.query.filter_by(username=username).first()
#     if user is None:
#         return jsonify({'error': 'Nie znaleziono użytkownika'}), 404

#     # Pobierz walutę i próg z formularza, nie pobieraj emaila
#     currency = request.form.get('currency')
#     threshold = float(request.form.get('threshold', 0))

#     new_subscription = Subscription(user_id=user.id, currency=currency, threshold=threshold)
#     db.session.add(new_subscription)
#     db.session.commit()

#     return jsonify({'message': f'Subskrypcja na walutę {currency} z progiem {threshold} została zarejestrowana'})
@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'username' not in session:
        return jsonify({'error': 'Musisz być zalogowany, aby subskrybować powiadomienia'}), 401

    username = session['username']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({'error': 'Nie znaleziono użytkownika'}), 404

    currency = request.form.get('currency')
    threshold = float(request.form.get('threshold', 0))

    new_subscription = Subscription(user_id=user.id, currency=currency, threshold=threshold)
    db.session.add(new_subscription)
    db.session.commit()

    return jsonify({'message': f'Subskrypcja na walutę {currency} z progiem {threshold} została zarejestrowana'})

@app.route('/subscriptions', methods=['GET'])
def subscriptions():
    if 'username' not in session or session['username'] != 'admin':
        return jsonify({'error': 'Brak uprawnień'}), 403

    all_subscriptions = Subscription.query.join(User).add_columns(
        Subscription.id, User.username, Subscription.currency, Subscription.threshold
    ).all()

    subscriptions_list = [
        {
            'id': sub.id, 
            'username': sub.username, 
            'currency': sub.currency, 
            'threshold': sub.threshold
        } for sub in all_subscriptions
    ]

    return jsonify(subscriptions_list)

@app.route('/delete_subscription/<int:subscription_id>', methods=['POST'])
def delete_subscription(subscription_id):
    if 'username' not in session or session['username'] != 'admin':
        return jsonify({'error': 'Brak uprawnień'}), 403

    subscription = Subscription.query.get_or_404(subscription_id)
    db.session.delete(subscription)
    db.session.commit()

    return jsonify({'message': 'Subskrypcja została usunięta'})


if __name__ == '__main__':
    app.run(debug=True)

