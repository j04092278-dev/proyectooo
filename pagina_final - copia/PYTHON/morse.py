import serial
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from threading import Thread
import matplotlib.pyplot as plt
import sys

# Configuración serial
port = 'COM4'  # Cambiar al puerto correcto
baudrate = 9600

# Inicializa la conexión serial
ser = None
try:
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # Espera a que la conexión se establezca
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial: {e}", file=sys.stderr)
    ser = None
except Exception as e:
    print(f"Error inesperado: {e}", file=sys.stderr)
    ser = None

# Variables globales
send_times = []  # Tiempos de envío (mensaje, tiempo)
receive_times = []  # Tiempos de recepción

# Mensajes del sistema
MENSAJES = {
    "error_generico": "Error: Mensaje no reconocido. Vuelva a intentar.",
    "error_formato": "Error: Formato de mensaje incorrecto. Se esperaba 'mensaje,tiempo,unidad'",
    "envio_exitoso": "Mensaje enviado exitosamente",
    "conexion_exitosa": "Conexión establecida con Arduino",
    "conexion_fallida": "Error en la conexión con Arduino",
    "grafica_no_datos": "No hay suficientes datos para graficar. Envíe y reciba más mensajes primero."
}

# Configuración de colores
AZUL = '#1f77b4'
NARANJA = '#ff7f0e'
GRIS_CLARO = '#f0f0f0'
BLANCO = 'white'

