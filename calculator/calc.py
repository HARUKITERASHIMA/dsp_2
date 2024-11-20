import math
import flet as ft


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.colors.WHITE24
        self.color = ft.colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.ORANGE
        self.color = ft.colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.BLUE_GREY_100
        self.color = ft.colors.BLACK


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=ft.colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                ft.Row(
                    controls=[
                        ExtraActionButton(
                            text="x^2", button_clicked=self.button_clicked
                        ),
                        ExtraActionButton(
                            text="x^3", button_clicked=self.button_clicked
                        ),
                        ExtraActionButton(
                            text="x^y", button_clicked=self.button_clicked
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        ExtraActionButton(
                            text="cosx", button_clicked=self.button_clicked
                        ),
                        ExtraActionButton(
                            text="sinx", button_clicked=self.button_clicked
                        ),
                    ],
                ),                
                ft.Row(
                    controls=[
                        ExtraActionButton(
                            text="AC", button_clicked=self.button_clicked
                        ),
                        ExtraActionButton(
                            text="+/-", button_clicked=self.button_clicked
                        ),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(
                            text="0", expand=2, button_clicked=self.button_clicked
                        ),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value += data

        elif data in ("+", "-", "*", "/"):
            self.result.value = self.format_number(
                self.calculate(self.operand1, float(self.result.value), self.operator)
            )
            self.operator = data
            self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data == "=":
            self.result.value = self.format_number(
                self.calculate(self.operand1, float(self.result.value), self.operator)
            )
            self.reset()

        elif data == "%":
            self.result.value = self.format_number(float(self.result.value) / 100)
            self.reset()

        elif data == "+/-":
            self.result.value = self.format_number(-float(self.result.value))

        elif data == "x^2":
            self.result.value = self.format_number(float(self.result.value) ** 2)
            self.reset()

        elif data == "x^3":
            self.result.value = self.format_number(float(self.result.value) ** 3)
            self.reset()

        elif data == "x^y":
            self.ask_exponent()

        elif data == "cosx":
            self.result.value = self.format_number(math.cos(math.radians(float(self.result.value))))
            self.reset()

        elif data == "sinx":
            self.result.value = self.format_number(math.sin(math.radians(float(self.result.value))))
            self.reset()

        self.update()

    def ask_exponent(self):
        def set_exponent(e):
            try:
                exponent = float(input_field.value)
                self.result.value = self.format_number(
                    float(self.result.value) ** exponent
                )
                dialog.open = False
                self.update()
            except ValueError:
                self.result.value = "Error"
                dialog.open = False
                self.update()

        input_field = ft.TextField(label="Enter exponent:")
        dialog = ft.AlertDialog(
            title=ft.Text("x^y Calculation"),
            content=input_field,
            actions=[
                ft.TextButton("OK", on_click=set_exponent),
                ft.TextButton("Cancel", on_click=lambda e: dialog.dismiss()),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.update()

    def format_number(self, num):
        if num % 1 == 0:
            return str(int(num))
        else:
            return str(num)

    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return operand1 + operand2
        elif operator == "-":
            return operand1 - operand2
        elif operator == "*":
            return operand1 * operand2
        elif operator == "/":
            return "Error" if operand2 == 0 else operand1 / operand2

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Calc App"
    calc = CalculatorApp()
    page.add(calc)


ft.app(target=main)
