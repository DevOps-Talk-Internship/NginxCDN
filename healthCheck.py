from flask import Flask, jsonify, request
import mariadb
import sys
import logging

app = Flask(__name__)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_database_user',
    'password': 'your_database_password',
    'database': 'your_database_name'
}

def get_db_connection():
    """Establish a connection to the MariaDB database"""
    try:
        conn = mariadb.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return conn
    except mariadb.Error as e:
        app.logger.error(f"Database Connection Error: {e}")
        return None

@app.route('/health', methods=['GET'])
def check_database_health():
    """Endpoint to check database health with comprehensive error handling"""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({
                'status': 'error',
                'message': 'Unable to connect to the database',
                'details': 'Connection could not be established',
                'client_ip': client_ip
            }), 500

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return jsonify({
                    'status': 'healthy',
                    'message': 'Database connection successful',
                    'details': {
                        'host': DB_CONFIG['host'],
                        'database': DB_CONFIG['database']
                    },
                    'client_ip': client_ip
                }), 200

        except mariadb.Error as query_error:
            return jsonify({
                'status': 'error',
                'message': 'Database query failed',
                'details': str(query_error),
                'client_ip': client_ip
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'critical',
            'message': 'Unexpected database error',
            'details': str(e),
            'client_ip': client_ip
        }), 500

@app.errorhandler(mariadb.Error)
def handle_database_error(error):
    """Global error handler for MariaDB specific errors"""
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return jsonify({
        'status': 'error',
        'message': 'Database system error',
        'details': str(error),
        'client_ip': client_ip
    }), 500

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Application configuration
app.config.update(
    DEBUG=True,
    JSON_SORT_KEYS=False
)

if __name__ == '__main__':
    try:
        test_conn = get_db_connection()
        if test_conn:
            print("Initial database connection successful")
            test_conn.close()
        else:
            print("Warning: Could not establish initial database connection")

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except Exception as startup_error:
        print(f"Application startup failed: {startup_error}")
        sys.exit(1)