class AplicacionSerial:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Comunicación Serial")
        self.root.configure(bg=GRIS_CLARO)
        
        # Crear frames para cada pantalla
        self.ventana_principal = tk.Frame(self.root, bg=GRIS_CLARO)
        self.ventana_menu = tk.Frame(self.root, bg=GRIS_CLARO)
        self.ventana_comunicacion = tk.Frame(self.root, bg=GRIS_CLARO)
        
        self.crear_ventana_principal()
        self.crear_ventana_menu()
        self.crear_ventana_comunicacion()
        
        # Mostrar ventana principal al inicio
        self.mostrar_ventana_principal()
        
        # Iniciar hilo para lectura serial
        if ser and ser.is_open:
            self.mostrar_respuesta("=== Sistema de Comunicación Serial ===\n", "blue")
            self.mostrar_respuesta(">> Listo para enviar y recibir mensajes\n\n", "blue")
            self.mostrar_estado_conexion(True)
            self.thread_lectura = Thread(target=self.leer_respuesta_automaticamente, daemon=True)
            self.thread_lectura.start()

    def mostrar_ventana_principal(self):
        self.ocultar_todas_ventanas()
        self.ventana_principal.pack(padx=10, pady=10)

    def mostrar_ventana_menu(self):
        self.ocultar_todas_ventanas()
        self.ventana_menu.pack(padx=10, pady=10)

    def mostrar_ventana_comunicacion(self):
        self.ocultar_todas_ventanas()
        self.ventana_comunicacion.pack(padx=10, pady=10)

    def ocultar_todas_ventanas(self):
        for ventana in [self.ventana_principal, self.ventana_menu, self.ventana_comunicacion]:
            ventana.pack_forget()

    def crear_ventana_principal(self):
        # Ventana de bienvenida
        tk.Label(
            self.ventana_principal, 
            text="Bienvenido al Sistema de Comunicación Serial", 
            font=("Arial", 16), 
            bg=GRIS_CLARO
        ).pack(pady=20)
        
        # Botones
        frame_botones = tk.Frame(self.ventana_principal, bg=GRIS_CLARO)
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones, 
            text="Menú Principal", 
            command=self.mostrar_ventana_menu,
            bg=AZUL,
            fg=BLANCO,
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=20)
        
        tk.Button(
            frame_botones, 
            text="Salir", 
            command=self.cerrar_aplicacion,
            bg=NARANJA,
            fg=BLANCO,
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        ).pack(side=tk.RIGHT, padx=20)

    def crear_ventana_menu(self):
        # Menú principal
        tk.Label(
            self.ventana_menu, 
            text="Menú Principal", 
            font=("Arial", 16), 
            bg=GRIS_CLARO
        ).pack(pady=20)
        
        # Botones del menú
        frame_botones = tk.Frame(self.ventana_menu, bg=GRIS_CLARO)
        frame_botones.pack(pady=10)
        
        tk.Button(
            frame_botones, 
            text="Comunicación Serial", 
            command=self.mostrar_ventana_comunicacion,
            bg=AZUL,
            fg=BLANCO,
            font=('Arial', 12),
            width=20,
            pady=10
        ).pack(pady=10)
        
        tk.Button(
            frame_botones, 
            text="Gráficas", 
            command=self.mostrar_grafica,
            bg=AZUL,
            fg=BLANCO,
            font=('Arial', 12),
            width=20,
            pady=10
        ).pack(pady=10)
        
        tk.Button(
            frame_botones, 
            text="Regresar", 
            command=self.mostrar_ventana_principal,
            bg=NARANJA,
            fg=BLANCO,
            font=('Arial', 12),
            width=20,
            pady=10
        ).pack(pady=10)

    def crear_ventana_comunicacion(self):
        # Frame principal
        frame_principal = tk.Frame(self.ventana_comunicacion, bg=GRIS_CLARO)
        frame_principal.pack(padx=10, pady=10)
        
        # Campo de entrada para enviar mensajes
        self.entrada_texto = tk.Entry(
            frame_principal, 
            width=50, 
            font=('Arial', 11), 
            bg='white', 
            fg='black'
        )
        self.entrada_texto.grid(row=0, column=0, padx=5, pady=5)
        
        # Botón para enviar mensajes
        tk.Button(
            frame_principal, 
            text="Enviar", 
            command=self.enviar_mensaje,
            bg=NARANJA,
            fg=BLANCO,
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            borderwidth=2
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Área de texto para mostrar respuestas
        self.area_respuestas = scrolledtext.ScrolledText(
            frame_principal, 
            width=70, 
            height=20, 
            font=('Consolas', 10),
            wrap=tk.WORD,
            bg='white',
            fg='black'
        )
        self.area_respuestas.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.area_respuestas.config(state=tk.DISABLED)
        
        # Frame para botones inferiores
        frame_botones = tk.Frame(frame_principal, bg=GRIS_CLARO)
        frame_botones.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Botones adicionales
        tk.Button(
            frame_botones, 
            text="Graficar", 
            command=self.mostrar_grafica,
            bg=AZUL,
            fg=BLANCO,
            font=('Arial', 9, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones, 
            text="Limpiar", 
            command=self.limpiar_consola,
            bg=AZUL,
            fg=BLANCO,
            font=('Arial', 9, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones, 
            text="Regresar", 
            command=self.mostrar_ventana_menu,
            bg=NARANJA,
            fg=BLANCO,
            font=('Arial', 9, 'bold')
        ).pack(side=tk.RIGHT, padx=5)

    def mostrar_estado_conexion(self, exito):
        estado = MENSAJES["conexion_exitosa"] if exito else MENSAJES["conexion_fallida"]
        self.mostrar_respuesta(f"Estado: {estado}\n")

    def enviar_mensaje(self):
        message = self.entrada_texto.get().strip()
        if message:
            try:
                send_time = time.time()
                ser.write((message + "\n").encode())
                send_times.append((message, send_time))
                self.entrada_texto.delete(0, tk.END)
                self.mostrar_respuesta(f"[ENVIADO] {message}\n", "blue")
                self.mostrar_respuesta(f"  > {MENSAJES['envio_exitoso']} a las {time.strftime('%H:%M:%S')}\n", "blue")
            except serial.SerialException as e:
                messagebox.showerror("Error de envío", f"No se pudo enviar el mensaje: {e}")
        else:
            messagebox.showwarning("Campo vacío", "Por favor ingrese un mensaje antes de enviar")

    def leer_respuesta_automaticamente(self):
        while ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    response = ser.readline().decode().strip()
                    receive_time = time.time()
                    
                    if not response:
                        continue
                    
                    if response == "ERROR":
                        self.mostrar_respuesta(f"[ERROR] {MENSAJES['error_generico']}\n", "red")
                        continue
                    
                    if "," in response:
                        parts = response.split(",")
                        if len(parts) == 3:
                            message, send_time_ms, unit = parts
                            if unit == "ms":
                                try:
                                    send_time = float(send_time_ms) / 1000
                                    
                                    # Buscar el mensaje correspondiente
                                    for i, (sent_msg, sent_time) in enumerate(send_times):
                                        if sent_msg == message:
                                            del send_times[i]
                                            break
                                    
                                    receive_times.append((send_time, receive_time))
                                    self.mostrar_respuesta(f"[RECIBIDO] {message}\n", "orange")
                                    self.mostrar_respuesta(f"  > Tiempo de procesamiento: {send_time_ms} ms\n", "orange")
                                    self.mostrar_respuesta(f"  > Recibido a las {time.strftime('%H:%M:%S')}\n", "orange")
                                except ValueError:
                                    self.mostrar_respuesta(f"[ERROR] {MENSAJES['error_formato']}: {response}\n", "red")
                            else:
                                self.mostrar_respuesta(f"[ERROR] Unidad de tiempo no reconocida: {unit}\n", "red")
                        else:
                            self.mostrar_respuesta(f"[ERROR] {MENSAJES['error_formato']}: {response}\n", "red")
                    else:
                        self.mostrar_respuesta(f"[RECIBIDO] {response}\n", "orange")
                        self.mostrar_respuesta(f"  > Recibido a las {time.strftime('%H:%M:%S')}\n", "orange")
                        
            except UnicodeDecodeError:
                self.mostrar_respuesta("[ERROR] No se pudo decodificar el mensaje recibido\n", "red")
            except Exception as e:
                self.mostrar_respuesta(f"[ERROR] Error inesperado: {str(e)}\n", "red")
                break

    def mostrar_respuesta(self, texto, color="black"):
        self.area_respuestas.config(state=tk.NORMAL)
        self.area_respuestas.tag_config("blue", foreground="blue")
        self.area_respuestas.tag_config("orange", foreground=NARANJA)
        self.area_respuestas.tag_config("red", foreground="red")
        self.area_respuestas.insert(tk.END, texto, color)
        self.area_respuestas.config(state=tk.DISABLED)
        self.area_respuestas.see(tk.END)

    def mostrar_grafica(self):
        if len(receive_times) < 2:
            messagebox.showwarning("Datos insuficientes", MENSAJES["grafica_no_datos"])
            return
        
        send_times_plot = [t[0] for t in receive_times]
        receive_times_plot = [t[1] for t in receive_times]
        delays = [recv - send for send, recv in receive_times]
        
        plt.figure(figsize=(12, 5))
        
        # Gráfico 1: Tiempos absolutos
        plt.subplot(1, 2, 1)
        plt.plot(send_times_plot, receive_times_plot, 'o-', color=AZUL)
        plt.xlabel('Tiempo de envío (s)')
        plt.ylabel('Tiempo de recepción (s)')
        plt.title('Tiempos absolutos de comunicación')
        plt.grid(True)
        
        # Gráfico 2: Retrasos
        plt.subplot(1, 2, 2)
        plt.plot(delays, '*-', color=NARANJA)
        plt.xlabel('Número de mensaje')
        plt.ylabel('Retraso (s)')
        plt.title('Retrasos en la comunicación')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

    def limpiar_consola(self):
        self.area_respuestas.config(state=tk.NORMAL)
        self.area_respuestas.delete(1.0, tk.END)
        self.area_respuestas.config(state=tk.DISABLED)
        self.mostrar_respuesta("-- Consola limpiada --\n", "blue")
        self.mostrar_respuesta(f"-- {time.strftime('%H:%M:%S')} --\n\n", "blue")

    def cerrar_aplicacion(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea salir?"):
            try:
                if ser and ser.is_open:
                    ser.close()
            except:
                pass
            finally:
                self.root.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AplicacionSerial(root)
        root.protocol("WM_DELETE_WINDOW", app.cerrar_aplicacion)
        root.mainloop()
    except Exception as e:
        print(f"Error en la aplicación: {e}", file=sys.stderr)
        if ser and ser.is_open:
            ser.close()