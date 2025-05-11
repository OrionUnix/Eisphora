 # Eisphora
** Eisphora is an open-source web application to simplify tax management, initially for French taxation, with plans to expand to the US, Luxembourg, and more. It features a multilingual interface, a powerful LLM for tax law interpretation, and secure data handling.
Features **

* Tax calculations (FIFO, income tax, etc.)
* Transaction management and analytics
* Multilingual support (French, English, Spanish)
* Secure data encryption (AES-256)
* Responsive UI with React/Next.js and Tailwind CSS

## Installation

```
Clone the repository:git clone https://github.com/OrionUnix/Eisphora.git
cd Eisphora
```

Install backend dependencies:
```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install frontend dependencies:
```
cd ../frontend
npm install
```

Set up environment variables:
```
cp .env.example .env
```

Run migrations:
```
cd ../backend
python manage.py migrate
```

Build frontend:
```
./build_frontend.sh
```

Start the server:
```
python manage.py runserver
```


## Contributing
See CONTRIBUTING.md for details.

## License
ThisReported issues: project is licensed under the BSD-3-Clause License - see LICENSE for details.
