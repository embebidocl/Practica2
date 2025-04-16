# https://unicode.org/emoji/charts/full-emoji-list.html ✅(1540)⚠️(1430)⏳(990)📦(1299)
# https://elcodigoascii.com.ar
# Matias Rivera Devia (20.654.829-0)
# Alexis Zamora Bernal (18.785.368-0)

import serial                   # Importa la biblioteca para manejar comunicación serial
import time                     # Importa time para las esperas
import serial.tools.list_ports  # Importa submódulo de pyserial (no se importa automaticamente con pyserial)

class Ardu:
    def __init__(self, port: str = None, bauds: int = None, timeout: float = 1.0): # Constructor de la clase
        self.port = port            # Puerto serial (Ej: COM3)
        self.bauds = bauds          # Tasa de baudios (velocidad)
        self.timeout = timeout      # Tiempo de espera para lectura (segundos)
        self.serial = None          # Objeto que representa la conexión serial

    def open(self): # Método para abrir la conexión al puerto serial
        try:
            self.serial = serial.Serial(self.port, self.bauds, timeout=self.timeout) # Intenta abrir el puerto serial con los parámetros actuales
            print(f"✅ Conectado a {self.port} a {self.bauds} baudios.") # Muestra por pantalla el puerto y la tasa de baudios

        except Exception as e: # Manejo de errores
            print("⚠️ Error al abrir el puerto serial:", e)
            self.serial = None

    def detectSerialPort(self): # Método para detectar el puerto serial
        print("⏳ Buscando puertos seriales disponibles")
        ports = serial.tools.list_ports.comports() # lista de puertos disponibles
        for port in ports: # Recorre los puertos seriales disponibles en el sistema y los analiza uno por uno
            if "Arduino" in port.description or "CH340" in port.description:
                """
                Buscara y seleccionara el puerto con Arduino o CH340 en la descripción del dispositivo.
                Nota: Preferimos dejar el programa con esta selección automática del puerto, ya que, al probar el programa en diferentes PC 
                cambiaba el puerto (p.EJ: COM3 al COM5) y la idea no es modificar el programa cada vez que se conecte a una nueva máquina
                """
                self.port = port.device # guarda el puerto detectado en el atributo del objeto
                print(f"✅ Puerto detectado automáticamente: {port.device} - {port.description}") # imprime por pantalla el puerto seleccionado
                return port.device # Devuelve el puerto que se va utilizar
        print("⚠️ No se encontró un puerto con un dispositivo Arduino") # En caso de NO detección
        return None # Método para detectar el puerto serial
    
    def detectBaudRate(self): # Método para detecta la tasa de baudios
        print("⏳ Detectando baudios...")
        commonBaudRates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]  # Lista de baudios para probar

        for baud in commonBaudRates: # Recorre los baudios en la lista
            try:
                self.serial = serial.Serial(self.port, baud, timeout=1.0) # Abre la conexión con el puerto serial usando los parametros obtenidos
                print(f"⏳ Probando {baud} baudios") # imprime por pantalla los baudios que se estan probando de la lista

                buffer = "" # Acumula caracteres ASCII hasta formar un byte hexadecimal (p.Ej: "7E")
                tempData = [] # Lista temporal para almacenar los bytes convertidos
                startTime = time.time() # Guarda el tiempo inicial para medir 2 segundos de prueba

                while time.time() - startTime < 2: # Mientras no hayan pasado más de dos segundos:
                    if self.serial.in_waiting: # Verifica si hay datos disponibles en el puerto
                        char = self.serial.read().decode("ascii", errors="ignore") # Se lee un carácter ASCII
                        
                        if char == ' ': # Si hay un espacio se considera un byte terminado
                            if len(buffer) == 2: # Si hay dos caracteres acumulados (un byte hexadecimal p.Ej: 7E)
                                try:
                                    byte = int(buffer, 16) # Convierte el texto hexadecimal a entero
                                    tempData.append(byte) # Lo agrega a la lista temporal

                                    if len(tempData) == 8: # Cuando hay 8 bytes acumulados, se analiza como posible trama
                                        if tempData[0] == 0x7E and tempData[-1] == 0x7E: # Verifica que la trama empiece y termine con 0x7E
                                            crcCalc = self.crc16CcittFalse(tempData[1:5]) # Calcula el CRC de los 4 bytes centrales (tipo, id, query, dato)
                                            crcReceived = (tempData[5] << 8) | tempData[6] # Reconstruye el CRC recibido desde los bytes 5 y 6

                                            if crcCalc == crcReceived: # Si el CRC calculado y el recibido coinciden corresponde a la velocidad correcta (baudios)
                                                print(f"✅ Tasa de baudios detecteda: {baud}")
                                                self.bauds = baud # Guarda la velocidad
                                                self.serial.close() # Cierra la conexión serial
                                                return baud # Devuelve la velocidad detectada (baud)
                                        tempData = [] # Si no era una trama válida, reinicia la lista temporal
                                except ValueError:
                                    pass # Si el byte no era valor hexadecimal válido es ignorado
                            buffer = "" # Reinicia el buffer de caracteres
                        else:
                            buffer += char # Acumula los caracteres que forman el byte

                self.serial.close() # Si no se detecto trama valida en 2 segundos se cierra la conexión

            except Exception as e: # Manejo de errores
                print(f"⚠️ Error de lectura {baud} baudios: {e}")

        print("⚠️ No se pudo detectar una tasa de baudios")
        return None # Devuelve None para indicar que fallo la conexión de baudios

    def connect(self): # Método que automatiza la conexión con el arduino (detectando puerto y tasa de baudios) y empieza a leer los datos enviados por el arduino
        if not self.detectSerialPort(): # Método para detectar el puerto automáticamente, en caso de NO detectarlo entrara al if y lo pedira de forma manual al usuario
            print("⚠️ No se pudo detectar el puerto serial automáticamente")
            manualPort = input("Ingresar el puerto manualmente (p.Ej: COM3 o /dev/ttyACM0):") # Solicita el puerto al usuario
            if manualPort.strip() == "": # En caso de que el usuario no ingrese ningun puerto (.strip() se utiliza para eliminar espacios en blanco)}
                print("⚠️ No se ingreso ningun puerto. Finalizando conexión...")
                return # Devuelve None, solo se quiere detener la ejecución del flujo
            self.port = manualPort # Atributo del objeto, contiene el valor del puerto ingresado por el usuario
        if self.detectBaudRate(): # Método para detectar la tasa de baudios
            self.open() # Se utiliza el método open para abrir la conexión del puerto serial
            self.readByte() # Se utiliza el método readByte para leer bytes del puerto serial, los transforma en datos útiles que se muestran por pantalla y valida su integridad usando CRC
        else:
            print("⚠️ Fallo en establecer comunicación con el Arduino")

    def crc16CcittFalse(self, bytesIn: list[int]) -> int: # Método que simula cómo el Arduino calcula el CRC, se utiliza para validar los datos recibidos
        crc = 0xFFFF # Valor inicial estándar para CRC-16/CCITT-False
        for byte in bytesIn: # Para cada byte de entrada
            crc ^= byte << 8 # Aplica una operación XOR con el CRC actual, para inyectar ese byte al proceso de calculo
            for _ in range(8): # Procesa 8 bits (1 Byte = 8 bits)
                if crc & 0x8000: # Verifica si el bit más significativo del CRC (el bit 15 de 16) es 1
                    crc = (crc << 1) ^ 0x1021 # Desplaza el CRC una posición a la izquierda y hace un XOR con el polinomio 0x1021, que es el divisor del algoritmo CRC.
                else:
                    crc <<= 1 # Solo se desplaza a la izquierda, sin aplicar el polinomio al igual que en una división (si no se puede dividir, solo se baja el siguiente bit)
                crc &= 0xFFFF # Se asegura que el CRC quede en 16 bits
        return crc # Devuelve el resultado final

    def readByte(self): # Método para leer datos del puerto serial byte por byte en formato hexadecimal, los convierte a números y los agrupa en tramas de 8 bytes
        if self.serial is None:
            print("⚠️ Puerto no conectado.")
            return # Termina la ejecución

        buffer = "" # Acumula caracteres hasta tener un byte completo
        try:
            while True:

                if self.serial.in_waiting: # Verifica si hay datos disponibles en el buffer de entrada              
                    char = self.serial.read().decode("ascii", errors="ignore") # Lee un solo carácter ASCII desde el puerto (como por ejemplo: "7", "E")
                    
                    if char == ' ': # Cuando llega un espacio "", significa que un byte terminó
                        if len(buffer) == 2: # Cada "palabra" es un byte en hexadecimal
                            
                            try:
                                byte = int(buffer, 16) # Convierte los 2 caracteres HEX (p.ej: 7E) a un valor entero
                                self.payloadByte(byte) # llama al metodo payloadByte: transforma bytes en datos útiles y valida su integridad usando CRC

                            except ValueError:
                                print(f"⚠️ Byte inválido: {buffer}")

                        buffer = "" # Limpia el buffer para el siguiente byte
                    else:
                        buffer += char # Acumula caracteres

        # Manejo de errores e interrupciones

        except KeyboardInterrupt:
            print("\nLectura interrumpida por el usuario.")
        except Exception as e:
            print("⚠️ Error durante la lectura:", e)
        finally:
            self.close() # Cierra la conexión serial

    def payloadByte(self, byte): # Método para convertir bytes recibidos por serial en datos útiles, legibles y validados
        """    
        1) Junta los bytes recibidos uno a uno hasta formar una trama de 8 bytes (verificando que empiece y termine con 0x7E)
        2) Extrae los datos importantes (tipo de dispositivo, id de dispositivo, valor del dato, etc)
        3) Calcula el CRC real con los datos del medio y lo compara con el recibido
        4) Imprime un mensaje legible, que indica el tipo de sensor, valor y si el checksum esta correcto o no
        """
        if not hasattr(self, 'payload'): # Crea el buffer si no existe
            self.payload = [] # Buffer

        self.payload.append(byte) # Agrega el nuevo byte al buffer

        # Se asegura de que se haya recibido solo 1 byte y que el primer byte de la trama sea 0x7E (inicio válido), sino descarta todo y empieza una nueva trama
        if len(self.payload) == 1 and self.payload[0] != 0x7E:
            self.payload = [] # Buffer
            return # Termina la ejecución

        # Si ya hay más de un byte, pero si no hay 0x7E al principio, también descartara la trama
        if len(self.payload) > 1 and self.payload[0] != 0x7E:
            print("Ignorado: no comienza con 0x7E")
            self.payload = [] # Buffer
            return # Termina la ejecución

        if len(self.payload) == 8: # Comprobando el largo de la trama (8 bytes, p.Ej: [0x7E, 0x02, 0x01, 0x11, 0x37, 0xAB, 0xCD, 0x7E])
            if self.payload[-1] == 0x7E: # Verifica que la trama termine en 0x7E

                #Extrae cada campo de la trama según el formato
                type = self.payload[1] # Extrae el tipo de dispositivo (0x0x1 para temperatura y 0x02 para la humedad)
                dispId = self.payload[2] # Obtiene el ID del dispositivo
                query = self.payload[3] # Guarda el código de consulta (query)
                data = self.payload[4] # Obtiene el valor del sensor (p.Ej: 25°C)
                crcHi = self.payload[5] # CRC: Parte alta del CRC (8 bits más significativos)
                crcLo = self.payload[6] # CRC: Parte baja del CRC (8 bits menos significativos)
                crcGet = (crcHi << 8) | crcLo # Reconstruye el CRC recibido como un solo número de 16 bits
                """
                crcHi << 8 -> mueve crcHi 8 bits a la izquierda
                | crcLo -> combina con la parte baja usando OR bit a bit
                """
                crcCalc = self.crc16CcittFalse(self.payload[1:5]) # Calcula CRC desde los 4 bytes centrales

                # Determinar tipo de dispositivo 0x01 para temperatura y 0x02 para humedad
                if type == 0x01:
                    typeStr = "01-temperatura" # Guarda descripción del sensor de temperatura
                    dataRead = f"temperatura: {data} °C" # Guarda un mensaje con un valor obtenido de temperatura (data=25)
                elif type == 0x02:
                    typeStr = "02-humedad" # Guarda descripción del sensor de humedad
                    dataRead = f"humedad relativa: {data} %" # Guarda un mensaje con un valor obtenido de humedad (data=55)
                else:
                    typeStr = f"{type:#04x}-desconocido" # Muestra un f-string con un valor hexadecimal del tipo de dispositivo para un dispositivo desconocido
                    dataRead = f"dato: {data}" # Muestra el dato que llego desde el dispositivo desconocido

                # Compara dos valores de CRC (recibido y calculado) si son iguales la trama es válida, si no coinciden la trama tiene errores
                statusCrc = "ok ✅" if crcGet == crcCalc else f"incorrecto ⚠️ (esperado: {crcCalc:#06x})"

                # Muestra por pantalla un resumen completo y legible de una trama recibida desde el arduino
                #print(f"📦 Dispositivo: {typeStr}, ID: {dispId:02d}, {dataRead}, checksum: {statusCrc}")

            else:
                print("⚠️ Trama inválida (sin delimitador final).") # se ejecuta cuando el ultimo byte no es 0x7E (delimitador incorrecto)

            self.payload = []  # Limpia el buffer payload, para recibir una nueva trama

    def close(self): # Método para cerrar el puerto serial si esta abierto
        if self.serial and self.serial.is_open: # Verifica que el objeto de conexión serial exista y que el puerto se encuentre abierto (ambas condiciones se deben cumplir)
            self.serial.close() # Cierra el puerto serial
            print("Puerto cerrado.") # Muestra por pantalla que el puerto se ha cerrado


    """
    CRC: Cyclic Redundancy Check (Verificación de redundancia cíclica) es un algoritmo que se usa para detectar errores en datos que se envían.
    
    p.Ej: el arduino envía:

    0x7E: Inicio
    0x01: Sensor de temperatura
    0x01: ID del sensor
    0x11: Código de query
    0x19: Dato
    CRC_H, CRC_L: Número CRC que calcula el Arduino
    0x7E: Fin
    
    Antes de envíar la trama el arduino calcula el CRC que depende de los datos del medio y ese número se adjunta 
    en la trama, luego, este programa en python recalcula el mismo número con los datos que recibio.

    Entonces, si el CRC coincide significa que los datos no fueron alterados y todo llego bien, por el contrario si el CRC NO coincide 
    significa que algunos datos cambiaron por un error en la transmisión.
    """