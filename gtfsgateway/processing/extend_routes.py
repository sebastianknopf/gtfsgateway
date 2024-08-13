def extend_routes(gateway, params):
    cursor = gateway.static_database._connection.cursor()

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_color TEXT NOT NULL DEFAULT '4285F4'")
    except Exception as ex:
        pass

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_text_color TEXT NOT NULL DEFAULT 'FFFFFF'")
    except Exception as ex:
        pass
        
    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_url TEXT NOT NULL DEFAULT ''")
    except Exception as ex:
        pass

    df_filename = params['datafile']['filename']
    df_columns = params['datafile']['columns']
    df_delimiter = params['datafile']['delimiter']
    df_quotechar = params['datafile']['quotechar']

    df_content = gateway._load_processing_datafile(df_filename, df_columns, df_delimiter, df_quotechar)
    for rd in df_content:
        if rd['route_short_name'] == rd['route_short_name']:
            route_type = rd['route_type']
            route_color = rd['route_color']
            route_color = route_color.lstrip('#')
     
            if _calculate_luminance(route_color) >= 140:
                route_text_color = '000000'
            else:
                route_text_color = 'FFFFFF'
                
            route_url = rd['route_url']

            if not route_type == '':
                cursor.execute(
                    "UPDATE routes SET route_type = ?, route_long_name = ?, route_color = ?, route_text_color = ?, route_url = ? WHERE route_short_name = ?",
                    (
                        route_type,
                        rd['route_long_name'],
                        route_color,
                        route_text_color,
                        route_url,
                        rd['route_short_name']
                    )
                )
            else:
                cursor.execute(
                    "UPDATE routes SET route_long_name = ?, route_color = ?, route_text_color = ?, route_url = ? WHERE route_short_name = ?",
                    (
                        rd['route_long_name'],
                        route_color,
                        route_text_color,
                        route_url,
                        rd['route_short_name']
                    )
                )

def _calculate_luminance(hexcolor):
    rgb = tuple(int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))

    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722