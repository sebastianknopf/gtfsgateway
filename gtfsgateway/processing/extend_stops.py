import logging

def extend_stops(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    df_filename = params['datafile']['filename']
    df_columns = params['datafile']['columns']
    df_delimiter = params['datafile']['delimiter']
    df_quotechar = params['datafile']['quotechar']

    # run postprocessing using external data file
    df_content = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
    for rd in df_content:

        stop_id = rd['stop_id']
        stop_lat = rd['stop_lat']
        stop_lon = rd['stop_lon']
        
        stop_lat = stop_lat.replace(',', '.')
        stop_lon = stop_lon.replace(',', '.')

        cursor.execute(
            "UPDATE stops SET stop_lat = ?, stop_lon = ? WHERE (location_type = '' OR location_type = '0') AND stop_id = ?",
            (
                stop_lat,
                stop_lon,
                stop_id
            )
        )
        
    # optimize location of parent stations according to their stops
    cursor.execute("SELECT * FROM stops WHERE location_type = '1'")
    stations = cursor.fetchall()
    
    for station in stations:
    
        logging.info(f"updating station {station['stop_id']}")
    
        stop_lats = list()
        stop_lons = list()
        
        cursor.execute(
            "SELECT * FROM stops WHERE (location_type = '' OR location_type = '0') AND parent_station = ?",
            (
                station['stop_id'],
            )
        )
        
        stops = cursor.fetchall()
 
        for stop in stops:
            stop_lats.append(float(stop['stop_lat']))
            stop_lons.append(float(stop['stop_lon']))
            
        stop_lat = sum(stop_lats) / len(stop_lats)
        stop_lon = sum(stop_lons) / len(stop_lons)
        
        cursor.execute(
            "UPDATE stops SET stop_lat = ?, stop_lon = ? WHERE location_type = '1' AND stop_id = ?",
            (
                stop_lat,
                stop_lon,
                station['stop_id']
            )
        )
        
