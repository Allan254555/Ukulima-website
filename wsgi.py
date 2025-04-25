from website import create_app
from flask_cors  import CORS
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
print("Loading environment variables from .env file", env_path)  # Debug to check file path


load_dotenv(dotenv_path=env_path)
print("Loading environment variables from .env file", os.getenv('FLASK_ENV'))

app = create_app()
CORS(app)

if __name__ == "__main__": 
    flask_env = os.getenv('FLASK_ENV')
    if flask_env == 'development':
        print("Running in development mode")
        app.run(debug=True)
        
    else:
        print("Running in production mode")
        from waitress import serve
        serve(app, host="0.0.0.0", port=8000)