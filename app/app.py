import os, json, urllib.request
import pymysql, redis
from flask import Flask, render_template_string

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME", "shop")
REDIS_HOST = os.environ.get("REDIS_HOST")
S3_URL = os.environ.get("S3_URL")

cache = redis.Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2,
                    socket_timeout=2, decode_responses=True)
db_ready = False


def imds(path):
    """Read instance metadata (instance id, AZ) using IMDSv2."""
    try:
        req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token", method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
        token = urllib.request.urlopen(req, timeout=2).read().decode()
        req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/" + path,
            headers={"X-aws-ec2-metadata-token": token})
        return urllib.request.urlopen(req, timeout=2).read().decode()
    except Exception:
        return "unknown"


def get_conn():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                           database=DB_NAME, connect_timeout=5,
                           cursorclass=pymysql.cursors.DictCursor)


def init_db():
    global db_ready
    conn = get_conn()
    with conn.cursor() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE,
            price DECIMAL(10,2),
            image VARCHAR(100))""")
        c.executemany(
            "INSERT IGNORE INTO products (name, price, image) VALUES (%s,%s,%s)",
            [("Laptop", 55000, "p1.jpg"),
             ("Smartphone", 20000, "p2.jpg"),
             ("Headphones", 2500, "p3.jpg")])
    conn.commit()
    conn.close()
    db_ready = True


def get_products():
    try:
        cached = cache.get("products")
        if cached:
            return json.loads(cached), "HIT (from ElastiCache)"
    except Exception:
        pass
    if not db_ready:
        init_db()
    conn = get_conn()
    with conn.cursor() as c:
        c.execute("SELECT name, price, image FROM products")
        rows = c.fetchall()
    conn.close()
    rows = [{"name": r["name"], "price": float(r["price"]), "image": r["image"]} for r in rows]
    try:
        cache.setex("products", 60, json.dumps(rows))
    except Exception:
        pass
    return rows, "MISS (from RDS database)"


PAGE = """
<html><head><title>Cloud Shop</title>
<style>
 body{font-family:Arial;background:#f4f4f4;margin:0}
 header{background:#232f3e;color:#fff;padding:20px;text-align:center}
 .grid{display:flex;gap:20px;justify-content:center;padding:30px;flex-wrap:wrap}
 .card{background:#fff;padding:15px;border-radius:8px;width:220px;text-align:center}
 .card img{width:200px;height:150px;object-fit:cover}
 .info{text-align:center;background:#ff9900;padding:10px}
</style></head><body>
<header><h1>Cloud Shop</h1></header>
<div class="info">Served by <b>{{iid}}</b> in <b>{{az}}</b> | Cache: <b>{{src}}</b></div>
<div class="grid">
{% for p in products %}
 <div class="card"><img src="{{s3}}/images/{{p.image}}"><h3>{{p.name}}</h3><p>₹{{p.price}}</p></div>
{% endfor %}
</div></body></html>
"""


@app.route("/")
def index():
    products, src = get_products()
    return render_template_string(PAGE, products=products, src=src, s3=S3_URL,
                                  iid=imds("instance-id"),
                                  az=imds("placement/availability-zone"))


@app.route("/health")
def health():
    return "OK", 200