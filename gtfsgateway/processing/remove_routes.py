def remove_routes(static_database, route_ids):
    cursor = static_database.get_connection().cursor()

    for route_id in route_ids:
        cursor.execute("DELETE FROM routes WHERE route_id = ?", (route_id,))
    
    cursor.execute("DELETE FROM agency WHERE agency_id NOT IN (SELECT agency_id FROM routes)")
    cursor.execute("DELETE FROM trips WHERE route_id NOT IN (SELECT route_id FROM routes)")
    cursor.execute("DELETE FROM stop_times WHERE trip_id NOT IN (SELECT trip_id FROM trips)")
    cursor.execute("DELETE FROM stops WHERE stop_id NOT IN (SELECT stop_id FROM stop_times) AND location_type = ''")
    cursor.execute("DELETE FROM stops WHERE stop_id NOT IN (SELECT parent_station FROM stops) AND location_type = '1'")
    cursor.execute("DELETE FROM calendar WHERE service_id NOT IN (SELECT service_id FROM trips)")
    cursor.execute("DELETE FROM calendar_dates WHERE service_id NOT IN (SELECT service_id FROM trips)")
    cursor.execute("DELETE FROM transfers WHERE from_stop_id NOT IN (SELECT stop_id FROM stops)")
    cursor.execute("DELETE FROM transfers WHERE to_stop_id NOT IN (SELECT stop_id FROM stops)")

    cursor.close()