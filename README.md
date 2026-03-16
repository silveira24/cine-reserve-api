# CineReserve API 🎬

A professional Django-based movie reservation system. This project is built with a focus on scalability, security, and developer experience, utilizing a fully dockerized environment.

## 🚀 Quick Start

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Setup

1. **Clone the repository:**

    [github.com/silveira24/cine-reserve-api](https://github.com/silveira24/cine-reserve-api)

   ```bash
   git clone https://github.com/silveira24/cine-reserve-api.git
   cd cine-reserve-api
   ```

2. **Environment Variables:**
   The project uses environment variables for configuration. Create a `.env` file in the root directory. You can use the example below:
   ```bash
   cp .env.example .env
   ```

3. **Build and Run the Containers:**
   The following command will build the image, create the database volume, run migrations, and start the development server:
   ```bash
   docker compose up -d --build
   ```

4. **Access the API:**
   Once the build is finished and the logs show "Starting the application", the API will be available at:
   * **API:** [http://localhost:8000/](http://localhost:8000/)
   * **Admin Interface:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 🛠 Useful Commands

### Creating a Superuser
To access the Django Admin, you'll need an admin account:
```bash
docker compose exec app python manage.py createsuperuser
```

### Running Migrations
Migrations are applied automatically on startup via the `entrypoint.sh`, but you can run them manually if needed:
```bash
docker compose exec app python manage.py migrate
```

---