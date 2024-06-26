def remove_shapes(gateway):
    cursor = gateway.static_database._connection.cursor()

    cursor.execute("DELETE FROM shapes")
    cursor.execute("UPDATE trips SET shape_id = ''")
    cursor.execute("UPDATE stop_times SET shape_dist_traveled = ''")

    cursor.close()