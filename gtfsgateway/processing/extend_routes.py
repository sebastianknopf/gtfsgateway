def extend_routes(gateway):
    cursor = gateway._processing_database._connection.cursor()

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_color TEXT NOT NULL DEFAULT '4285F4'")
    except Exception as ex:
        pass

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_text_color TEXT NOT NULL DEFAULT 'FFFFFF'")
    except Exception as ex:
        pass

    df_filename = gateway._gateway_config['processing']['extend_routes']['datafile']['filename']
    df_columns = gateway._gateway_config['processing']['extend_routes']['datafile']['columns']
    df_delimiter = gateway._gateway_config['processing']['extend_routes']['datafile']['delimiter']
    df_quotechar = gateway._gateway_config['processing']['extend_routes']['datafile']['quotechar']

    df_content = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
    for rd in df_content:
        cursor.execute(
            "UPDATE routes SET route_long_name = ?, route_color = ?, route_text_color = ? WHERE route_short_name = ?",
            (
                rd['route_long_name'],
                rd['route_color'],
                rd['route_text_color'],
                rd['route_short_name']
            )
        )