import datetime

from flask import Flask, render_template, request, send_file
from sassutils.wsgi import SassMiddleware

from .convert import convert
from .create import HP_TO_MM, create
from .update import update

__version__ = datetime.datetime.now().strftime("%Y.%m.%d.%H%M")


def create_app() -> Flask:
    app = Flask(__name__)

    if app.debug:
        app.wsgi_app = SassMiddleware(
            app.wsgi_app,
            {__name__: ("static/scss", "static/css", "/static/css", False)},
        )

    @app.get("/")
    def home_endpoint():
        return render_template("index.html", hp_sizes=list(HP_TO_MM.keys()), symbols={})

    @app.post("/create")
    def create_endpoint():
        hp = request.form.get("hp", 12, type=int)
        name = request.form.get("name", "Untitled Module", type=str)

        return send_file(
            create(hp=hp, name=name),
            mimetype="image/svg+xml",
            as_attachment=True,
            download_name="panel.svg",
        )

    @app.post("/update")
    def update_endpoint():
        input_file = request.files.get("file")

        return send_file(
            update(input_file.stream),
            mimetype="image/svg+xml",
            as_attachment=True,
            download_name=input_file.filename,
        )

    @app.post("/convert")
    def convert_endpoint():
        input_file = request.files.get("file")
        name = input_file.filename.removesuffix(".svg")

        return send_file(
            convert(input_file.stream, name),
            mimetype="application/x-kicad-pcb",
            as_attachment=True,
            download_name=f"{name}.kicad_pcb",
        )

    return app
