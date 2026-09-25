from flask import Blueprint, jsonify

from .decorators import super_admin_required

admin_bp = Blueprint(
    "admin",
    __name__,
)


@admin_bp.get("/")
@super_admin_required
def admin_home():
    return jsonify({"message": "Welcome to the BiYo Events Super Admin area"})
