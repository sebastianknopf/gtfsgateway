def remove_routes(gateway):
    cursor = gateway._processing_database._connection.cursor()

    route_ids = [route['id'] for route in gateway._gateway_config['processing']['routes'] if route['published'] == False]
    for route_id in route_ids:
        cursor.execute("DELETE FROM routes WHERE route_id = ?", (route_id,))

    cursor.close()