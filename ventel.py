import tkinter as tk
from itertools import product

# ===================== THEME =====================
BG = "#edf0f5"
LEFT_BG = "#f7f9fc"
GRID = "#d0d6e5"

NODE_W = 120
NODE_H = 60
PORT_R = 6

LEFT_PANEL_WIDTH = 340

COLORS = {
    "IN": "#5b8def",
    "OUT": "#f2a65a",
    "AND": "#6fcf97",
    "OR": "#bb86fc",
    "XOR": "#56cfe1",
    "NOT": "#ef6f6c",
    "NAND": "#4ecdc4",
    "NOR": "#9b7ede",
    "XNOR": "#5e9cea",
    "WIRE_ON": "#3a3a3a",
    "WIRE_OFF": "#b0b0b0"
}

BTN_FONT = ("Segoe UI", 12, "bold")
TITLE_FONT = ("Segoe UI", 15, "bold")
SUB_FONT = ("Segoe UI", 11)
STATUS_FONT = ("Segoe UI", 10)
TABLE_FONT = ("Segoe UI", 10)
TABLE_CELL_W = 8

# ===================== TOOLTIP =====================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        tk.Label(
            self.tip,
            text=self.text,
            bg="#2b2f3a",
            fg="white",
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        ).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ===================== LOGIC =====================
def AND(a, b): return a & b
def OR(a, b): return a | b
def XOR(a, b): return a ^ b
def NOT(a, b=0): return 1 - a
def NAND(a, b): return 1 - (a & b)
def NOR(a, b): return 1 - (a | b)
def XNOR(a, b): return 1 - (a ^ b)

GATES = {
    "AND": AND, "OR": OR, "XOR": XOR,
    "NOT": NOT, "NAND": NAND, "NOR": NOR, "XNOR": XNOR
}

def inputs_count(kind):
    return 1 if kind in ("NOT", "OUT") else 2

# ===================== ROUNDED BUTTON =====================
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg="#edf0fa"):
        super().__init__(parent, height=50, bg=LEFT_BG, highlightthickness=0)
        self.command = command
        self.bg = bg
        self.hover = "#d9def0"

        self.rect = self._round_rect(10, 8, 300, 46, 18, self.bg)
        self.create_text(155, 27, text=text, font=BTN_FONT, fill="#333")

        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.bg))

        ToolTip(self, f"Добавление элемента: {text}")

    def _round_rect(self, x1, y1, x2, y2, r, color):
        return self.create_polygon(
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2,
            x1+r, y2, x1, y2, x1, y2-r,
            x1, y1+r, x1, y1,
            fill=color, outline="#aaa", smooth=True
        )

# ===================== GATE =====================
class Gate:
    counter = {"IN": 0, "OUT": 0}

    def __init__(self, sim, kind, x, y):
        self.sim = sim
        self.kind = kind
        self.x = x
        self.y = y
        self.inputs = [None] * inputs_count(kind)
        self.output_value = 0
        self.items = []

        if kind == "IN":
            Gate.counter["IN"] += 1
            self.label = f"IN{Gate.counter['IN']}"
        elif kind == "OUT":
            Gate.counter["OUT"] += 1
            self.label = f"OUT{Gate.counter['OUT']}"
        else:
            self.label = kind

        self.draw()

    def draw(self):
        c = self.sim.canvas
        self.items.clear()
        self.in_ports = []

        mid = self.y + NODE_H // 2

        body = c.create_rectangle(
            self.x, self.y,
            self.x + NODE_W, self.y + NODE_H,
            fill=COLORS[self.kind],
            outline="#444",
            width=2
        )
        text = c.create_text(
            self.x + NODE_W // 2,
            mid,
            text=self.label,
            fill="white",
            font=("Segoe UI", 10, "bold")
        )

        self.items.extend([body, text])

        for i in range(len(self.inputs)):
            py = self.y + 20 + i * 20
            p = c.create_oval(
                self.x - 12, py - PORT_R,
                self.x, py + PORT_R,
                fill="#555"
            )
            self.in_ports.append(p)
            self.items.append(p)

        self.out_port = c.create_oval(
            self.x + NODE_W,
            mid - PORT_R,
            self.x + NODE_W + 12,
            mid + PORT_R,
            fill="#555"
        )
        self.items.append(self.out_port)

        self.bind()

    def bind(self):
        c = self.sim.canvas
        for o in self.items:
            c.tag_bind(o, "<Button-1>", self.press)
            c.tag_bind(o, "<B1-Motion>", self.drag)
            c.tag_bind(o, "<Button-3>", lambda e: self.sim.delete_gate(self))
        for p in self.in_ports:
            c.tag_bind(p, "<Button-1>", lambda e, g=self: self.sim.finish_wire(g))
        c.tag_bind(self.out_port, "<Button-1>", lambda e, g=self: self.sim.start_wire(g))
        if self.kind == "IN":
            c.tag_bind(self.items[0], "<Double-Button-1>", lambda e: self.toggle())

    def press(self, e):
        self.start = (e.x, e.y)

    def drag(self, e):
        dx = e.x - self.start[0]
        dy = e.y - self.start[1]
        self.start = (e.x, e.y)
        for o in self.items:
            self.sim.canvas.move(o, dx, dy)
        self.x += dx
        self.y += dy
        self.sim.update_wires()

    def toggle(self):
        self.output_value ^= 1
        self.sim.evaluate_all()
        self.sim.update_wires()
        self.sim.update_truth()

    def evaluate(self):
        if self.kind == "IN":
            return self.output_value
        if self.kind == "OUT":
            self.output_value = self.inputs[0].output_value if self.inputs[0] else 0
            return self.output_value
        fn = GATES[self.kind]
        a = self.inputs[0].output_value if self.inputs[0] else 0
        b = self.inputs[1].output_value if len(self.inputs) > 1 and self.inputs[1] else 0
        self.output_value = fn(a, b)
        return self.output_value

    def evaluate_recursive(self, visited=None):
        if visited is None:
            visited = set()
        if self in visited:
            return self.output_value
        visited.add(self)
        for i in self.inputs:
            if i:
                i.evaluate_recursive(visited)
        return self.evaluate()

