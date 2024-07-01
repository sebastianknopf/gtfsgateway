def apiresponse(function):
    def _dec_function(*args, **kwargs):
        result = function(*args, **kwargs)

        if not isinstance(result, object) and hasattr(result, 'code') and hasattr(result, 'message'):
            return {
                'code': 200,
                'message': 'OK'
            }
        else:
            return result
        
    return _dec_function