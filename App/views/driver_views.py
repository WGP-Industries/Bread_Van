# File: App/views/driver_views.py (REPLACE THE EXISTING FILE)

from flask import Blueprint, request, jsonify, redirect, render_template, flash
from flask_jwt_extended import jwt_required, current_user

from App.controllers import driver as driver_controller
from App.controllers import user as user_controller
from App.controllers import drive as drive_controller
from App.controllers import stop as stop_controller
from App.controllers import area as area_controller
from App.controllers import street as street_controller
from App.controllers import item as item_controller
from App.api.security import role_required, current_user_id
from App.models import Drive, Stop
from datetime import datetime, date

driver_views = Blueprint('driver_views', __name__, template_folder='../templates')

# API Endpoints

@driver_views.route('/api/driver/me', methods=['GET'])
@jwt_required()
@role_required('Driver')
def api_me():
    uid = current_user_id()
    return jsonify({'id': uid}), 200

@driver_views.route('/api/driver/drives', methods=['GET'])
@jwt_required()
@role_required('Driver')
def api_list_drives():
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    all_drives = driver_controller.driver_view_drives(driver)
    items = [d.get_json() if hasattr(d, 'get_json') else d for d in (all_drives or [])]
    return jsonify({'items': items}), 200

@driver_views.route('/api/driver/drives', methods=['POST'])
@jwt_required()
@role_required('Driver')
def api_create_drive():
    data = request.get_json() or {}
    area_id = data.get('area_id')
    street_id = data.get('street_id')
    date_str = data.get('date')
    time_str = data.get('time')
    menu = data.get('menu')
    eta = data.get('eta')
    
    if not street_id or not date_str or not time_str:
        return jsonify({'error': {'code': 'validation_error', 'message': 'street_id, date and time required'}}), 422
    
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    drive = driver_controller.driver_schedule_drive(driver, area_id, street_id, date_str, time_str, menu, eta)
    out = drive.get_json() if hasattr(drive, 'get_json') else drive
    return jsonify(out), 201

@driver_views.route('/api/driver/drives/<int:drive_id>/start', methods=['POST'])
@jwt_required()
@role_required('Driver')
def api_start_drive(drive_id):
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    driver_controller.driver_start_drive(driver, drive_id)
    return jsonify({'id': drive_id, 'status': 'started'}), 200

@driver_views.route('/api/driver/drives/<int:drive_id>/end', methods=['POST'])
@jwt_required()
@role_required('Driver')
def api_end_drive(drive_id):
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    res = driver_controller.driver_end_drive(driver)
    return jsonify({'id': getattr(res, 'id', drive_id), 'status': 'ended'}), 200

@driver_views.route('/api/driver/drives/<int:drive_id>/cancel', methods=['POST'])
@jwt_required()
@role_required('Driver')
def api_cancel_drive(drive_id):
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    driver_controller.driver_cancel_drive(driver, drive_id)
    return jsonify({'id': drive_id, 'status': 'cancelled'}), 200

@driver_views.route('/api/driver/drives/<int:drive_id>/requested-stops', methods=['GET'])
@jwt_required()
@role_required('Driver')
def api_requested_stops(drive_id):
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    stops = driver_controller.driver_view_requested_stops(driver, drive_id)
    items = [s.get_json() if hasattr(s, 'get_json') else s for s in (stops or [])]
    return jsonify({'items': items}), 200

@driver_views.route('/api/driver/location', methods=['POST'])
@jwt_required()
@role_required('Driver')
def api_update_driver_location():
    uid = current_user_id()
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")
    
    driver_controller.update_driver_location(uid, lat, lng)
    return jsonify({"status": "ok"}), 200

@driver_views.route('/api/driver/drives/<int:drive_id>/map', methods=['GET'])
@jwt_required()
@role_required("Driver")
def api_drive_map(drive_id):
    stops = drive_controller.get_stops_for_drive(drive_id)
    data = [s.get_json() for s in stops]
    return jsonify(data), 200

# Web Views

@driver_views.route('/driver/dashboard')
@jwt_required()
def driver_dashboard():
    if current_user.type != 'Driver':
        return redirect('/')
    
    # Get upcoming drives
    drives = driver_controller.driver_view_drives(current_user)
    
    # Get active drive
    active_drive = Drive.query.filter_by(
        driverId=current_user.id, 
        status="In Progress"
    ).first()
    
    # Get stop requests for active drive
    active_stops = []
    if active_drive:
        active_stops = stop_controller.get_stops_by_drive(active_drive.id)
    
    # Get next upcoming drive
    upcoming_drives = [d for d in drives if d.status == "Upcoming"]
    next_drive = upcoming_drives[0] if upcoming_drives else None
    
    return render_template('driver_dashboard.html',
                         upcoming_drives=upcoming_drives,
                         active_drive=active_drive,
                         active_stops=active_stops,
                         next_drive=next_drive,
                         pending_stops=len(active_stops))

