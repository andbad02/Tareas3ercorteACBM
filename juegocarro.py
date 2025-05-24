import tkinter as tk
import math
import time
import random

class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0
        self.last_output = 0

    def compute(self, error, dt):
        if dt <= 0:
            derivative = 0
        else:
            derivative = (error - self.prev_error) / dt * 0.7
        self.integral = max(-50, min(self.integral + error * dt, 50))
        raw_output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        smoothed_output = 0.3 * raw_output + 0.7 * self.last_output
        self.last_output = smoothed_output
        self.prev_error = error
        return smoothed_output

class LineFollowerCar:
    def __init__(self, canvas):
        self.canvas = canvas
        self.car_x = 150
        self.car_y = 500
        self.car_angle = 270
        self.speed = 1.5
        self.sensor_distance = 30
        self.sensor_offset = 20
        self.pid = PIDController(3, 0.00001, 0.00001)
        self.last_time = time.time()
        self.trail = []
        self.last_angle_change = 0
        self.max_turn_rate = 3.0
        self.stopping = False

        # Dibujar cuerpo, ruedas y sensores
        self.body = self.create_car_body()
        self.left_wheel = self.create_wheel()
        self.right_wheel = self.create_wheel()
        self.sensor_left = self.create_sensor()
        self.sensor_right = self.create_sensor()
        self.update_car()

    def create_car_body(self):
        return self.canvas.create_polygon([0,0,50,0,50,30,0,30], fill='#2E86C1', outline='#1B4F72', width=2)
    def create_wheel(self):
        return self.canvas.create_oval(0,0,12,12, fill='#2C3E50', outline='#1B2631')
    def create_sensor(self):
        return self.canvas.create_oval(0,0,10,10, fill='#E74C3C', outline='#922B21', width=2)

    def update_car(self):
        angle = math.radians(self.car_angle)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        # Body coords
        coords = [
            self.car_x + 15*cos_a - 10*sin_a, self.car_y + 15*sin_a + 10*cos_a,
            self.car_x + 15*cos_a + 10*sin_a, self.car_y + 15*sin_a - 10*cos_a,
            self.car_x - 15*cos_a + 10*sin_a, self.car_y - 15*sin_a - 10*cos_a,
            self.car_x - 15*cos_a - 10*sin_a, self.car_y - 15*sin_a + 10*cos_a
        ]
        self.canvas.coords(self.body, *coords)
        # Wheels
        self._update_wheel(self.left_wheel, -10, angle)
        self._update_wheel(self.right_wheel, 10, angle)
        # Sensors
        sl, sr = self.get_sensor_positions()
        self.canvas.coords(self.sensor_left, sl[0]-5, sl[1]-5, sl[0]+5, sl[1]+5)
        self.canvas.coords(self.sensor_right, sr[0]-5, sr[1]-5, sr[0]+5, sr[1]+5)

    def _update_wheel(self, wheel, offset, angle):
        x = self.car_x + offset * math.sin(angle)
        y = self.car_y - offset * math.cos(angle)
        self.canvas.coords(wheel, x-6, y-6, x+6, y+6)

    def get_sensor_positions(self):
        a = math.radians(self.car_angle)
        fx = self.car_x + self.sensor_distance * math.cos(a)
        fy = self.car_y + self.sensor_distance * math.sin(a)
        ls = (fx - self.sensor_offset * math.sin(a), fy + self.sensor_offset * math.cos(a))
        rs = (fx + self.sensor_offset * math.sin(a), fy - self.sensor_offset * math.cos(a))
        return ls, rs

    def check_stop_bar(self, sl, sr):
        # Verificar si ambos sensores detectan la barra de parada
        left_stop = self.check_sensor_stop_bar(*sl)
        right_stop = self.check_sensor_stop_bar(*sr)
        return left_stop and right_stop

    def check_sensor_stop_bar(self, x, y):
        overlap = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        return stop_bar in overlap

    def move(self):
        now = time.time()
        dt = now - self.last_time if now - self.last_time > 0 else 1e-3
        self.last_time = now

        sl, sr = self.get_sensor_positions()
        sc = ((sl[0]+sr[0])/2, (sl[1]+sr[1])/2)
        
        # Verificar si el carro debe detenerse
        if self.check_stop_bar(sl, sr):
            self.stopping = True
            # Mostrar mensaje de parada
            self.canvas.create_text(self.car_x, self.car_y - 30, 
                                   text="¡DETENIDO!", 
                                   font=("Arial", 12, "bold"),
                                   fill="red")
            return
        
        # Si el carro está detenido, no seguir moviendo
        if self.stopping:
            return
            
        left_active = self.check_sensor(*sl)
        right_active = self.check_sensor(*sr)
        center_active = self.check_sensor(*sc)

        state = 'none'
        if left_active and right_active:
            state = 'both'
        elif left_active:
            state = 'left'
        elif right_active:
            state = 'right'
        elif center_active:
            state = 'center'

        # Control
        if state == 'none':
            self.speed = 0.8
            if time.time() - self.last_angle_change > 0.5:
                self.last_angle_change = time.time()
                self.car_angle += 2 if int(time.time()*2)%2==0 else -2
        else:
            self.speed = 1.5 if state == 'both' else 1.3 if state=='center' else 1.0
            # Error invertido para giros correctos
            if state == 'left': error = 3
            elif state == 'right': error = -3
            elif state == 'center': error = 0.5 * self.pid.prev_error
            else: error = 0
            steering = self.pid.compute(error, dt)
            steering = max(-self.max_turn_rate, min(steering, self.max_turn_rate))
            self.car_angle += steering

        rad = math.radians(self.car_angle)
        self.car_x = max(20, min(self.car_x + self.speed*math.cos(rad), 780))
        self.car_y = max(20, min(self.car_y + self.speed*math.sin(rad), 580))
        self.trail.append((self.car_x, self.car_y))
        if len(self.trail)>100: self.trail.pop(0)
        self.update_car()

    def check_sensor(self, x, y):
        overlap = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        return guide_line in overlap

