# Eisphora

**Eisphora** is an open-source web application designed to simplify tax management. Initially focused on French taxation, it has plans to expand to the US, Luxembourg, and other countries. It features a multilingual interface, leverages a powerful LLM for tax law interpretation, and ensures secure data handling.

## Features

* Tax calculations (FIFO, income tax, etc.)
* Transaction management and analytics
* Multilingual support (French, English, Spanish)
* Secure data encryption (AES-256)
* Responsive UI with React/Next.js and Tailwind CSS

## Installation

Follow these steps to install and configure the project locally:

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/OrionUnix/Eisphora.git](https://github.com/OrionUnix/Eisphora.git)
    cd Eisphora
    ```

2.  **Configure Environment Variables:**

    * **For the Backend (at the project root):**
        Copy the example file `.env.example` (if it exists at the root) or create a `.env` file at the root of the project. You **must** then edit this `.env` file and fill in the appropriate values for your database, secret keys, etc.
        ```bash
        # Make sure you are at the root of the Eisphora project
        cp .env.example .env  # If a .env.example exists at the root
        # Or create it manually if needed
        ```
        **Important:** Open the created `.env` file and replace the default or placeholder values with your actual configuration information.

    * **For the Frontend (in `frontend/.env.local`):**
        Create a file named `.env.local` inside the `frontend/` directory. This file will contain the environment variables needed for the Next.js frontend to function correctly.
        ```bash
        # Make sure you are at the root of the Eisphora project
        touch frontend/.env.local
        ```
        **Important:** Open the `frontend/.env.local` file and add the necessary variables. For example, to set the base URL of your backend API:
        ```dotenv
        NEXT_PUBLIC_BASE_URL=http://localhost:8000  # Replace with your backend URL if different
        ```
        Ensure you configure all variables required by the frontend.

3.  **Install Backend Dependencies:**

    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

4.  **Install Frontend Dependencies:**

    ```bash
    cd ../frontend
    npm install
    ```

5.  **Run Database Migrations:**

    ```bash
    cd ../backend
    python manage.py migrate
    ```

6.  **Build Frontend:**

    ```bash
    # Make sure you are at the root of the Eisphora project
    ./build_frontend.sh
    # Note: This script depends on its presence and content.
    # Alternatively, you might need commands like `cd frontend && npm run build`
    ```

7.  **Start the Backend Server:**

    ```bash
    cd backend
    python manage.py runserver
    ```

Your application should now be accessible (usually at `http://localhost:8000`).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to the project.

## License

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details.