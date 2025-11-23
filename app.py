from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from Flask app!", 200

@app.route('/health')
def health_check():
    return jsonify(status="healthy"), 200

# تنظیم Cache-Control صحیح برای فایل‌های static
@app.after_request
def add_cache_header(response):
    # فقط روی فایل‌های static هدر cache اعمال شود
    if request.path.startswith("/static/"):
        # حذف کامل هدر no-cache
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response

if __name__ == '__main__':
    # Flask در Production باید بدون debug اجرا شود
    app.run(host='0.0.0.0', port=8000)
