def remove_shapes(static_database):
    cursor = static_database.get_connection().cursor()

    cursor.execute("DELETE FROM shapes")
    cursor.execute("UPDATE trips SET shape_id = ''")
    cursor.execute("UPDATE stop_times SET shape_dist_traveled = ''")

    cursor.close()