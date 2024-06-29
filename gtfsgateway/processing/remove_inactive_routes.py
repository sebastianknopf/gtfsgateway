def remove_inactive_routes(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    route_ids = [route['id'] for route in gateway._gateway_config['processing']['route_index'] if route['include'] == False]
    for route_id in route_ids:
        cursor.execute("DELETE FROM routes WHERE route_id = ?", (route_id,))

    cursor.close()