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

    df_filename = params['datafile']['filename']
    df_columns = params['datafile']['columns']
    df_delimiter = params['datafile']['delimiter']
    df_quotechar = params['datafile']['quotechar']
    
    df_content = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
        
    # optimize location of parent stations according to their stops
    cursor.execute("SELECT * FROM agency")
    agencies = cursor.fetchall()
    
    for agency in agencies:
    
        logging.info(f"updating agency {agency['agency_id']}")
    
        agency_updated = False
        for ad in df_content:
            if agency['agency_id'] == ad['agency_id']:
                cursor.execute(
                    "UPDATE agency SET agency_name = ?, agency_url = ?, agency_phone = ?, agency_email = ? WHERE agency_id = ?",
                    (
                        ad['agency_name'],
                        ad['agency_url'],
                        ad['agency_phone'],
                        ad['agency_email'],
                        agency['agency_id']
                    )
                )
                
                agency_updated = True
                
                break
                
        if not agency_updated:
            logging.warn(f"agency {agency['agency_id']} not found in datafile")
        
