from flask import Flask, Response, jsonify, send_file

app = Flask(__name__)

@app.route("/")
def index():
    return "200, connect success"

@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"error": str(error)}), 500

@app.route("/init-log")
def get_log():
    try:
        logfile = "/var/log/cloud-init-output.log"
        with open(logfile, "r") as f:
            content = f.read()
            return Response(content, mimetype="text/plain")
    except Exception as e:
        return handle_error(e)

@app.route("/ca-download")
def download_ca():
    try:
        cafile = "/vpn-certs/server-root-ca.pem"
        return send_file(f"{cafile}", as_attachment=True)
    except Exception as e:
        return handle_error(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
