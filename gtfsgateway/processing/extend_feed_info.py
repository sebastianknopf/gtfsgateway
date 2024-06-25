import datetime

def extend_feed_info(static_database, publisher_name, publisher_url):
    cursor = static_database.get_connection().cursor()

    cursor.execute(
        "UPDATE feed_info SET feed_publisher_name = ?, feed_publisher_url = ?, feed_version = ?",
        (
            publisher_name,
            publisher_url,
            datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        )       
    )