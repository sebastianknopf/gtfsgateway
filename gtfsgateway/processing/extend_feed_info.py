import datetime

def extend_feed_info(gateway, params):

    cursor = gateway.static_database._connection.cursor()

    publisher_name = params['publisher_name']
    publisher_url = params['publisher_url']
    contact_email = params['contact_email']

    cursor.execute(
        "UPDATE feed_info SET feed_publisher_name = ?, feed_publisher_url = ?, feed_version = ?, feed_contact_email = ?",
        (
            publisher_name,
            publisher_url,
            datetime.datetime.today().strftime('%Y%m%d%H%M%S'),
            contact_email
        )       
    )