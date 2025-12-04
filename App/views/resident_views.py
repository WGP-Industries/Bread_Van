# File: App/views/resident_views.py (REPLACE THE EXISTING FILE)

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, current_user
from App.api.security import role_required, current_user_id
from App.controllers import resident as resident_controller
from App.controllers import user as user_controller
from App.controllers import stop as stop_controller
from App.controllers import drive as drive_controller
from App.models import Drive, Stop
from datetime import datetime, date

resident_views = Blueprint('resident_views', __name__, template_folder='../templates')

# Api Endpoints

@resident_views.route('/api/resident/me', methods=['GET'])
@jwt_required()
@role_required('Resident')
def api_me():
    uid = current_user_id()
    return jsonify({'id': uid}), 200

@resident_views.route('/api/resident/stops', methods=['POST'])
@jwt_required()
@role_required('Resident')
def api_create_stop():
    data = request.get_json() or {}
    drive_id = data.get('drive_id')
    if not drive_id:
        return jsonify({'error': {'code': 'validation_error', 'message': 'drive_id required'}}), 422
    
    uid = current_user_id()
    resident = user_controller.get_user(uid)
    
    try:
        stop = resident_controller.resident_request_stop(resident, drive_id)
    except ValueError as e:
        return jsonify({'error': {'code': 'validation_error', 'message': str(e)}}), 400
    
    out = stop.get_json() if hasattr(stop, 'get_json') else stop
    return jsonify(out), 201

@resident_views.route('/api/resident/stops/<int:stop_id>', methods=['DELETE'])
@jwt_required()
@role_required('Resident')
def api_delete_stop(stop_id):
    uid = current_user_id()
    resident = user_controller.get_user(uid)
    
    try:
        resident_controller.resident_cancel_stop(resident, stop_id)
    except ValueError as e:
        return jsonify({'error': {'code': 'resource_not_found', 'message': str(e)}}), 404
    
    return '', 204

@resident_views.route('/api/resident/inbox', methods=['GET'])
@jwt_required()
@role_required('Resident')
def api_inbox():
    uid = current_user_id()
    resident = user_controller.get_user(uid)
    items = resident_controller.resident_view_inbox(resident)
    items = [i.get_json() if hasattr(i, 'get_json') else i for i in (items or [])]
    return jsonify({'items': items}), 200

@resident_views.route('/api/resident/driver-stats', methods=['GET'])
@jwt_required()
@role_required('Resident')
def api_driver_stats():
    params = request.args
    driver_id = params.get('driver_id')
    if not driver_id:
        return jsonify({'error': {'code': 'validation_error', 'message': 'driver_id is required'}}), 422
    
    uid = current_user_id()
    resident = user_controller.get_user(uid)
    
    try:
        stats = resident_controller.resident_view_driver_stats(resident, int(driver_id))
    except ValueError as e:
        return jsonify({'error': {'code': 'not_found', 'message': str(e)}}), 404
    
    return jsonify({'stats': stats}), 200

@resident_views.route('/api/resident/stops_for_map', methods=['GET'])
@jwt_required()
@role_required('Resident')
def api_stops_for_map():
    uid = current_user_id()
    resident = user_controller.get_user(uid)
    
    stops = stop_controller.get_resident_stops_for_map(resident)
    return jsonify([s.get_json() for s in stops]), 200

# Web Endpoints

@resident_views.route('/resident/dashboard')
@jwt_required()
def resident_dashboard():
    if current_user.type != 'Resident':
        return redirect('/')
    
    unread_count = current_user.get_unread_count()
    
    subscribed_count = len(current_user.subscribed_drives)
    
    active_stops = stop_controller.get_stops_by_resident(current_user.id)
    
    # Get today's drives in the resident's area and street
    todays_drives = Drive.query.filter_by(
        areaId=current_user.areaId,
        streetId=current_user.streetId,
        date=date.today()
    ).all()
    
    return render_template('resident_dashboard.html',
                         unread_count=unread_count,
                         subscribed_count=subscribed_count,
                         active_stops=active_stops,
                         todays_drives=todays_drives)

@resident_views.route('/resident/drives')
@jwt_required()
def view_area_drives():
    if current_user.type != 'Resident':
        return redirect('/')
    
    # Get all drives in resident's area
    drives = drive_controller.get_drives_by_area(current_user.areaId)
    
    # Separate upcoming and past drives
    today = date.today()
    upcoming = []
    past = []
    
    for drive in drives:
        if drive.date >= today and drive.status in ["Upcoming", "In Progress"]:
            upcoming.append(drive)
        else:
            past.append(drive)
    
    return render_template('resident_drives.html', 
                         upcoming=upcoming, 
                         past=past)

