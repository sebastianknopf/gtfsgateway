def extend_stops(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    df_filename = params['datafile']['filename']
    df_columns = params['datafile']['columns']
    df_delimiter = params['datafile']['delimiter']
    df_quotechar = params['datafile']['quotechar']

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
