from datetime import datetime

def cleanup(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    current_date = datetime.now().strftime('%Y%m%d')
    cursor.execute(f"DELETE FROM calendar WHERE end_date < '{current_date}'")
    cursor.execute(f"DELETE FROM calendar_dates WHERE date < '{current_date}'")
    cursor.execute(f"DELETE FROM trips WHERE service_id NOT IN (SELECT service_id FROM calendar UNION SELECT service_id FROM calendar_dates)")

    cursor.execute("DELETE FROM trips WHERE route_id NOT IN (SELECT route_id FROM routes)")
    cursor.execute("DELETE FROM routes WHERE route_id NOT IN (SELECT route_id FROM trips)")
    cursor.execute("DELETE FROM agency WHERE agency_id NOT IN (SELECT agency_id FROM routes)")
    cursor.execute("DELETE FROM stop_times WHERE trip_id NOT IN (SELECT trip_id FROM trips)")
    cursor.execute("DELETE FROM stops WHERE stop_id NOT IN (SELECT stop_id FROM stop_times) AND location_type = ''")
    cursor.execute("DELETE FROM stops WHERE stop_id NOT IN (SELECT parent_station FROM stops) AND location_type = '1'")
    cursor.execute("DELETE FROM calendar WHERE service_id NOT IN (SELECT service_id FROM trips)")
    cursor.execute("DELETE FROM calendar_dates WHERE service_id NOT IN (SELECT service_id FROM trips)")
    cursor.execute("DELETE FROM transfers WHERE from_stop_id NOT IN (SELECT stop_id FROM stops)")
    cursor.execute("DELETE FROM transfers WHERE to_stop_id NOT IN (SELECT stop_id FROM stops)")
    
    # update feed_start_date according to the existing data
    cursor.execute("SELECT MIN(feed_date) AS min_feed_date FROM (SELECT start_date AS feed_date FROM calendar UNION SELECT date AS feed_date FROM calendar_dates)")
    result = cursor.fetchone()
    
    cursor.execute("UPDATE feed_info SET feed_start_date = ?", (result['min_feed_date'], ))

    # close cursor and VACUUM whole database
    cursor.close()
    gateway.static_database._connection.commit()

    cursor = gateway.static_database._connection.cursor()
    cursor.execute("VACUUM")

    