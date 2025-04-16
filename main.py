# Matias Rivera Devia (20.654.829-0)
# Alexis Zamora Bernal (18.785.368-0)

from Ardu import Ardu               # Importa la clase Ardu desde el archivo ardu.py
import psycopg2                     # Librería para conectar con PostgreSQL
import time                         # Para pausas u operaciones temporizadas
import matplotlib.pyplot as plt     # Para plotear
import pandas as pd                 # Para las tablas
#import threading                    # Para ejecutar el menu en segundo plano

# Clase que administra la conexión a PostgreSQL
class DatabaseManager:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.connect()

    def connect(self):  # Abre conexión con la base de datos
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("✅ Conectado a la base de datos.")
        except Exception as e:
            print(f"⚠️ Error de conexión: {e}")

    def close(self):  # Cierra conexión con la base
        if self.conn:
            self.conn.close()
            print("🔒 Conexión cerrada.")

    # Crear (Create)
    def insertSensor(self, dispId, tipo, descripcion):  # Crea un nuevo sensor si no existe
        query = "INSERT INTO sensores (dispid, tipo, descripcion) VALUES (%s, %s, %s) RETURNING id;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (dispId, tipo, descripcion))
            self.conn.commit()
            return cursor.fetchone()[0]

    # Leer (Read)
    def getSensorByDispId(self, dispId):  # Busca un sensor por su dispId
        query = "SELECT id FROM sensores WHERE dispid = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (dispId,))
            return cursor.fetchone()

    # Crear (Create)        
    def insertLectura(self, sensorId, queryCode, valor, crcValido, rawFrame):  # Registra una lectura
        query = """
        INSERT INTO lecturas (sensor_id, query, valor, crc_valido, raw_frame)
        VALUES (%s, %s, %s, %s, %s);
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (sensorId, queryCode, valor, crcValido, rawFrame))
            self.conn.commit()

    # Leer (Read)
    def getLecturasConSensor(self): # CONSULTA RELACIONAL: trae lecturas unidas con sensores
        query = """
        SELECT 
            l.id AS lectura_id,
            s.dispid AS sensor_did,
            s.tipo,
            s.descripcion,
            l.valor,
            l.crc_valido,
            l.lectura_timestamp
        FROM lecturas l
        JOIN sensores s ON l.sensor_id = s.id
        ORDER BY l.lectura_timestamp ASC
        LIMIT 10;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    # Actualizar (Update)
    def updateSensorDescription(self, sensorId, nuevaDescripcion): # Modifica la descripción de un sensor existente

        query = "UPDATE sensores SET descripcion = %s WHERE id = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (nuevaDescripcion, sensorId))
            self.conn.commit()
            print(f"Descripción del sensor {sensorId} actualizada.")

    # Borrar (Delete)
    def deleteLectura(self, lecturaId): # Elimina una lectura especifica por ID

        query = "DELETE FROM lecturas WHERE id = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (lecturaId,))
            self.conn.commit()
            print(f"Lectura {lecturaId} eliminada.")



# Subclase que une lectura serial + base de datos
class ArduConDB(Ardu): 
    def __init__(self, dbManager):
        super().__init__()
        self.db = dbManager

    def payloadByte(self, byte):  # Procesa tramas de 8 bytes, extrae, valida e inserta
        if not hasattr(self, 'payload'):
            self.payload = []

        self.payload.append(byte)

        if len(self.payload) == 1 and self.payload[0] != 0x7E:
            self.payload = []
            return

        if len(self.payload) > 1 and self.payload[0] != 0x7E:
            self.payload = []
            return

        if len(self.payload) == 8:
            if self.payload[-1] == 0x7E:
                # Extrae los campos de la trama
                type = self.payload[1]
                dispId = self.payload[2]
                query = self.payload[3]
                data = self.payload[4]
                crcHi = self.payload[5]
                crcLo = self.payload[6]
                crcGet = (crcHi << 8) | crcLo
                crcCalc = self.crc16CcittFalse(self.payload[1:5])
                crcValido = crcGet == crcCalc
                raw = ' '.join(f"{b:02X}" for b in self.payload)

                # Determinar tipo de sensor
                if type == 0x01:
                    tipoStr = "temperatura"
                elif type == 0x02:
                    tipoStr = "humedad"
                else:
                    tipoStr = "desconocido"

                # Si el sensor no está, lo inserta
                sensor = self.db.getSensorByDispId(dispId)
                if not sensor:
                    sensorId = self.db.insertSensor(dispId, type, f"Sensor {tipoStr}")
                else:
                    sensorId = sensor[0]

                # Guarda la lectura
                self.db.insertLectura(sensorId, query, data, crcValido, raw)

                # Imprime por consola
                estado = "✅" if crcValido else "⚠️"
                print(f"📦 Dispositivo: {tipoStr}, ID: {dispId}, valor: {data}, CRC: {estado}")

            self.payload = []


# PROGRAMA PRINCIPAL
if __name__ == "__main__":
    db = DatabaseManager(
        host="192.168.1.94",  # IP del servidor PostgreSQL
        port=5432, # Puerto estandar de PostgreSQL
        database="postgres",  # Base de datos 
        user="postgres", # Credencial
        password="Admin.123" # Credencial
    )

    ardu = ArduConDB(db)

    try:
        ardu.connect()  # Inicia la lectura desde Arduino

        # CONSULTA RELACIONAL: muestra datos de sensores y sus lecturas
        print("\n Lecturas registradas con detalles del sensor:")
        lecturas = db.getLecturasConSensor()
        # Se crea un DataFrame para mostrarlo como tabla
        df = pd.DataFrame(lecturas, columns=["ID Lectura", "ID Sensor", "Tipo", "Descripción", "Valor", "CRC OK", "Fecha y Hora"])
        # Se muestra tabla en consola
        print(df.to_string(index=False))

        # Solo se grafican valores de sensores de temperatura
        valores = []
        fechas = []

        for l in reversed(lecturas):  # reversed para que muestre cronológicamente
            _, _, tipo, _, valor, _, timestamp = l
            if tipo == 1:  # tipo 1 = temperatura
                valores.append(valor)
                fechas.append(timestamp.strftime('%H:%M:%S'))
            if len(valores)>=10:
                break # Solo primeras 10 lecturas

        # se invierten las listas para graficar de lo más antiguo a lo más nuevo
        valores.reverse()
        fechas.reverse()

        plt.figure(figsize=(10, 5))
        plt.plot(fechas, valores, marker='o')
        plt.title("Primeras 10 Lecturas de Temperatura")
        plt.xlabel("Hora")
        plt.ylabel("Valor (°C)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(True)
        plt.show()  
    

    except KeyboardInterrupt:
        print("⚠️ Interrumpido por el usuario.")

    finally:
        ardu.close()
        db.close()