@driver_views.route('/driver/drives/schedule', methods=['GET', 'POST'])
@jwt_required()
def schedule_drive():
    if current_user.type != 'Driver':
        return redirect('/')
    
    if request.method == 'POST':
        area_id = request.form.get('area_id')
        street_id = request.form.get('street_id')
        date = request.form.get('date')
        time = request.form.get('time')
        menu = request.form.get('menu')
        eta = request.form.get('eta')
        
        try:
            drive = driver_controller.driver_schedule_drive(
                current_user, area_id, street_id, date, time, menu, eta
            )
            flash('Drive scheduled successfully!')
            return redirect('/driver/dashboard')
        except ValueError as e:
            flash(str(e))
            return redirect('/driver/drives/schedule')
    
    areas = area_controller.get_all_areas()
    return render_template('schedule_drive.html', areas=areas)

@driver_views.route('/driver/drives', methods=['GET'])
@jwt_required()
def list_drives():
    uid = current_user_id()
    driver = user_controller.get_user(uid)
    
    all_drives = driver_controller.driver_view_drives(driver)
    
    upcoming_drives = []
    in_progress_drives = []
    completed_drives = []
    cancelled_drives = []
    
    for drive in all_drives:
        if drive.status == "Upcoming":
            upcoming_drives.append(drive)
        elif drive.status == "In Progress":
            in_progress_drives.append(drive)
        elif drive.status == "Completed":
            completed_drives.append(drive)
        elif drive.status == "Cancelled":
            cancelled_drives.append(drive)
    
    return render_template('driver_drives.html',
                         upcoming_drives=upcoming_drives,
                         in_progress_drives=in_progress_drives,
                         completed_drives=completed_drives,
                         cancelled_drives=cancelled_drives)

@driver_views.route('/driver/drives/<int:drive_id>', methods=['GET'])
@jwt_required()
def drive_details(drive_id):
    """Display detailed view of a specific drive"""
    if current_user.type != 'Driver':
        return redirect('/')
    
    drive = Drive.query.get(drive_id)
    
    if not drive or drive.driverId != current_user.id:
        flash("Drive not found or you don't have permission to view it.")
        return redirect('/driver/drives')
    
    return render_template('drive_details.html', drive=drive)

@driver_views.route('/driver/drives/<int:drive_id>/edit', methods=['GET'])
@jwt_required()
def edit_drive(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    drive = Drive.query.get(drive_id)
    
    if not drive or drive.driverId != current_user.id:
        return redirect('/driver/drives')
    
    return render_template('edit_drive.html', drive=drive)

@driver_views.route('/driver/drives/<int:drive_id>/update', methods=['POST'])
@jwt_required()
def update_drive(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    menu = request.form.get('menu')
    eta = request.form.get('eta')
    
    # Update menu
    if menu:
        driver_controller.driver_update_drive_menu(current_user, drive_id, menu)
    
    # Update ETA
    if eta:
        driver_controller.driver_update_drive_eta(current_user, drive_id, eta)
    
    return redirect(f'/driver/drives/{drive_id}')

@driver_views.route('/driver/drives/<int:drive_id>/start', methods=['GET'])
@jwt_required()
def start_drive_web(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    try:
        driver_controller.driver_start_drive(current_user, drive_id)
        flash('Drive started successfully!')
    except ValueError as e:
        flash(str(e))
    
    return redirect('/driver/dashboard')

@driver_views.route('/driver/drives/<int:drive_id>/end', methods=['GET'])
@jwt_required()
def end_drive_web(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    try:
        result = driver_controller.driver_end_drive(current_user)
        flash('Drive ended successfully!')
    except ValueError as e:
        flash(str(e))
    
    return redirect('/driver/dashboard')

@driver_views.route('/driver/drives/<int:drive_id>/cancel', methods=['GET'])
@jwt_required()
def cancel_drive_web(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    try:
        driver_controller.driver_cancel_drive(current_user, drive_id)
        flash('Drive cancelled successfully!')
    except ValueError as e:
        flash(str(e))
    
    return redirect('/driver/drives')

@driver_views.route('/driver/update_location', methods=['POST'])
@jwt_required()
def update_location_web():
    if current_user.type != 'Driver':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    try:
        driver_controller.update_driver_location(current_user.id, lat, lng)
        return jsonify({'status': 'success'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@driver_views.route('/add-item', methods=['GET', 'POST'])
@jwt_required()
def add_item_page():
    if current_user.type != 'Driver':
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        tags = request.form.get("tags")

        item_controller.add_item(name, price, description, tags)
        return redirect('/menu')
    
    return render_template('add_item.html')

@driver_views.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_item(item_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    item = item_controller.get_item_by_id(item_id)

    if request.method == 'POST':
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        tags = request.form.get("tags")

        item_controller.update_item(item_id, name, price, description, tags)
        return redirect('/menu')

    return render_template("edit_item.html", item=item)

@driver_views.route('/item/<int:item_id>/delete', methods=['GET'])
@jwt_required()
def delete_item(item_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    item_controller.delete_item(item_id)
    return redirect('/menu')

@driver_views.route('/driver/drives/<int:drive_id>/requested-stops', methods=['GET'])
@jwt_required()
def requested_stops_web(drive_id):
    if current_user.type != 'Driver':
        return redirect('/')
    
    from App.models import Drive
    drive = Drive.query.get(drive_id)
    if not drive or drive.driverId != current_user.id:
        flash('Drive not found or access denied.')
        return redirect('/driver/dashboard')
    
    stops = drive.stops  
    
    return render_template('driver_requested_stops.html', drive=drive, stops=stops)