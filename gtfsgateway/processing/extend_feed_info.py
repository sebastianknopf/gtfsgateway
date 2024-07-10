import datetime

def extend_feed_info(gateway, params):

    cursor = gateway.static_database._connection.cursor()

    try:
        cursor.execute("ALTER TABLE feed_info ADD COLUMN feed_contact_email TEXT NOT NULL DEFAULT ''")
    except Exception as ex:
        pass
        
    try:
        cursor.execute("ALTER TABLE feed_info ADD COLUMN feed_contact_url TEXT NOT NULL DEFAULT ''")
    except Exception as ex:
        pass

    publisher_name = params['publisher_name']
    publisher_url = params['publisher_url']
    contact_email = params['contact_email']
    contact_url = params['contact_url']

    cursor.execute(
        "UPDATE feed_info SET feed_publisher_name = ?, feed_publisher_url = ?, feed_version = ?, feed_contact_email = ?, feed_contact_url = ?",
        (
            publisher_name,
            publisher_url,
            datetime.datetime.today().strftime('%Y%m%d%H%M%S'),
            contact_email,
            contact_url
        )       
    )