# Función de pista con paradas
def create_track_path(stops):
    pts = []
    pts.append(stops[0])
    for p in stops[1:]: pts.append(p)
    pts.append(stops[0])
    return [coord for pt in pts for coord in pt]

# Ventana principal
global guide_line, stop_bar
window = tk.Tk()
window.title("Seguidor de Línea con Pista Extendida")
canvas = tk.Canvas(window, width=800, height=600)
canvas.pack()

# Definir paradas para formar una pista con curvas adicionales
stops = [
    (150, 500),   # Punto de inicio/fin (esquina inferior izquierda)
    (150, 400),   # Curva 1
    (300, 400),   # Curva 2
    (300, 300),   # Curva 3
    (150, 300),   # Curva 4
    (150, 200),   # Curva 5
    (450, 200),   # Curva 6
    (450, 350),   # Curva 7
    (550, 350),   # Curva 8
    (550, 100),   # Curva 9
    (650, 100),   # Curva 10
    (650, 450),   # Curva 11
    (400, 450),   # Curva 12
]

# Fondo y decoración
canvas.create_rectangle(0,0,800,600, fill='#7DCEA0', stipple='gray25')

# Pista base y línea guía
track = canvas.create_line(
    create_track_path(stops), fill='#566573', width=30,
    smooth=True, capstyle=tk.ROUND
)
guide_line = canvas.create_line(
    create_track_path(stops), fill='black', width=15,
    smooth=True, joinstyle=tk.ROUND, capstyle=tk.ROUND
)

# Dibujar estaciones
for i, (x,y) in enumerate(stops, start=1):
    canvas.create_oval(x-15, y-15, x+15, y+15,
                       fill='#F1C40F', outline='#B7950B', width=3)
    canvas.create_text(x, y, text=f"S{i}", font=("Arial",12,"bold"))

# Crear barra de parada en el punto final (primer punto)
s_end_x, s_end_y = stops[0]  # Posición de parada final
stop_bar = canvas.create_rectangle(s_end_x-40, s_end_y-5, s_end_x+40, s_end_y+5, 
                                 fill='black', outline='red', width=2)

# Inicializar carro
car = LineFollowerCar(canvas)
canvas.create_text(400, 30, text="Seguidor de Línea - Pista Extendida", font=("Arial",14,"bold"))

# Loop
def game_loop():
    car.move()
    if random.random()>0.5 and not car.stopping:
        canvas.create_oval(car.car_x-1, car.car_y-1,
                           car.car_x+1, car.car_y+1,
                           fill='#F39C12', outline='')
    window.after(30, game_loop)

game_loop()
window.mainloop()
