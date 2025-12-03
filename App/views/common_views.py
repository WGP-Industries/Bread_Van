from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required
from App.controllers import area as area_controller
from App.controllers import street as street_controller
from App.controllers import drive as drive_controller
from App.controllers import driver as driver_controller
from App.models import Item

common_views = Blueprint('common_views', __name__)



@common_views.route('/menu', methods=['GET'])
def get_menu():
    items = Item.query.all()
    return render_template("menu.html", items=items)

@common_views.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    return render_template("profile.html")

@common_views.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    return render_template("notification.html")

@common_views.route('/map', methods=['GET'])
@jwt_required()
def get_map():
    return render_template("map.html", lat=10.6918, lng=-61.2225)

@common_views.route('/areas', methods=['GET'])
def get_areas():
    areas = area_controller.admin_view_all_areas() if hasattr(area_controller, 'admin_view_all_areas') else []
    items = [a.get_json() if hasattr(a, 'get_json') else a for a in (areas or [])]
    return jsonify({'items': items}), 200


@common_views.route('/streets', methods=['GET'])
def get_streets():
    area_id = request.args.get('area_id')
    streets = []
    if area_id and hasattr(street_controller, 'get_streets_for_area'):
        streets = street_controller.get_streets_for_area(area_id)
    elif hasattr(street_controller, 'admin_view_all_streets'):
        streets = street_controller.admin_view_all_streets()
    items = [s.get_json() if hasattr(s, 'get_json') else s for s in (streets or [])]
    return jsonify({'items': items}), 200


@common_views.route('/streets/<int:street_id>/drives', methods=['GET'])
def street_drives(street_id):
    date = request.args.get('date')
    drives = []
    if hasattr(drive_controller, 'get_drives_for_street'):
        drives = drive_controller.get_drives_for_street(street_id, date)
    items = [d.get_json() if hasattr(d, 'get_json') else d for d in (drives or [])]
    return jsonify({'items': items}), 200

@common_views.route('/van_location', methods=['GET'])
def van_location():
    
    loc = driver_controller.get_latest_driver_location()

    if not loc:
        return jsonify({"lat": 0, "lng": 0}), 200

    return jsonify({"lat": loc.last_lat, "lng": loc.last_lng}), 200
