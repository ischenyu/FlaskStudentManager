
import datetime
from flask import Blueprint, jsonify
import psutil

bp = Blueprint('system', __name__, url_prefix='/api/system')

def get_system_info():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    uptime = str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time()))
    system_info = {
        'current': current_time,
        'uptime': uptime,
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'load': psutil.getloadavg()
    }
    return jsonify(system_info)

@bp.route('status')
def system_status():
    return get_system_info()
