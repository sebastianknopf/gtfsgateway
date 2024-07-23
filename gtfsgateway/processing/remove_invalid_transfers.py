import logging

from math import radians, cos, sin, asin, sqrt

def remove_invalid_transfers(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    cursor.execute("SELECT * FROM transfers")
    
    transfers = cursor.fetchall()
    for transfer in transfers:
        
        if transfer['transfer_type'] == 2:
            from_stop_position = _get_stop_position_by_id(gateway, transfer['from_stop_id'])
            to_stop_position = _get_stop_position_by_id(gateway, transfer['to_stop_id'])
            from_to_min_seconds = transfer['min_transfer_time']
            
            if from_to_min_seconds == 0:
                from_to_min_seconds = 59
            
            from_to_distance = _haversine(from_stop_position, to_stop_position)
            from_to_speed = from_to_distance / from_to_min_seconds
            
            if from_to_speed > 4:
                logging.info(f"removing invalid transfer from {transfer['from_stop_id']} to {transfer['to_stop_id']} (type {transfer['transfer_type']}, {from_to_distance} meters in {from_to_min_seconds} seconds)")
                
                cursor.execute("DELETE FROM transfers WHERE from_stop_id = ? AND to_stop_id = ?", 
                    (
                        transfer['from_stop_id'],
                        transfer['to_stop_id']
                    )
                )
            

    cursor.close()
    
def _get_stop_position_by_id(gateway, stop_id):
    cursor = gateway.static_database._connection.cursor()
    cursor.execute("SELECT stop_lat, stop_lon FROM stops WHERE stop_id = ?", (stop_id, ))
    
    stop = cursor.fetchone()
    return (float(stop['stop_lat']), float(stop['stop_lon']))
    
def _haversine(pos1, pos2):
    lon1, lat1, lon2, lat2 = map(radians, [pos1[1], pos1[0], pos2[1], pos2[0]])

    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a)) 
    
    r = 6371
    return c * r * 1000