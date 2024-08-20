# 42LiliCal

## Description
42LiliCal is a small iCal api translater server designed for the 42  Piscine (tool developed by a piscineux). It get peer evaluation event from 42 api and add it to a Calendar via CalDav protocol.

## Features
- Event Getting from 42 API.
    - Peer evaluate or evaluator get from api and it location if connected.
- Synchronization with third-party calendar applications.

## Prerequisites
- Python 3.x
- Flask
- A CalDav compatible Server (if using with the docker compose in the repo a Radicale server is set)

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/42LiliCal.git
    cd 42LiliCal
    ```
2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Start the server:
    ```bash
    flask run
    ```
2. Access the application via your browser at `http://127.0.0.1:5000`.
4. An initial login is required to initialize the application. Then periodically to refresh the API authorization.
5. To manually update the calendar, go to the address `/update/`.

## Usage with Docker Compose
1. Make sure you have Docker and Docker Compose installed on your machine.
2. Create a `.env` file at the root of the project with the following variables:
    ```env
    UID=""
    SECRET=""
    TOKEN=""
    ADDRESS=""
    DAVICAL_USER=""
    DAVICAL_PASS=""
    LOGIN=""
    ```
3. Start the services with Docker Compose:
    ```bash
    docker-compose up
    ```
4. Access the application via your browser at `http://127.0.0.1:5000`.

## .env File
A `.env` file is required to configure the application's environment variables. Here are the variables to include:
- `UID`: Your UID provided on the intra (API 42).
- `SECRET`: Your key provided on the intra (API 42).
- `TOKEN`: (retrieved when starting the server with an API request for your account login).
- `ADDRESS`: The address where you deploy this server.
- `DAVICAL_USER`: CalDav server user.
- `DAVICAL_PASS`: CalDav server password.
- `LOGIN`: Your 42 login.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss the changes you wish to make.