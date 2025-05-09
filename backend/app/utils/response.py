from flask import jsonify, current_app


def make_response(code=200, message='success', data=None):
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), code

def validate_api_key(request):
    """生产环境API密钥验证"""
    api_key = request.headers.get('X-API-KEY')
    return api_key == current_app.config['API_KEY']