@resident_views.route('/resident/drive/<int:drive_id>')
@jwt_required()
def drive_detail(drive_id):
    if current_user.type != 'Resident':
        return redirect('/')
    
    drive = Drive.query.get(drive_id)
    if not drive:
        flash('Drive not found')
        return redirect('/resident/drives')
    
    # Check if resident has requested a stop for this drive
    has_stop = Stop.query.filter_by(
        driveId=drive_id,
        residentId=current_user.id
    ).first() is not None
    
    # Check if resident is subscribed
    is_subscribed = drive_id in current_user.subscribed_drives
    
    return render_template('resident_drive_detail.html',
                         drive=drive,
                         has_stop=has_stop,
                         is_subscribed=is_subscribed)

@resident_views.route('/resident/drive/<int:drive_id>/request_stop')
@jwt_required()
def request_stop_web(drive_id):
    if current_user.type != 'Resident':
        return redirect('/')
    
    try:
        stop = resident_controller.resident_request_stop(current_user, drive_id)
        flash('Stop requested successfully!')
    except ValueError as e:
        flash(str(e))
    
    return redirect(f'/resident/drive/{drive_id}')

@resident_views.route('/resident/drive/<int:drive_id>/cancel_stop')
@jwt_required()
def cancel_stop_web(drive_id):
    if current_user.type != 'Resident':
        return redirect('/')
    
    try:
        stop = resident_controller.resident_cancel_stop(current_user, drive_id)
        flash('Stop cancelled successfully!')
    except ValueError as e:
        flash(str(e))
    
    return redirect(f'/resident/drive/{drive_id}')

@resident_views.route('/resident/drive/<int:drive_id>/subscribe')
@jwt_required()
def subscribe_drive_web(drive_id):
    if current_user.type != 'Resident':
        return redirect('/')
    
    try:
        resident_controller.resident_subscribe_to_drive(current_user, drive_id)
        flash('Subscribed to drive notifications!')
    except ValueError as e:
        flash(str(e))
    
    return redirect(f'/resident/drive/{drive_id}')

@resident_views.route('/resident/drive/<int:drive_id>/unsubscribe')
@jwt_required()
def unsubscribe_drive_web(drive_id):
    if current_user.type != 'Resident':
        return redirect('/')
    
    try:
        resident_controller.resident_unsubscribe_from_drive(current_user, drive_id)
        flash('Unsubscribed from drive notifications')
    except ValueError as e:
        flash(str(e))
    
    return redirect(f'/resident/drive/{drive_id}')

@resident_views.route('/resident/stops')
@jwt_required()
def view_stops():
    if current_user.type != 'Resident':
        return redirect('/')
    
    stops = stop_controller.get_stops_by_resident(current_user.id)
    return render_template('resident_stops.html', stops=stops)

@resident_views.route('/resident/settings', methods=['GET', 'POST'])
@jwt_required()
def notification_settings():
    if current_user.type != 'Resident':
        return redirect('/')
    
    if request.method == 'POST':
        preferences = []
        if request.form.get('drive_scheduled'):
            preferences.append('drive_scheduled')
        if request.form.get('menu_updated'):
            preferences.append('menu_updated')
        if request.form.get('eta_updated'):
            preferences.append('eta_updated')
        if request.form.get('arrival_alert'):
            preferences.append('arrival_alert')
        
        resident_controller.resident_update_notification_preferences(current_user, preferences)
        flash('Notification preferences updated!')
        return redirect('/resident/dashboard')
    
    current_prefs = current_user.notification_preferences or []
    return render_template('notification_settings.html', 
                         current_prefs=current_prefs)

@resident_views.route('/resident/notifications', methods=['GET'])
@jwt_required()
def resident_notifications():
    if current_user.type != 'Resident':
        return redirect('/')
    
    resident = user_controller.get_user(current_user.id)
    notifications = resident_controller.resident_view_inbox(resident)
    
    return render_template("notification.html", notifications=notifications)

@resident_views.route('/resident/notifications/mark_all_read')
@jwt_required()
def mark_all_read():
    if current_user.type != 'Resident':
        return redirect('/')
    
    resident_controller.resident_mark_all_notifications_read(current_user)
    flash('All notifications marked as read')
    return redirect('/resident/notifications')