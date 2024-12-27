from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import math
import sys

# Constants
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
ROBOT_ARM_START_X = 0
ROBOT_ARM_START_Y = -200

# Game State

robot_arm_position = [ROBOT_ARM_START_X, ROBOT_ARM_START_Y]
score = 0
hearts = 6
game_over = False
paused = False
treasures = []
debris = []
# Collision counters
sticky_collision_count = 0
moving_collision_count = 0

explosive_collisions = 0


# Missed treasures counter
missed_treasures = 0
# Constants for robotic arm speed
DEFAULT_SPEED = 20
SLOW_SPEED = 5


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2, -
               WINDOW_HEIGHT // 2, WINDOW_HEIGHT // 2)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


# Drawing utilities
def draw_point(x, y):
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def draw_line(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()


def draw_circle(radius, cx, cy):
    d = 1 - radius
    x = 0
    y = radius
    while x <= y:
        eight_way_symmetry(x, y, cx, cy)
        x += 1
        if d < 0:
            d += 2 * x + 1
        else:
            y -= 1
            d += 2 * (x - y) + 1


def eight_way_symmetry(x, y, cx, cy):
    points = [
        (cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
        (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x)
    ]
    glBegin(GL_POINTS)
    for px, py in points:
        glVertex2f(px, py)
    glEnd()
# Drawing robotic arm


def draw_robotic_arm(x, y):
    # Semicircular Top (open upwards)
    for angle in range(180, 361):  # Angle range for an open upward semicircle
        rad = math.radians(angle)
        cx = x + 40 * math.cos(rad)
        cy = y + 40 * math.sin(rad)
        draw_point(cx, cy)

    # Rectangle Base
    for i in range(-20, 21):  # Width of the rectangle
        for j in range(-60, -20):  # Height of the rectangle, positioned below the semicircle
            draw_point(x + i, y + j)


# Keyboard movement
# Slow down robotic arm
def move_robot_arm(key, x, y):
    global robot_arm_position, robot_arm_speed
    step = robot_arm_speed
    if key == b'\x1b':
        sys.exit()
    elif key == b'a':
        robot_arm_position[0] += step
        robot_arm_position[1] += step
    elif key == b'w':
        robot_arm_position[0] -= step
        robot_arm_position[1] += step
    elif key == b'd':
        robot_arm_position[0] -= step
        robot_arm_position[1] -= step
    elif key == b'x':
        robot_arm_position[0] += step
        robot_arm_position[1] -= step
    glutPostRedisplay()
    # elif key == b'\xe0':  # Arrow keys
    #     if x == 0: robot_arm_position[0] += step
    #     if x == -1: robot_arm_position[0] -= step
    #     if y == 0: robot_arm_position[1] += step
    #     if y == -1: robot_arm_position[1] -= step
    glutPostRedisplay()


def special_keys(key, x, y):
    global robot_arm_position, robot_arm_speed
    step = robot_arm_speed  # Use the current robotic arm speed

    # Handling arrow keys
    if key == GLUT_KEY_LEFT:  # Move left
        robot_arm_position[0] -= step
    elif key == GLUT_KEY_RIGHT:  # Move right
        robot_arm_position[0] += step
    elif key == GLUT_KEY_UP:  # Move up
        robot_arm_position[1] += step
    elif key == GLUT_KEY_DOWN:  # Move down
        robot_arm_position[1] -= step

    glutPostRedisplay()


# Constants for treasures and debris
TREASURE_RADIUS = 15
DEBRIS_RADIUS = 10
TREASURE_SPEED = 0.5
DEBRIS_SPEED = 1
robot_arm_speed = DEFAULT_SPEED


# Initializing treasures and debris
# Updated debris initialization
def initialize_objects():
    global treasures, debris, shields
    # Treasures
    treasures = [{'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
                  'y': random.randint(0, WINDOW_HEIGHT // 2),
                  'radius': TREASURE_RADIUS,
                  'shrinking': random.choice([True, False]),
                  'expanding': True} for _ in range(10)]

    # Debris
    debris = [
        {'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
         'y': random.randint(-WINDOW_HEIGHT // 2, WINDOW_HEIGHT // 2),
         'radius': DEBRIS_RADIUS,
         'type': 'sticky',
         'timer': random.randint(150, 300)} for _ in range(5)
    ] + [
        {'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
         'y': random.randint(-WINDOW_HEIGHT // 2, WINDOW_HEIGHT // 2),
         'radius': DEBRIS_RADIUS,
         'type': 'explosive',
         'timer': random.randint(150, 300)} for _ in range(3)
    ] + [
        {'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
         'y': random.randint(-WINDOW_HEIGHT // 2, WINDOW_HEIGHT // 2),
         'radius': DEBRIS_RADIUS,
         'type': 'moving',
         'dx': random.choice([-1, 1]) * 2.5,  # Horizontal speed
         'dy': random.choice([-1, 1]) * 2.5,
         'cooldown': 0} for _ in range(3)
    ]

    # Shields
    shields = [{'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
                'y': random.randint(-WINDOW_HEIGHT // 2, WINDOW_HEIGHT // 2),
                'radius': 20} for _ in range(2)]


# Drawing treasures and debris
def draw_treasures():
    for treasure in treasures:
        if treasure['shrinking']:
            # Darker green for shrinking/expanding treasures
            glColor3f(0.0, 0.8, 0.0)
        else:
            glColor3f(0.0, 1.0, 0.0)  # Bright green for normal treasures
        draw_circle(treasure['radius'], treasure['x'], treasure['y'])


def draw_triangle(x, y, size):
    glBegin(GL_LINES)
    # Top vertex to bottom-left vertex
    glVertex2f(x, y + size)  # Top vertex
    glVertex2f(x - size, y - size)  # Bottom-left vertex
    # Bottom-left vertex to bottom-right vertex
    glVertex2f(x - size, y - size)
    glVertex2f(x + size, y - size)  # Bottom-right vertex
    # Bottom-right vertex to top vertex
    glVertex2f(x + size, y - size)
    glVertex2f(x, y + size)  # Top vertex
    glEnd()


def draw_star(x, y, size):
    glBegin(GL_LINES)
    # Define 5 points of the star
    points = []
    for i in range(5):
        angle = math.radians(i * 72)  # 72 degrees
        points.append((x + size * math.cos(angle), y + size * math.sin(angle)))

    # Draw lines between alternating points
    for i in range(5):
        glVertex2f(points[i][0], points[i][1])  # Current point
        glVertex2f(points[(i + 2) % 5][0], points[(i + 2) % 5][1])
    glEnd()


def draw_debris():
    for debri in debris:
        if debri['type'] == 'sticky':
            glColor3f(1.0, 0.0, 0.0)  # Red color
            draw_triangle(debri['x'], debri['y'], DEBRIS_RADIUS)
        elif debri['type'] == 'explosive':
            glColor3f(1.0, 0.5, 0.0)  # Orange color
            draw_triangle(debri['x'], debri['y'],
                          DEBRIS_RADIUS * 2)  # Bigger triangle
        elif debri['type'] == 'moving':
            glColor3f(1.0, 0.0, 1.0)  # Pink color
            draw_triangle(debri['x'], debri['y'], DEBRIS_RADIUS)


# Update treasures and debris
def update_objects():
    global treasures, debris, shields, missed_treasures

    # Update treasures
    for treasure in list(treasures):
        treasure['y'] -= TREASURE_SPEED
        if treasure['shrinking']:
            if treasure['expanding']:
                treasure['radius'] += 0.2
                if treasure['radius'] >= TREASURE_RADIUS * 1.5:
                    treasure['expanding'] = False
            else:
                treasure['radius'] -= 0.2
                if treasure['radius'] <= TREASURE_RADIUS * 0.5:
                    treasure['expanding'] = True
        if treasure['y'] < -WINDOW_HEIGHT // 2:
            missed_treasures += 1
            print(f"Missed treasures: {missed_treasures}")
            decrease_heart()
            treasures.remove(treasure)

    # Update debris
    for debri in list(debris):

        if debri['type'] == 'moving' and debri['cooldown'] > 0:
            debri['cooldown'] -= 1

        elif debri['type'] == 'sticky':
            debri['timer'] -= 1
            if debri['timer'] <= 0:
                debri['x'] = random.randint(-WINDOW_WIDTH //
                                            2, WINDOW_WIDTH // 2)
                debri['y'] = random.randint(-WINDOW_HEIGHT //
                                            2, WINDOW_HEIGHT // 2)
                debri['timer'] = random.randint(50, 150)

        elif debri['type'] == 'explosive':
            debri['timer'] -= 1
            if debri['timer'] <= 0:
                debris.extend([
                    {'x': debri['x'] + random.randint(-20, 20),
                     'y': debri['y'] + random.randint(-20, 20),
                     'radius': DEBRIS_RADIUS // 2,
                     'type': 'sticky',
                     'timer': random.randint(50, 150)} for _ in range(3)
                ])
                debris.remove(debri)

        elif debri['type'] == 'moving':
            debri['x'] += debri['dx']
            debri['y'] += debri['dy']
            if debri['x'] > WINDOW_WIDTH // 2 or debri['x'] < -WINDOW_WIDTH // 2:
                debri['dx'] = -debri['dx']
            if debri['y'] > WINDOW_HEIGHT // 2 or debri['y'] < -WINDOW_HEIGHT // 2:
                debri['dy'] = -debri['dy']

    for shield in shields:
        shield['y'] -= TREASURE_SPEED
        if shield['y'] < -WINDOW_HEIGHT // 2:
            shield['y'] = WINDOW_HEIGHT // 2
            shield['x'] = random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2)

# Collision detection


def detect_collision(obj1, obj2, radius1, radius2):
    distance = math.sqrt((obj1[0] - obj2[0])**2 + (obj1[1] - obj2[1])**2)
    return distance < (radius1 + radius2)


def decrease_heart():
    global hearts, game_over
    if hearts > 0:
        hearts -= 1
        print(f"Hearts: {hearts}")
    if hearts == 0 and not game_over:
        game_over = True
        print("Game Over!")


def check_collisions():
    global score, hearts, treasures, debris, robot_arm_position, robot_arm_speed
    global sticky_collision_count  # Explicitly mark it as global
    global explosive_collisions, missed_treasures
    global moving_collision_count

    # Check collisions with treasures
    for treasure in list(treasures):
        if detect_collision(robot_arm_position, (treasure['x'], treasure['y']), 20, treasure['radius']):
            treasures.remove(treasure)
            missed_treasures = 0  # Reset missed treasures counter
            if treasure['shrinking']:
                score += 2
                print("Collected a shrinking treasure! +2 points")
            else:
                score += 1
                print("Collected a normal treasure! +1 point")
            print(f"Score: {score}")
    # Check collisions with debris
    for debri in list(debris):
        if detect_collision(robot_arm_position, (debri['x'], debri['y']), 40, debri['radius']):
            if debri['type'] == 'moving' and debri['cooldown'] == 0:
                moving_collision_count += 1
                debri['cooldown'] = 10
                print(f"Moving debris collisions: {moving_collision_count}")

                if moving_collision_count == 2:
                    decrease_heart()
                    moving_collision_count = 0
        elif detect_collision(robot_arm_position, (debri['x'], debri['y']), 40, debri['radius']):
            if debri['type'] == 'sticky':
                sticky_collision_count += 1
                robot_arm_speed = SLOW_SPEED
                print(f"Sticky collisions: {sticky_collision_count}")

                # Check if sticky collisions reach 2
                if sticky_collision_count == 2:
                    decrease_heart()  # Decrease heart count
                    sticky_collision_count = 0
            elif debri['type'] == 'explosive':

                game_over = True
                print("Game Over!")
                return
            elif debri['type'] == 'moving':
                moving_collision_count += 1
                print(f"Moving debris collisions: {moving_collision_count}")

                # Check if moving collisions reach 2
                if moving_collision_count == 2:
                    decrease_heart()
                    moving_collision_count = 0
    robot_arm_speed = DEFAULT_SPEED


# Update function
def update_scene():
    if not paused and not game_over:
        update_objects()
        check_collisions()
    glutPostRedisplay()


# UI Button Constants
BUTTON_WIDTH = 60
BUTTON_HEIGHT = 30

# Drawing buttons


def draw_buttons():
    # Restart button (Left arrow)
    glColor3f(0.0, 1.0, 0.0)
    draw_line(-WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT // 2 - 40, -
              WINDOW_WIDTH // 2 + 80, WINDOW_HEIGHT // 2 - 40)
    draw_line(-WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT // 2 - 40, -
              WINDOW_WIDTH // 2 + 50, WINDOW_HEIGHT // 2 - 60)

    # Play/Pause button
    glColor3f(1.0, 1.0, 0.0)
    if paused:
        draw_line(-20, WINDOW_HEIGHT // 2 - 40, 20, WINDOW_HEIGHT // 2 - 40)
        draw_line(0, WINDOW_HEIGHT // 2 - 60, 0, WINDOW_HEIGHT // 2 - 20)
    else:
        draw_line(-10, WINDOW_HEIGHT // 2 - 60, 10, WINDOW_HEIGHT // 2 - 60)
        draw_line(-10, WINDOW_HEIGHT // 2 - 20, 10, WINDOW_HEIGHT // 2 - 20)

    # Exit button (Cross)
    glColor3f(1.0, 0.0, 0.0)
    draw_line(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 20,
              WINDOW_WIDTH // 2 - 20, WINDOW_HEIGHT // 2 - 60)
    draw_line(WINDOW_WIDTH // 2 - 20, WINDOW_HEIGHT // 2 - 20,
              WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 - 60)


def mouse_input(button, state, x, y):
    global paused, game_over
    mapped_x = x - (WINDOW_WIDTH // 2)
    mapped_y = (WINDOW_HEIGHT // 2) - y

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Restart button logic
        if -WINDOW_WIDTH // 2 + 20 <= mapped_x <= -WINDOW_WIDTH // 2 + 80 and \
           WINDOW_HEIGHT // 2 - 60 <= mapped_y <= WINDOW_HEIGHT // 2 - 40:
            restart_game()

        # Play/Pause button logic
        elif -20 <= mapped_x <= 20 and WINDOW_HEIGHT // 2 - 60 <= mapped_y <= WINDOW_HEIGHT // 2 - 20:
            paused = not paused

        # Exit button logic
        elif WINDOW_WIDTH // 2 - 80 <= mapped_x <= WINDOW_WIDTH // 2 - 20 and \
                WINDOW_HEIGHT // 2 - 60 <= mapped_y <= WINDOW_HEIGHT // 2 - 20:
            print("Exiting game...")
            glutLeaveMainLoop()


# Advanced Mechanics Constants
SHIELD_DURATION = 200
HEART_RADIUS = 15

# Additional game state
shields = []
hearts_collected = 0
shield_active = False
shield_timer = 0

# Adding Shields and Hearts


def initialize_advanced_objects():
    global shields
    shields = [{'x': random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
                'y': random.randint(0, WINDOW_HEIGHT // 2),
                'radius': 15} for _ in range(2)]

# Drawing Shields and Hearts


def draw_shields():
    glColor3f(0.0, 0.5, 1.0)  # Blue color for shields
    for shield in shields:
        draw_star(shield['x'], shield['y'], shield['radius'])


def update_shields():
    global shields, shield_active, shield_timer
    for shield in shields:
        shield['y'] -= TREASURE_SPEED
        if shield['y'] < -WINDOW_HEIGHT // 2:
            shield['y'] = WINDOW_HEIGHT // 2
            shield['x'] = random.randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2)

    # Manage shield activation duration
    if shield_active:
        shield_timer -= 1
        if shield_timer <= 0:
            shield_active = False
            print("Shield expired!")


def check_shield_collision():
    global shields, shield_active, shield_timer
    for shield in shields:
        if detect_collision(robot_arm_position, (shield['x'], shield['y']), 20, shield['radius']):
            shields.remove(shield)
            shield_active = True
            shield_timer = SHIELD_DURATION
            print("Shield activated!")


def check_heart_collision():
    global hearts, hearts_collected
    heart_x, heart_y = -WINDOW_WIDTH // 2 + 50, WINDOW_HEIGHT // 2 - 80
    if detect_collision(robot_arm_position, (heart_x, heart_y), 20, HEART_RADIUS):
        hearts += 1
        hearts_collected += 1
        print(f"Heart collected! Hearts: {hearts}")

# Game-over Conditions


def check_game_over():
    global game_over
    if hearts <= 0:
        game_over = True
        print("Game Over!")
        print(f"Final Score: {score}")


# Restarting the Game
def restart_game():
    global score, hearts, game_over, paused, treasures, debris, shields, shield_active, hearts_collected
    score = 0
    hearts = 6
    game_over = False
    paused = False
    treasures = []
    debris = []
    shields = []
    shield_active = False
    hearts_collected = 0
    initialize_objects()
    initialize_advanced_objects()
    print("Game restarted!")

# Enhanced Update Function


def enhanced_update_scene():
    if not paused and not game_over:
        update_objects()
        update_shields()
        check_shield_collision()
        check_heart_collision()
        check_collisions()
        check_game_over()
    glutPostRedisplay()
# Main display function


def timer(value):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)  # Approx. 60 FPS


def display():
    global shield_active
    glClear(GL_COLOR_BUFFER_BIT)
    draw_robotic_arm(robot_arm_position[0], robot_arm_position[1])
    draw_treasures()
    draw_debris()
    draw_shields()

    draw_buttons()
    render_game_info()
    if shield_active:
        glColor3f(0.0, 1.0, 0.0)  # Change arm color to indicate shield
        draw_robotic_arm(robot_arm_position[0], robot_arm_position[1])
    glutSwapBuffers()

# Rendering game info


def render_game_info():
    glColor3f(1, 1, 1)  # White text
    draw_text(f"Score: {score}", -WINDOW_WIDTH //
              2 + 20, WINDOW_HEIGHT // 2 - 40)
    draw_text(f"Hearts: {hearts}", -WINDOW_WIDTH //
              2 + 20, WINDOW_HEIGHT // 2 - 60)


def draw_text(text, x, y):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

# Main function


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Space hunting adventure")
    init()
    initialize_objects()
    initialize_advanced_objects()
    glutDisplayFunc(display)
    glutIdleFunc(enhanced_update_scene)
    glutKeyboardFunc(move_robot_arm)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse_input)
    glutTimerFunc(0, timer, 0)

    glutMainLoop()


if __name__ == "__main__":
    main()
