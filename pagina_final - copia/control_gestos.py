import cv2 
import mediapipe as mp 
import serial 
import time 
import numpy as np 
from matplotlib.backends.backend_agg import FigureCanvasAgg 
from matplotlib import pyplot as plt 
import pygame 
from pygame.locals import * 

# Configuración serial - cambiar COM según tu sistema 
SERIAL_PORT = 'COM3'  
BAUD_RATE = 9600 

try: 
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) 
    time.sleep(2)  # Espera para inicialización 
    print(f"Conexión establecida con Arduino en {SERIAL_PORT}") 
except serial.SerialException as e: 
    print(f"Error de conexión: {e}") 
    arduino = None 

# Configuración de MediaPipe Hands 
mp_hands = mp.solutions.hands 
mp_drawing = mp.solutions.drawing_utils 
mp_drawing_styles = mp.solutions.drawing_styles 

hands = mp_hands.Hands( 
    max_num_hands=1, 
    min_detection_confidence=0.8, 
    min_tracking_confidence=0.8 
) 

# Inicializar cámara 
cap = cv2.VideoCapture(0) 

if not cap.isOpened(): 
    print("Error al abrir la cámara") 
    exit() 

# Inicializar pygame para interfaz gráfica 
pygame.init() 
info = pygame.display.Info() 
screen_width, screen_height = info.current_w - 100, info.current_h - 100 
screen = pygame.display.set_mode((screen_width, screen_height)) 
pygame.display.set_caption("Control por Gestos - Sistema de Domótica") 

# Colores 
WHITE = (255, 255, 255) 
BLACK = (0, 0, 0) 
GREEN = (0, 255, 0) 
RED = (255, 0, 0) 
BLUE = (0, 0, 255) 
YELLOW = (255, 255, 0) 
ORANGE = (255, 165, 0) 

# Fuentes 
font_large = pygame.font.SysFont('Arial', 30) 
font_medium = pygame.font.SysFont('Arial', 24) 
font_small = pygame.font.SysFont('Arial', 18) 

# Mapeo de gestos a comandos 
GESTURE_COMMANDS = { 
    "00000": {"cmd": "ALL_OFF", "desc": "Puño cerrado - Apagar todo", "color": RED},           
    "11111": {"cmd": "LED_ON", "desc": "Mano abierta - Encender luces", "color": GREEN},            
    "01100": {"cmd": "FAN_ON", "desc": "Paz y amor - Ventilador ON", "color": BLUE},            
    "01111": {"cmd": "FAN_OFF", "desc": "Cuatro dedos - Ventilador OFF", "color": RED},      
    "10000": {"cmd": "BUZZER_ON", "desc": "Solo pulgar - Alarma sonora", "color": ORANGE},         
    "00111": {"cmd": "DOOR_OPEN", "desc": "Tres dedos - Abrir puerta", "color": GREEN},         
    "00001": {"cmd": "DOOR_CLOSE", "desc": "Solo meñique - Cerrar puerta", "color": RED},        
    "01000": {"cmd": "DOOR_SET_ANGLE=90", "desc": "Solo índice - Ángulo 90°", "color": YELLOW}, 
    "11000": {"cmd": "FAN_REVERSE", "desc": "Pulgar + índice - Reversa ventilador", "color": ORANGE} 
} 

# Estados adicionales para control progresivo 
GESTURE_CONTROL = { 
    "11111": {"action": "INCREASE", "target": "SERVO", "step": 5}, 
    "00000": {"action": "DECREASE", "target": "SERVO", "step": 5}, 
    "10101": {"action": "INCREASE", "target": "FAN", "step": 25}, 
    "01010": {"action": "DECREASE", "target": "FAN", "step": 25} 
} 

def count_fingers(hand_landmarks): 
    tips_ids = [4, 8, 12, 16, 20]  # Pulgar, índice, medio, anular, meñique 
    fingers = [] 
    
    # Detección pulgar (comparación eje X) 
    thumb_tip = hand_landmarks.landmark[tips_ids[0]] 
    thumb_dip = hand_landmarks.landmark[tips_ids[0]-1] 
    fingers.append(1 if thumb_tip.x < thumb_dip.x else 0) 
    
    # Detección otros dedos (comparación eje Y) 
    for id in range(1, 5): 
        tip = hand_landmarks.landmark[tips_ids[id]] 
        dip = hand_landmarks.landmark[tips_ids[id]-2] 
        fingers.append(1 if tip.y < dip.y else 0) 
    
    return "".join(map(str, fingers)) 

