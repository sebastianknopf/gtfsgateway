import csv
import os
import sqlite3

class StaticDatabase:

    def __init__(self, local_sqlite_file):
        self._connection = sqlite3.connect(local_sqlite_file)
        self._connection.row_factory = sqlite3.Row

    def _get_col_datatypes(self, csv_file):
        dr = csv.DictReader(csv_file)
        field_types = {}

        for entry in dr:
            fields_left = [f for f in dr.fieldnames if f not in field_types.keys()]
            if not fields_left: 
                break
            
            for field in fields_left:
                data = entry[field]

                if len(data) == 0:
                    continue

                if data.isdigit():
                    field_types[field] = "INTEGER"
                else:
                    field_types[field] = "TEXT"

        if len(fields_left) > 0:
            for field in fields_left:
                field_types[field] = "TEXT"

        return field_types
    
    def import_csv_files(self, input_directory):
        for f in os.listdir(input_directory):
            if f.endswith('.txt'):
                table_name = f.replace('.txt', '')
                file_name = os.path.join(input_directory, f)

                self.import_csv_file(file_name, table_name)

    def import_csv_file(self, input_file, table_name):
        with open(input_file, mode='r', encoding='utf-8') as csv_file:
            dt = self._get_col_datatypes(csv_file)

            cursor = self._connection.cursor()

            # generate create statement for database table
            csv_file.seek(0)
            csv_reader = csv.DictReader(csv_file)

            fields = csv_reader.fieldnames
            cols = []
            for f in fields:
                cols.append(f"{f} {dt[f]}")

            stmt = f"CREATE TABLE IF NOT EXISTS {table_name}  ({','.join(cols)})"
            cursor.execute(stmt)

            # generate insert statement for data
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')

            stmt = f"INSERT INTO {table_name} VALUES ({','.join('?' * len(cols))});"

            next(csv_reader)
            cursor.executemany(stmt, csv_reader)

            self._connection.commit()

    def export_csv_files(self, output_directory):
        cursor = self._connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        for tbl in cursor.fetchall():
            self.export_csv_file(
                tbl[0],
                os.path.join(output_directory, f"{tbl[0]}.txt")
            )

        cursor.close()

    def export_csv_file(self, table_name, output_filename):
        cursor = self._connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")

        columns = [col[0] for col in cursor.description]
        results = list()
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        cursor.close()

        if len(results) > 0:
            with open(output_filename, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=columns, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writeheader()

                for row in results:
                    csv_writer.writerow(row)

    def get_route_base_info(self):
        cursor = self._connection.cursor()
        cursor.execute("SELECT route_id, route_short_name FROM routes;")

        return cursor.fetchall()

    def close(self):
        self._connection.close()
