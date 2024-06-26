app = dict(
    data_directory = 'data',
    tmp_directory = 'tmp',
    bin_directory = 'bin',
    app_directory = 'app',
    processing = dict(
        functions = [
            'remove_routes',
            'remove_shapes',
            'extend_feed_info',
            'extend_routes',
            'cleanup'
        ]
    ),
    staging_filename = 'gtfsgateway-staging.db3',
    staging_backup_filename = 'gtfsgateway-staging.bak',
    static_filename = 'gtfsgateway-static.db3',
    static_feed_filename = 'gtfsgateway-feed.zip'
)