def send_command(cmd): 
    if arduino: 
        try: 
            arduino.write(f"{cmd}\n".encode()) 
            print(f"Comando enviado: {cmd}") 
            return True 
        except Exception as e: 
            print(f"Error enviando comando: {e}") 
            return False 
    else: 
        print(f"Simulando comando: {cmd}") 
        return True 

def draw_hand_graph(hand_landmarks, size=(300, 300)): 
    """Crea una gráfica de los puntos de la mano usando matplotlib""" 
    fig, ax = plt.subplots(figsize=(4, 4), facecolor='black') 
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1) 
    ax.set_xlim(0, 1) 
    ax.set_ylim(1, 0)  # Invertir eje Y para coincidir con imagen 
    ax.axis('off') 
    
    # Dibujar conexiones 
    connections = mp_hands.HAND_CONNECTIONS 
    for connection in connections: 
        start_idx = connection[0] 
        end_idx = connection[1] 
        start = hand_landmarks.landmark[start_idx] 
        end = hand_landmarks.landmark[end_idx] 
        ax.plot([start.x, end.x], [start.y, end.y], 'w-', linewidth=2) 
    
    # Dibujar puntos 
    for landmark in hand_landmarks.landmark: 
        ax.plot(landmark.x, landmark.y, 'ro', markersize=5) 
    
    # Convertir a superficie pygame 
    canvas = FigureCanvasAgg(fig) 
    canvas.draw() 
    renderer = canvas.get_renderer() 
    raw_data = renderer.tostring_argb() 
    plt.close(fig) 
    
    # Cambiado de "RGB" a "ARGB" y ajustado el tamaño 
    size_pixels = (int(renderer.width), int(renderer.height)) 
    surf = pygame.image.fromstring(raw_data, size_pixels, "ARGB") 
    return pygame.transform.scale(surf, size) 

def draw_gesture_info(surface, finger_state, command, servo_angle, fan_speed): 
    """Dibuja información sobre el gesto detectado""" 
    # Fondo del panel de información 
    pygame.draw.rect(surface, (30, 30, 40), (0, 0, surface.get_width(), 120)) 
    
    # Texto de estado de dedos 
    gesture_data = GESTURE_COMMANDS.get(finger_state, {"desc": "Gestos no reconocido", "color": WHITE}) 
    fingers_text = font_large.render(f"Estado de dedos: {finger_state}", True, gesture_data["color"]) 
    surface.blit(fingers_text, (20, 20)) 
    
    # Descripción del gesto 
    gesture_text = font_medium.render(f"Gesto: {gesture_data['desc']}", True, WHITE) 
    surface.blit(gesture_text, (20, 55)) 
    
    # Comando actual 
    cmd_text = font_medium.render(f"Comando: {command if command else 'Ninguno'}", True, GREEN if command else RED) 
    surface.blit(cmd_text, (surface.get_width() - 400, 20)) 
    
    # Ángulo del servo 
    servo_text = font_medium.render(f"Ángulo puerta: {servo_angle}°", True, WHITE) 
    surface.blit(servo_text, (surface.get_width() - 400, 55)) 
    
    # Velocidad ventilador 
    fan_text = font_medium.render(f"Veloc. ventilador: {fan_speed}/255", True, WHITE) 
    surface.blit(fan_text, (surface.get_width() - 400, 85)) 

def draw_device_status(surface, devices): 
    """Dibuja el estado de los dispositivos""" 
    # Fondo del panel de estado 
    pygame.draw.rect(surface, (40, 40, 50), (0, surface.get_height() - 150, surface.get_width(), 150)) 
    
    # Título 
    status_title = font_large.render("Estado de Dispositivos:", True, YELLOW) 
    surface.blit(status_title, (20, surface.get_height() - 140)) 
    
    # Dispositivos 
    for i, device in enumerate(devices): 
        x_pos = 20 + (i * 250) 
        if x_pos < surface.get_width() - 200: 
            # Icono representativo 
            icon = font_large.render(device["icon"], True, device["color"]) 
            surface.blit(icon, (x_pos, surface.get_height() - 100)) 
            
            # Texto del estado 
            state_text = font_medium.render(device["state"], True, device["color"]) 
            surface.blit(state_text, (x_pos + 40, surface.get_height() - 100)) 
            
            # Barra de progreso para elementos con valores 
            if "value" in device: 
                pygame.draw.rect(surface, (70, 70, 80), (x_pos, surface.get_height() - 60, 200, 20)) 
                pygame.draw.rect(surface, device["color"], (x_pos, surface.get_height() - 60, int(200 * (device["value"]/device["max"])), 20)) 
                value_text = font_small.render(f"{device['value']}/{device['max']}", True, WHITE) 
                surface.blit(value_text, (x_pos + 80, surface.get_height() - 55)) 