# ===================== WIRE =====================
class Wire:
    def __init__(self, sim, src, dst, idx):
        self.sim = sim
        self.src = src
        self.dst = dst
        self.idx = idx
        dst.inputs[idx] = src
        self.line = sim.canvas.create_line(0, 0, 0, 0, width=2)
        self.update()

    def update(self):
        self.sim.evaluate_all()
        x1 = self.src.x + NODE_W
        y1 = self.src.y + NODE_H // 2
        x2 = self.dst.x
        y2 = self.dst.y + 20 + self.idx * 20
        self.sim.canvas.coords(self.line, x1, y1, x2, y2)
        self.sim.canvas.itemconfig(
            self.line,
            fill=COLORS["WIRE_ON"] if self.src.output_value else COLORS["WIRE_OFF"]
        )

# ===================== SIMULATOR =====================
class Simulator:
    def __init__(self, root):
        root.title("Интерактивный симулятор логических схем")
        root.configure(bg=BG)

        self.left = tk.Frame(root, width=LEFT_PANEL_WIDTH, bg=LEFT_BG)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)

        tk.Label(
            self.left,
            text="Интерактивный симулятор\nлогических схем",
            bg=LEFT_BG,
            fg="#222",
            font=TITLE_FONT,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(12, 4))

        tk.Label(
            self.left,
            text="Учебный программный комплекс",
            bg=LEFT_BG,
            fg="#555",
            font=SUB_FONT
        ).pack(anchor="w", padx=12, pady=(0, 10))

        tk.Label(
            self.left,
            text=(
                "Методические указания\n"
                "────────────────────\n"
                "1. Добавьте входные элементы (IN)\n"
                "2. Разместите логические элементы\n"
                "3. Соедините выходы с входами\n"
                "4. Двойной щелчок по IN — смена значения\n"
                "5. Правая кнопка мыши — удаление элемента\n"
                "6. Таблица истинности формируется автоматически"
            ),
            bg=LEFT_BG,
            fg="#444",
            font=("Segoe UI", 10),
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=14, pady=(6, 10))

        self.buttons = tk.Frame(self.left, bg=LEFT_BG)
        self.buttons.pack(fill="x")

        for k in ["IN", "OUT"] + list(GATES.keys()):
            RoundedButton(self.buttons, k, lambda x=k: self.add_gate(x)).pack(pady=4)

        RoundedButton(self.buttons, "ШАГ НАЗАД", self.step_delete, bg="#ffe4e4").pack(pady=6)
        RoundedButton(self.buttons, "ОЧИСТИТЬ ВСЁ", self.clear_all, bg="#ffdede").pack(pady=6)

        tk.Label(
            self.left,
            text="Студент: 09-443 Ева\nДисциплина: АСВТ",
            bg=LEFT_BG,
            fg="#666",
            font=("Segoe UI", 9),
            justify="left"
        ).pack(side="bottom", pady=8)

        # ===== ИЗМЕНЕНИЕ ТОЛЬКО ЗДЕСЬ =====
        self.canvas_frame = tk.Frame(root, bg="#bfc6d8", bd=2, relief="sunken")
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg=BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        self.truth_frame = tk.Frame(self.canvas_frame, bg="white", bd=2, relief="ridge", width=420)
        self.truth_frame.pack(side="right", fill="y", padx=6, pady=6)
        self.truth_frame.pack_propagate(False)
        # =================================

        self.status = tk.Label(
            root,
            text="Готово",
            bg="#dde2ef",
            fg="#333",
            anchor="w",
            font=STATUS_FONT,
            padx=10
        )
        self.status.pack(side="bottom", fill="x")

        self.gates = []
        self.wires = []
        self.wire_start = None

        self.draw_grid()
        self.update_truth()

    def draw_grid(self):
        for i in range(0, 4000, 40):
            self.canvas.create_line(i, 0, i, 3000, fill=GRID)
        for j in range(0, 3000, 40):
            self.canvas.create_line(0, j, 4000, j, fill=GRID)

    def add_gate(self, kind):
        self.gates.append(Gate(self, kind, 360, 200))
        self.status.config(text=f"Добавлен элемент: {kind}")
        self.update_truth()

    def start_wire(self, gate):
        self.wire_start = gate
        self.status.config(text="Выберите вход для соединения")

    def finish_wire(self, gate):
        if self.wire_start and gate != self.wire_start:
            for i in range(len(gate.inputs)):
                if gate.inputs[i] is None:
                    self.wires.append(Wire(self, self.wire_start, gate, i))
                    self.status.config(text="Соединение создано")
                    break
        self.wire_start = None
        self.update_truth()

    def update_wires(self):
        for w in self.wires:
            w.update()

    def evaluate_all(self):
        for g in self.gates:
            g.evaluate_recursive()

    def step_delete(self):
        if self.wires:
            w = self.wires.pop()
            self.canvas.delete(w.line)
        elif self.gates:
            self.delete_gate(self.gates[-1])
        self.status.config(text="Отмена последнего действия")
        self.update_truth()

    def clear_all(self):
        for w in self.wires:
            self.canvas.delete(w.line)
        for g in self.gates:
            for o in g.items:
                self.canvas.delete(o)
        self.wires.clear()
        self.gates.clear()
        Gate.counter["IN"] = 0
        Gate.counter["OUT"] = 0
        self.wire_start = None
        self.status.config(text="Схема очищена")
        self.update_truth()

    def delete_gate(self, gate):
        for w in self.wires[:]:
            if w.src == gate or w.dst == gate:
                self.canvas.delete(w.line)
                self.wires.remove(w)
        for o in gate.items:
            self.canvas.delete(o)
        self.gates.remove(gate)
        self.status.config(text="Элемент удалён")
        self.update_truth()

    def update_truth(self):
        for w in self.truth_frame.winfo_children():
            w.destroy()

        ins = [g for g in self.gates if g.kind == "IN"]
        outs = [g for g in self.gates if g.kind == "OUT"]

        if not ins or not outs:
            tk.Label(
                self.truth_frame,
                text="Таблица истинности недоступна",
                bg="white",
                fg="black",
                font=("Segoe UI", 11)
            ).pack(pady=20)
            return

        tk.Label(
            self.truth_frame,
            text="Таблица истинности логической схемы",
            bg="white",
            fg="black",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(6, 4))

        table = tk.Frame(self.truth_frame, bg="white")
        table.pack(padx=6, pady=4)

        headers = [g.label for g in ins + outs]

        for c, h in enumerate(headers):
            tk.Label(
                table, text=h, borderwidth=1, relief="solid",
                width=TABLE_CELL_W, font=TABLE_FONT
            ).grid(row=0, column=c)

        for r, bits in enumerate(product([0, 1], repeat=len(ins)), start=1):
            for g, b in zip(ins, bits):
                g.output_value = b
            self.evaluate_all()
            vals = list(bits) + [o.output_value for o in outs]
            for c, v in enumerate(vals):
                tk.Label(
                    table, text=v, borderwidth=1, relief="solid",
                    width=TABLE_CELL_W, font=TABLE_FONT
                ).grid(row=r, column=c)

# ===================== RUN =====================
root = tk.Tk()
Simulator(root)
root.mainloop()
