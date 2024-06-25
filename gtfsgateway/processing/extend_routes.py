def extend_routes(static_database, route_data):
    cursor = static_database.get_connection().cursor()

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_color TEXT NOT NULL DEFAULT '4285F4'")
    except Exception as ex:
        pass

    try:
        cursor.execute("ALTER TABLE routes ADD COLUMN route_text_color TEXT NOT NULL DEFAULT 'FFFFFF'")
    except Exception as ex:
        pass

    for rd in route_data:
        cursor.execute(
            "UPDATE routes SET route_color = ?, route_text_color = ? WHERE route_short_name = ?",
            (
                rd['route_color'],
                rd['route_text_color'],
                rd['route_short_name']
            )
        )