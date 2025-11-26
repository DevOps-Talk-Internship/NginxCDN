from flask import Flask, jsonify, request
import mariadb
import sys
import logging

app = Flask(__name__)
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'database': 'ts'
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

def ensure_schema():
    """Create the table for logging client IPs if it doesn't exist"""
    conn = get_db_connection()
    if conn is None:
        app.logger.error("Schema init failed: no DB connection")
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_ip VARCHAR(45) NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
    except mariadb.Error as e:
        app.logger.error(f"Schema creation error: {e}")
    finally:
        conn.close()

@app.route('/health', methods=['GET'])
def check_database_health():
    """Endpoint to check database health and log client IP"""
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

            # Log client IP
            cursor.execute(
                "INSERT INTO health_checks (client_ip) VALUES (?)",
                (client_ip,)
            )
            conn.commit()

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

            return jsonify({
                'status': 'error',
                'message': 'Unexpected empty result from SELECT 1',
                'client_ip': client_ip
            }), 500

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

@app.route('/health/logs', methods=['GET'])
def get_health_logs():
    """Return recent client IP logs"""
    try:
        limit = int(request.args.get('limit', 50))
    except ValueError:
        limit = 50

    conn = get_db_connection()
    if conn is None:
        return jsonify({'status': 'error', 'message': 'DB connection failed'}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, client_ip, checked_at
            FROM health_checks
            ORDER BY checked_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'status': 'ok',
            'count': len(rows),
            'logs': [
                {'id': r[0], 'client_ip': r[1], 'checked_at': r[2].isoformat()}
                for r in rows
            ]
        }), 200
    except mariadb.Error as e:
        return jsonify({'status': 'error', 'message': 'Query failed', 'details': str(e)}), 500

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
        ensure_schema()
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
