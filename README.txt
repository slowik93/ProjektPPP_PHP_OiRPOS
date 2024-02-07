Dokumentacja Projektu Aplikacji Konwersji Walutowej

Wprowadzenie
Niniejsza dokumentacja dotyczy aplikacji Flask służącej do konwersji walut oraz subskrypcji powiadomień o zmianach kursów walutowych.

Wymagania
Python 3.6 lub nowszy
Flask
Flask-SQLAlchemy
Requests

Instalacja i uruchomienie (dla deweloperów)
1. Sklonuj repozytorium projektu.
2. Utwórz wirtualne środowisko dla projektu przy użyciu python -m venv venv.
3. Aktywuj środowisko wirtualne:
a) Na Windows: venv\Scripts\activate
b) Na macOS/Linux: source venv/bin/activate
4. Zainstaluj zależności przy użyciu pip install -r requirements.txt.
5. Uruchom aplikację przy pomocy flask run.

Konfiguracja
Przed uruchomieniem aplikacji należy się upewnić, że skonfigurowałeś klucz API dla zewnętrznego serwisu kursów walut oraz ustawiłeś sekretny klucz aplikacji Flask w pliku app.py.

Użycie (dla użytkowników)
Rejestracja i logowanie: Użytkownicy muszą się zarejestrować i zalogować, aby korzystać z aplikacji.
Konwersja walut: Po zalogowaniu użytkownik może przeliczać kwoty między różnymi walutami.
Historia konwersji: Użytkownicy mogą przeglądać historię swoich konwersji.
Subskrypcja powiadomień: Użytkownicy mogą subskrybować powiadomienia o zmianach kursów interesujących ich walut.

API
/convert: Endpoint do konwersji walut.
/history: Endpoint do przeglądania historii konwersji.
/subscribe: Endpoint do subskrypcji powiadomień o zmianach kursu walut.
/subscriptions: Endpoint do przeglądania subskrypcji (dostępny tylko dla admina).
/fetch_exchange_rates: Endpoint do pobierania aktualnych kursów walut.

Bezpieczeństwo
Aplikacja wykorzystuje mechanizmy sesji Flask do zarządzania logowaniem użytkowników oraz zabezpiecza hasła przy pomocy hashowania przed zapisaniem do bazy danych.

