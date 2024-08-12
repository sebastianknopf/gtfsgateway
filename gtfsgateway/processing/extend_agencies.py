import logging

def extend_agencies(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    try:
        cursor.execute("ALTER TABLE agency ADD COLUMN agency_phone TEXT NOT NULL DEFAULT ''")
    except Exception as ex:
        pass

    try:
        cursor.execute("ALTER TABLE agency ADD COLUMN agency_email TEXT NOT NULL DEFAULT ''")
    except Exception as ex:
        pass

    df_filename = params['agency_datafile']['filename']
    df_columns = params['agency_datafile']['columns']
    df_delimiter = params['agency_datafile']['delimiter']
    df_quotechar = params['agency_datafile']['quotechar']
    
    df_agencies = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
    
    df_filename = params['routes_datafile']['filename']
    df_columns = params['routes_datafile']['columns']
    df_delimiter = params['routes_datafile']['delimiter']
    df_quotechar = params['routes_datafile']['quotechar']
    
    df_routes = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
        
    # delete from agencies
    cursor.execute("DELETE FROM agency")
    
    # build index from each route to its agency based on datafiles
    route_agency_index = dict()
    for route in df_routes:
        route_matched = False
        for agency in df_agencies:
            route_foreign_key = route['agency_foreign_key']
            route_foreign_key = route_foreign_key.split('-')[0]
            route_foreign_key = route_foreign_key.strip()
            
            if route_foreign_key == agency['agency_primary_key']:
                logging.info(f"matched route {route['route_short_name']} to {agency['agency_name']}")
                
                route_agency_index[route['route_short_name']] = agency['agency_number']
                
                route_matched = True
                break
                
        if not route_matched:
            logging.warn(f"could not find matching agency for route {route['route_short_name']}")
            
    # update all routes with their new added agency ID
    for route_short_name, agency_id in route_agency_index.items():
        cursor.execute("UPDATE routes SET agency_id = ? WHERE route_short_name = ?", 
            (
                agency_id, route_short_name
            )
        )
    
    # add all agencies which are referenced by the routes
    agency_ids = set(route_agency_index.values())
    for agency in df_agencies:
        if agency['agency_number'] in agency_ids:
            logging.info(f"adding agency {agency['agency_number']} ({agency['agency_name']})")
            
            cursor.execute(
                "INSERT INTO agency (agency_id, agency_name, agency_timezone, agency_url, agency_phone, agency_email) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    agency['agency_number'],
                    agency['agency_name'],
                    'Europe/Berlin',
                    agency['agency_url'],
                    agency['agency_phone'],
                    agency['agency_email']
                )
            )
        