def parse_status_message(message): 
    """Parsea el mensaje de estado del Arduino""" 
    if not message.startswith("status:"): 
        return None 
    
    status_data = {} 
    parts = message[7:].strip().split(",") 
    for part in parts: 
        key, value = part.split("=") 
        status_data[key] = value 
    
    return status_data 

prev_command = None 
servo_angle = 90  # Ángulo inicial del servo 
fan_speed = 0     # Velocidad inicial del ventilador 
clock = pygame.time.Clock() 
running = True 
last_status = {} 
gesture_active_time = 0 
current_gesture = None 

# Dispositivos iniciales 
devices = [ 
    {"name": "Luces", "state": "OFF", "color": RED, "icon": "💡", "cmd_on": "LED_ON", "cmd_off": "LED_OFF"}, 
    {"name": "Ventilador", "state": "OFF", "color": RED, "icon": "🌀", "value": 0, "max": 255, "cmd_on": "FAN_ON", "cmd_off": "FAN_OFF", "cmd_reverse": "FAN_REVERSE"}, 
    {"name": "Alarma", "state": "OFF", "color": RED, "icon": "🚨", "cmd_on": "BUZZER_ON"}, 
    {"name": "Puerta", "state": "90°", "color": BLUE, "icon": "🚪", "value": 90, "max": 180, "cmd_open": "DOOR_OPEN", "cmd_close": "DOOR_CLOSE"} 
] 

