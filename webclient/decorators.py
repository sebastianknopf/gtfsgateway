def apiresponse(function):
    def _dec_function(*args, **kwargs):
        result = function(*args, **kwargs)

        if not isinstance(result, tuple) or not len(result) == 2:
            return {
                'code': 200,
                'message': 'OK'
            }
        else:
            return {
                'code': result[0],
                'message': result[1]
            }
        
    return _dec_function