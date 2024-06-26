import datetime

def extend_feed_info(gateway):
    cursor = gateway._processing_database._connection.cursor()

    publisher_name = gateway._gateway_config['processing']['extend_feed_info']['publisher_name']
    publisher_url = gateway._gateway_config['processing']['extend_feed_info']['publisher_url']         

    cursor.execute(
        "UPDATE feed_info SET feed_publisher_name = ?, feed_publisher_url = ?, feed_version = ?",
        (
            publisher_name,
            publisher_url,
            datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        )       
    )