while running: 
    for event in pygame.event.get(): 
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): 
            running = False 
        elif event.type == KEYDOWN: 
            if event.key == K_1: 
                send_command("LED_ON") 
            elif event.key == K_2: 
                send_command("LED_OFF") 
            elif event.key == K_3: 
                send_command("FAN_ON") 
            elif event.key == K_4: 
                send_command("FAN_OFF") 
            elif event.key == K_5: 
                send_command("BUZZER_ON") 
            elif event.key == K_6: 
                send_command("DOOR_OPEN") 
            elif event.key == K_7: 
                send_command("DOOR_CLOSE") 
            elif event.key == K_0: 
                send_command("ALL_OFF") 
            elif event.key == K_r: 
                send_command("FAN_REVERSE") 

    # Leer estado del Arduino si hay datos disponibles 
    if arduino and arduino.in_waiting > 0: 
        try: 
            status_message = arduino.readline().decode().strip() 
            last_status = parse_status_message(status_message) or last_status 
            print(f"Estado recibido: {status_message}") 
        except Exception as e: 
            print(f"Error leyendo estado: {e}") 

    # Actualizar dispositivos basado en el último estado 
    if last_status: 
        for device in devices: 
            if device["name"] == "Luces": 
                device["state"] = "ON" if last_status.get("led", "") == "on" else "OFF" 
                device["color"] = GREEN if device["state"] == "ON" else RED 
            elif device["name"] == "Ventilador": 
                speed = int(last_status.get("fan", "0")) 
                device["value"] = speed 
                device["state"] = f"{speed}/255" 
                device["color"] = GREEN if speed > 0 else RED 
                if "fan_dir" in last_status: 
                    if last_status["fan_dir"] == "reverse": 
                        device["state"] += " (R)" 
            elif device["name"] == "Alarma": 
                device["state"] = "ON" if last_status.get("buzzer", "") == "on" else "OFF" 
                device["color"] = ORANGE if device["state"] == "ON" else RED 
            elif device["name"] == "Puerta": 
                angle = int(last_status.get("door", "90")) 
                device["value"] = angle 
                device["state"] = f"{angle}°" 
                servo_angle = angle 

    # Capturar frame de la cámara 
    ret, frame = cap.read() 
    if not ret: 
        continue 

    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    results = hands.process(rgb_frame) 

    command = None 
    finger_state = "-----" 
    hand_graph_surf = None 

    if results.multi_hand_landmarks: 
        for hand_landmarks in results.multi_hand_landmarks: 
            # Procesar gestos 
            finger_state = count_fingers(hand_landmarks) 
            gesture_info = GESTURE_COMMANDS.get(finger_state, {}) 
            command = gesture_info.get("cmd", None) 
            
            # Crear gráfico de la mano 
            try: 
                hand_graph_surf = draw_hand_graph(hand_landmarks) 
            except Exception as e: 
                print(f"Error al dibujar gráfico de mano: {e}") 
                hand_graph_surf = None 

            # Control progresivo con gestos especiales 
            control_action = GESTURE_CONTROL.get(finger_state, {}) 
            if control_action: 
                if current_gesture != finger_state: 
                    current_gesture = finger_state 
                    gesture_active_time = time.time() 
                
                # Aplicar acción continua si el gesto se mantiene 
                if time.time() - gesture_active_time > 0.5:  # Retardo antes de acción continua 
                    if control_action["target"] == "SERVO": 
                        step = control_action["step"] * (1 if control_action["action"] == "INCREASE" else -1) 
                        servo_angle = max(0, min(180, servo_angle + step)) 
                        command = f"DOOR_SET_ANGLE={servo_angle}" 
                    elif control_action["target"] == "FAN": 
                        step = control_action["step"] * (1 if control_action["action"] == "INCREASE" else -1) 
                        fan_speed = max(0, min(255, fan_speed + step)) 
                        command = f"FAN_SPEED={fan_speed}" 
            else: 
                current_gesture = None 

    # Envío de comandos con deduplicación 
    if command and command != prev_command: 
        if send_command(command): 
            prev_command = command 
            # Actualizar estado local inmediatamente para mejor feedback 
            if command == "LED_ON": 
                for device in devices: 
                    if device["name"] == "Luces": 
                        device["state"] = "ON" 
                        device["color"] = GREEN 
            elif command == "LED_OFF": 
                for device in devices: 
                    if device["name"] == "Luces": 
                        device["state"] = "OFF" 
                        device["color"] = RED 
            elif command == "FAN_ON": 
                for device in devices: 
                    if device["name"] == "Ventilador": 
                        device["state"] = "255/255" 
                        device["color"] = GREEN 
                        device["value"] = 255 
            elif command == "FAN_OFF": 
                for device in devices: 
                    if device["name"] == "Ventilador": 
                        device["state"] = "0/255" 
                        device["color"] = RED 
                        device["value"] = 0 
            elif command.startswith("FAN_SPEED="): 
                speed = int(command.split("=")[1]) 
                for device in devices: 
                    if device["name"] == "Ventilador": 
                        device["state"] = f"{speed}/255" 
                        device["color"] = GREEN if speed > 0 else RED 
                        device["value"] = speed 
            elif command == "FAN_REVERSE": 
                for device in devices: 
                    if device["name"] == "Ventilador": 
                        device["state"] = "255/255 (R)" 
                        device["color"] = ORANGE 
                        device["value"] = 255 
            elif command.startswith("DOOR_SET_ANGLE="): 
                angle = int(command.split("=")[1]) 
                for device in devices: 
                    if device["name"] == "Puerta": 
                        device["state"] = f"{angle}°" 
                        device["value"] = angle 
                        servo_angle = angle 

    # Convertir frame de OpenCV a Pygame 
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    frame = np.rot90(frame) 
    frame = pygame.surfarray.make_surface(frame) 
    frame = pygame.transform.scale(frame, (screen_width // 2, screen_height - 150)) 

    # Limpiar pantalla 
    screen.fill(BLACK) 

    # Dibujar frame de la cámara 
    screen.blit(frame, (20, 130)) 

    # Dibujar gráfico de la mano si está disponible 
    if hand_graph_surf: 
        screen.blit(hand_graph_surf, (screen_width // 2 + 40, 130)) 
    else: 
        no_hand_text = font_large.render("Muestra tu mano a la cámara", True, WHITE) 
        screen.blit(no_hand_text, (screen_width // 2 + 100, screen_height // 2)) 

    # Dibujar información de gestos 
    draw_gesture_info(screen, finger_state, command, servo_angle, fan_speed) 

    # Dibujar estado de dispositivos 
    draw_device_status(screen, devices) 

    # Dibujar ayuda de teclado 
    help_text = font_small.render("Teclas: 1=LED ON, 2=LED OFF, 3=FAN ON, 4=FAN OFF, 5=BUZZER, 6=OPEN, 7=CLOSE, 0=ALL OFF, R=REVERSE", True, WHITE) 
    screen.blit(help_text, (20, screen_height - 30)) 

    # Actualizar pantalla 
    pygame.display.flip() 
    clock.tick(30) 

# Liberar recursos 
hands.close() 
cap.release() 
pygame.quit() 
if arduino: 
    arduino.close()