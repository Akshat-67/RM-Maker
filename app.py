from flask import Flask, url_for as flask_url_for
from routes.dashboard import dashboard_bp
from routes.cases import cases_bp
from routes.upload import upload_bp
from routes.generation import generation_bp
from routes.template_builder import template_builder_bp
from routes.epanjiyan import epanjiyan_bp

app = Flask(__name__, template_folder="web_templates", static_folder="static")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.template_filter('basename')
def basename_filter(s):
    if not s:
        return ""
    return str(s).replace('\\', '/').split('/')[-1]

@app.context_processor
def override_url_for():
    def custom_url_for(endpoint, **values):
        global_endpoints_map = {
            'dashboard': 'dashboard.dashboard',
            'new_case': 'cases.new_case',
            'view_case': 'cases.view_case',
            'template_builder': 'template_builder.template_builder',
            'devlys_to_unicode_route': 'dashboard.devlys_to_unicode_route'
        }
        if endpoint in global_endpoints_map:
            endpoint = global_endpoints_map[endpoint]
        return flask_url_for(endpoint, **values)
    return dict(url_for=custom_url_for)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(cases_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(generation_bp)
app.register_blueprint(template_builder_bp)
app.register_blueprint(epanjiyan_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
