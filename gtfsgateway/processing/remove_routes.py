def remove_routes(static_database, route_ids):
    cursor = static_database.get_connection().cursor()

    for route_id in route_ids:
        cursor.execute("DELETE FROM routes WHERE route_id = ?", (route_id,))

    cursor.close()