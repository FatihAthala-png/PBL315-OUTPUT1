import json
from html import unescape
from pathlib import Path

from flask import Flask, abort, render_template


BASE_DIR = Path(__file__).parent
app = Flask(__name__)
NAV_PAGES = {
    "pokemon-tcg": "pokemon_tcg",
    "action-figures": "action_figures",
    "rarity-vault": "rarity_vault",
    "cek-resi-pesanan": "cek_resi_pesanan",
    "panduan-grading-orisinalitas": "panduan_grading_orisinalitas",
}
BREADCRUMB_LABELS = {
    "home": "Semua Pokémon TCG & Figures",
    "pokemon_tcg": "Semua Pokémon TCG",
    "action_figures": "Action Figures",
    "rarity_vault": "Rarity Vault",
    "cek_resi_pesanan": "Cek Resi & Pesanan",
    "panduan_grading_orisinalitas": "Panduan Grading & Orisinalitas",
}


def get_products():
    """Sumber data sementara; ganti fungsi ini dengan query MySQL nanti."""
    with (BASE_DIR / "data" / "products.json").open(encoding="utf-8") as file:
        return [
            {
                key: unescape(value) if isinstance(value, str) else value
                for key, value in product.items()
            }
            for product in json.load(file)
        ]


@app.route("/")
def home():
    return render_template(
        "index.html",
        products=get_products(),
        active_page="home",
        breadcrumb_label=BREADCRUMB_LABELS["home"],
    )


@app.route("/<page>")
def page(page):
    active_page = NAV_PAGES.get(page)

    if not active_page:
        abort(404)

    return render_template(
        "index.html",
        products=get_products(),
        active_page=active_page,
        breadcrumb_label=BREADCRUMB_LABELS[active_page],
    )


if __name__ == "__main__":
    app.run(debug=True)
